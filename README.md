# Draw2Img

A simple web UI for interactive *text-guided image to image generation*, intended for any age and skill level.

<img src="demos/demo4.gif" width="48%"></img>
<img src="demos/demo1.gif" width="48%"></img>

### Community Showcase

*"ocean wave, sunset, rays of light, photograph, 35mm digital, 4k"*

<img src="gallery/canvas1.png" alt="ocean wave, sunset, rays of light, photograph, 35mm digital, 4k" />

**Did you make something cool with Draw2Img? Showcase your artwork here!**

# Features

- web based UI, interactive canvas with basic paint tool & color picker
- real-time text-guided image to image generation via [SDXL-Turbo](https://huggingface.co/stabilityai/sdxl-turbo) (512 x 512 pixels)
- editable prompt, seed, steps, and strength parameters 
- export button to save input and output images as PNG files, along with the parameters as JSON
- multi-threaded server supports multiple concurrent users
    - easy to host on your LAN for creative fun with family and friends
- local (no internet required), private, & open source

# Requirements

Hardware:
- **GPU** with at least 10 GB VRAM is recommended, but not strictly required
- CPU only environments are supported but image generation will be significantly slower

Operating System:
- Linux, Mac, or Windows

Software:
- Python >= 3.10 and <= 3.11

Browser:
- any modern browser (Firefox, Chrome, Edge, Safari, etc)

Internet:
- not required (except to download the model once on first run)

# Usage

## Install

Clone this repository

```bash
git clone https://github.com/GradientSurfer/Draw2Img.git
```

Install the dependencies

```bash
pip install .
```

## Start Server

Start the server, by default it will listen on [http://localhost:8080](http://localhost:8080)

```bash
python draw2img/main.py
```

Navigate to the HTTP URL via your browser, and...that's it, have fun!

### Options

You can host the server on a specific interface and port via the `--host` and `--port` options. For example to listen on `192.168.1.123:4269`:

```bash
python draw2img/main.py --host 192.168.1.123 --port 4269
```

To see all available options

```bash
python draw2img/main.py --help
```

### Container (Docker/Podman)

You can use the provided Dockerfile to build and run a container image:

```bash
DOCKER_BUILDKIT=1 docker build -t draw2img .
```

Be sure to mount your huggingface cache directory to avoid downloading the SDXL-Turbo model every time the container starts (`-v ~/.cache/huggingface:/root/.cache/huggingface`). To use GPU(s) you'll need the `--gpus all` option.

```bash
docker run -it -p 8080:8080 -p 8079:8079 -v ~/.cache/huggingface:/root/.cache/huggingface --gpus all draw2img
```

# Development

## Server

Install the Python package in editable mode

```bash
pip install -e .
```

## UI

The UI can be built manually (static files are output to `dist` folder)

```bash
cd draw2img/ui
npm run build
```

Or alternatively, the Vue 3 template comes with a file server & hot reloading for easy development

```bash
npm run dev
```

### Container (Docker/Podman)

You can avoid installing `node` and `npm` on your host machine by using a container image that already includes the UI toolchain (`node:lts-slim`).

```bash
cd draw2img/ui
# build the UI
docker run -it -v $(pwd):/ui -p 5173:5173 node:lts-slim bash -c "cd ui && npm run build"
# or run the dev server
docker run -it -v $(pwd):/ui -p 5173:5173 node:lts-slim bash -c "cd ui && npm run dev -- --host"
```

## Design Notes

The backend is a multi-threaded Python websocket server, that also serves the static files for the web UI.

The front-end is a JS/TS application (Vue 3) bootstrapped via `npm create vue@latest`. The build produces static files that can be served with any web server software.

### Performance

Although the websocket server is multi-threaded, a mutex protects the singleton `Pipeline` object because it is not thread safe. This means image generation is effectively single threaded, so performance scales poorly as the number of concurrent users increases, and CPU/GPU resources may be underutilized. Additionally, there is no batching of requests for inference, mainly due to the lack of underlying support for varying certain parameters (such as strength and steps) across samples within a single batch.

In practice the multithreading/lock primitives exhibit a degree of fairness, so limited CPU/GPU resources appear to be shared relatively evenly among concurrent users, even as incoming requests queue up. Technically though, Python doesn't make any guarantees regarding the order of thread scheduling when a lock is contended (according to the docs).

If you need additional concurrency and have available RAM/VRAM + compute, consider starting multiple instances of the `draw2img` process.

### Security

This code has not been audited for vulnerabilities.

# Contributions

Contributions are welcome! Please keep in mind the ethos of this project when opening PRs or issues.

# Safety

There is no safety filter to prevent offensive or undesireable images from being generated, please use discretion. Supervise children as usual with any computer/internet use.

# Non-goals / Other Projects

If you're an advanced user looking for more functionality, other projects like [Stable Diffusion Web UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) or [ComfyUI](https://github.com/comfyanonymous/ComfyUI) may fit your needs better.

# License

[MIT](LICENSE)

See the [Stability AI Non-Commercial License for SDXL-Turbo](https://github.com/Stability-AI/generative-models/blob/main/model_licenses/LICENSE-SDXL-Turbo) and their [acceptable use policy](https://stability.ai/use-policy).

# Star History

[![Star History Chart](https://api.star-history.com/svg?repos=GradientSurfer/Draw2Img&type=Date)](https://star-history.com/#GradientSurfer/Draw2Img&Date)