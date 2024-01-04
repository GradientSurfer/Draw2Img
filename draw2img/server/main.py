import json
import logging
import sys
import threading
from queue import Empty, Queue
from time import sleep

import fire
import torch
from PIL import Image
from pydantic import BaseModel
from websockets import WebSocketServerProtocol
from websockets.sync.server import WebSocketServer, serve

from .model import device, pipe

logger = logging.getLogger("websocket_server")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

pipe.to(device)
pipe.set_progress_bar_config(disable=True)  # disable `tqdm`
mutex = threading.Lock()  # pipe is not thread safe


class Params(BaseModel):
    prompt: str = "ocean wave curling in with rays of sun in spray, photograph, 8k, 35mm digital, f1.8, depth of field, HDR "
    seed: int = 42
    steps: int = 1
    strength: float = 1.0

    def validate_steps(self):
        """SDXL-turbo requires `steps * strength >= 1.0`"""
        if self.steps * self.strength < 1.0:
            if self.steps == 1:
                self.strength = 1.0
            else:
                self.strength = 1.0 / self.steps


def img2img_inference(image: bytes, params: Params) -> Image.Image:
    """Performs text guided img2img generation and returns the generated image in RGB format."""
    input = Image.frombuffer("RGBA", (512, 512), image, "raw")
    # remove alpha channel (converted to white pixels)
    buffer = Image.new("RGB", input.size, (255, 255, 255))
    buffer.paste(input, mask=input.split()[3])
    # set seed for reproducible outputs
    generator = torch.Generator(device=device).manual_seed(params.seed)
    with mutex:  # inference
        r = pipe(
            [params.prompt],
            image=[buffer],
            num_inference_steps=params.steps,
            strength=params.strength,
            guidance_scale=0.0,  # must be 0.0 for SDXL-turbo
            generator=generator,
        )
    output: Image.Image = r.images[0]
    return output


def inference_loop(
    websocket: WebSocketServerProtocol,
    request_queue: Queue[bytes],
    stop: threading.Event,
):
    params = Params()
    previous_image: bytes = b""
    while True:
        if stop.is_set():
            break
        # process only the most recent input
        # (drop missed frames to prevent falling behind)
        try:
            if request_queue.empty():
                payload = request_queue.get(timeout=1.0)  # blocking
            while not request_queue.empty():
                payload = request_queue.get(timeout=1.0)  # blocking
            if payload is None:
                break
        except Empty:
            continue

        if isinstance(payload, str):
            obj = json.loads(payload)
            if obj["type"] == 1:
                params = Params.model_validate(obj)
                params.validate_steps()
                output = img2img_inference(previous_image, params)
                websocket.send(output.convert("RGBA").tobytes())
                continue
        elif isinstance(payload, bytes):
            if payload == previous_image:
                continue  # optimization: avoid redundant computation
            output = img2img_inference(payload, params)
            websocket.send(output.convert("RGBA").tobytes())
            previous_image = payload
        else:
            pass
        continue
    return


def connection(websocket: WebSocketServerProtocol):
    try:
        request_queue: Queue[bytes] = Queue()
        stop: threading.Event = threading.Event()
        thread = threading.Thread(
            target=inference_loop, args=(websocket, request_queue, stop)
        )
        thread.start()
        for message in websocket:
            request_queue.put(message)
    except KeyboardInterrupt:
        stop.set()
    except Exception:
        logger.exception("connection closed due to exception:")
    finally:
        stop.set()
        request_queue.put(None)
        thread.join()


def wait_for_exit(stop: threading.Event, server: WebSocketServer):
    while not stop.is_set():
        sleep(1.0)
    server.shutdown()


def server(
    host: str = "localhost", port: int = 8080, stop: threading.Event = threading.Event()
) -> WebSocketServer:
    """Start a multi-threaded websocket server for Draw2Img. Doesn't return (blocks thread)."""
    with serve(connection, host, port, server_header=None) as server:
        logger.info(f"listening: ws://{host}:{port}")
        thread = threading.Thread(target=wait_for_exit, args=(stop, server))
        thread.start()
        server.serve_forever()
        thread.join()


if __name__ == "__main__":
    fire.Fire(server)
