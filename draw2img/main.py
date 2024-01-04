import http.server
import logging
import os
import sys
import threading
from http.server import ThreadingHTTPServer
from threading import Thread

import fire

from draw2img.server import server

logger = logging.getLogger("draw2img")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger("websockets.server").setLevel(logging.WARNING)
logging.getLogger("http.server").setLevel(logging.WARNING)
# path to static files for serving web UI
UI_DIR = os.path.join(os.path.dirname(__file__), "ui/dist")


def main(host: str = "localhost", port: int = 8080, dir: str = UI_DIR):
    """Starts a draw2img process, blocks until keyboard interrupt."""

    try:
        # start web socket server in a separate thread
        wss_port = port - 1
        stop_event: threading.Event = threading.Event()
        thread = Thread(target=server, args=(host, wss_port, stop_event))
        thread.start()

        # start static file server for web UI
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=dir, **kwargs)

        with ThreadingHTTPServer((host, port), Handler) as httpd:
            logger.info(f"Web UI URL: http://{host}:{port}")
            httpd.serve_forever()

    except KeyboardInterrupt:
        stop_event.set()
    except Exception:
        logger.exception("draw2img unexpected error")
    finally:
        thread.join()

    return


if __name__ == "__main__":
    fire.Fire(main)
