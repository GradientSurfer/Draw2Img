<script lang="ts">

// how fast to send images to backend
const IMAGES_PER_SEC = 5;
const MS_PER_IMAGE = 1000 / 5; // 1000 ms / 5 = 200 ms
// image size
const WIDTH = 512;
const HEIGHT = 512;

class State {
  prompt: string = "ocean wave curling in with rays of sun in spray, photograph, 8k, 35mm digital, f1.8, depth of field, HDR"
  seed: number = 42
  steps: number = 1
  strength: number = 1.0
  guidance_scale: number = 1.2
  penSize: number = 10
  fillStyle: string = 'black'
  mru_colors: Array<string> = []
  timer: number = -1;
  ws: WebSocket | null = null;
  conn_state: number = WebSocket.CLOSED
  dirty_canvas: boolean = true;
}

export default {
  data() {
    return new State()
  },
  methods: {
    clear_foreground() {
      const el: HTMLCanvasElement = this.$refs.foreground as HTMLCanvasElement;
      const ctx = el?.getContext("2d")
      if (ctx == null) throw new Error("")
      ctx.clearRect(0, 0, WIDTH, HEIGHT);
      return {
        "ctx": ctx,
        "el": el
      }
    },
    get_foreground() {
      const el: HTMLCanvasElement = this.$refs.foreground as HTMLCanvasElement;
      const ctx = el?.getContext("2d")
      if (ctx == null) throw new Error("")
      return {
        "ctx": ctx,
        "el": el
      }
    },
    get_background() {
      const el: HTMLCanvasElement = this.$refs.background as HTMLCanvasElement;
      const ctx = el?.getContext("2d")
      if (ctx == null) throw new Error("")
      return {
        "ctx": ctx,
        "el": el
      }
    },
    get_canvas() {
      const el: HTMLCanvasElement = this.$refs.canvas as HTMLCanvasElement;
      const ctx = el?.getContext("2d")
      if (ctx == null) throw new Error("")
      return {
        "ctx": ctx,
        "el": el
      }
    },
    get_output() {
      const el: HTMLCanvasElement = this.$refs.output as HTMLCanvasElement;
      const ctx = el?.getContext("2d")
      if (ctx == null) throw new Error("")
      return {
        "ctx": ctx,
        "el": el
      }
    },
    composite_input() {
      const canvas = this.get_canvas()
      const foreground = this.get_foreground()
      const background = this.get_background()

      canvas.ctx.clearRect(0, 0, WIDTH, HEIGHT);
      canvas.ctx.drawImage(background.el, 0, 0);
      canvas.ctx.drawImage(foreground.el, 0, 0);
    },
    mouseMove(ev: MouseEvent) {

      if (ev.buttons == 0) { // no buttons
        const canvas = this.get_canvas()
        let rect = canvas.el.getBoundingClientRect();
        let x = ev.clientX - rect.left
        let y = ev.clientY - rect.top

        const foreground = this.get_foreground()
        foreground.ctx.clearRect(0, 0, WIDTH, HEIGHT);
        foreground.ctx.beginPath();
        foreground.ctx.arc(x, y, this.penSize, 0, 2 * Math.PI, false);
        foreground.ctx.fillStyle = this.fillStyle;
        foreground.ctx.stroke();
        foreground.ctx.fill();

        this.composite_input()
        return
      }

      if (ev.buttons == 1) { // primary button (left)
        this.dirty_canvas = true
        const canvas = this.get_canvas()
        let rect = canvas.el.getBoundingClientRect();
        let x = ev.clientX - rect.left
        let y = ev.clientY - rect.top

        // fill pen
        const background = this.get_background()
        background.ctx.beginPath();
        background.ctx.arc(x, y, this.penSize, 0, 2 * Math.PI, false);
        background.ctx.fillStyle = this.fillStyle;
        background.ctx.fill();

        // stroke pen
        const foreground = this.get_foreground()
        foreground.ctx.clearRect(0, 0, WIDTH, HEIGHT);
        foreground.ctx.beginPath();
        foreground.ctx.arc(x, y, this.penSize, 0, 2 * Math.PI, false);
        foreground.ctx.fillStyle = this.fillStyle;
        foreground.ctx.stroke();

        this.composite_input()
        return
      }
    },
    mouseOut(ev: MouseEvent) {
      const foreground = this.get_foreground()
      foreground.ctx.clearRect(0, 0, WIDTH, HEIGHT);
      this.composite_input()
    },
    composite_output(blob: Blob) {
      const el: HTMLCanvasElement = this.$refs.output as HTMLCanvasElement;
      const ctx = el.getContext("2d")
      if (ctx == null) { return }
      blob.arrayBuffer().then((b: ArrayBuffer) => {
        const imageData = ctx.createImageData(WIDTH, HEIGHT);
        imageData.data.set(new Uint8ClampedArray(b));
        ctx?.putImageData(imageData, 0, 0)
      })
    },
    on_param_change() {
      this.ws?.send(JSON.stringify({ type: 1, prompt: this.prompt, guidance_scale: this.guidance_scale, steps: this.steps, strength: this.strength, seed: this.seed }))
    },
    submit_prompt(ev: KeyboardEvent) {
      this.ws?.send(JSON.stringify({ type: 1, prompt: this.prompt, guidance_scale: this.guidance_scale, steps: this.steps, strength: this.strength, seed: this.seed }))
    },
    change_color(fillStyle: string) {
      const idx = this.mru_colors.findIndex((c) => { return fillStyle == c; })
      if (idx == -1) {
        this.mru_colors.unshift(fillStyle)
        if (this.mru_colors.length > 10) {
          this.mru_colors.pop()
        }
        return
      }
      this.mru_colors.splice(idx, 1)
      this.mru_colors.unshift(fillStyle)
      this.fillStyle = fillStyle;
    },
    ws_is_connected(): boolean {
      return this.conn_state == WebSocket.OPEN;
    },
    clear() {
      if (confirm("are you sure?")) {
        const background = this.get_background()
        background.ctx.clearRect(0, 0, WIDTH, HEIGHT)
        this.composite_input()
        this.dirty_canvas = true
      }
    },
    xport() {
      const filename = new Date().toISOString()
      var link = document.createElement('a');
      link.download = filename + '_output.png';
      link.href = this.get_output().el.toDataURL()
      link.click();

      var link = document.createElement('a');
      link.download = filename + '_input.png';
      link.href = this.get_canvas().el.toDataURL()
      link.click();

      var a = document.createElement("a")
      a.href = URL.createObjectURL(
        new Blob([JSON.stringify({
          'seed': this.seed,
          'steps': this.steps,
          'strength': this.strength,
          'prompt': this.prompt
        })], { type: "application/json" })
      )
      a.download = filename + ".json"
      a.click()
    }
  },
  created() {
    this.mru_colors.unshift("#1a5fb4")
    this.mru_colors.unshift("#26a269")
    this.mru_colors.unshift("#e5a50a")
    this.mru_colors.unshift("#c64600")
    this.mru_colors.unshift("#a51d2d")
    this.mru_colors.unshift("#613583")
    this.mru_colors.unshift("#63452c")
    this.mru_colors.unshift("#9a9996")
    this.mru_colors.unshift("#000")
  },
  mounted() {
    const ws_port = parseInt(window.location.port) - 1
    this.ws = new WebSocket(`ws://${window.location.hostname}:${ws_port}`);
    const ws = this.ws;

    this.timer = window.setInterval(() => {
      if (!this.dirty_canvas) {
        return
      }
      this.dirty_canvas = false;
      // send canvas over websocket every N seconds
      if (this.ws?.readyState == this.ws?.OPEN) {
        const el: HTMLCanvasElement = this.$refs.canvas as HTMLCanvasElement;
        if (!el) { return }
        const background = this.get_background()
        const imageData = background.ctx.getImageData(0, 0, WIDTH, HEIGHT);
        const buffer = imageData.data.buffer;  // ArrayBuffer
        ws.send(buffer)
      }
    }, MS_PER_IMAGE)


    ws.addEventListener('open', (event) => {
      // console.log('WebSocket connection opened:', event);
      this.conn_state = WebSocket.OPEN;
    });

    ws.addEventListener('message', (event) => {
      const b: Blob = event.data;
      this.composite_output(b)

    })
    ws.addEventListener('close', (event) => {
      // console.log('WebSocket connection closed:', event);
      this.conn_state = WebSocket.CLOSED;
    });

    ws.addEventListener('error', (event) => {
      console.log('WebSocket error:', event);
    });
  },
  updated() {

  },
  computed: {

  },

  unmounted() {
    if (this.timer != -1) {
      clearInterval(this.timer)
      this.timer = -1;
    }
  }

}
</script>

<template>
  <main>
    <div>
      <div v-if="!ws_is_connected()">
        <h2 style="color:red;">No connection - is the server running?</h2>
      </div>
      <div v-if="ws_is_connected()">
        <div style="display: inline-block; vertical-align: top;">
          <canvas id="foreground" ref="foreground" width="512px" height="512px"></canvas>
          <canvas id="background" ref="background" width="512px" height="512px"></canvas>
          <canvas id="canvas" ref="canvas" width="512px" height="512px" @mousemove="mouseMove($event)"
            @mousedown="mouseMove($event)" @mouseout="mouseOut($event)"></canvas>
          <div class="toolbar">
            <input id="color-picker" type="color" class="color-picker" v-model="fillStyle"
              @change="change_color(fillStyle)" />
            <div style="margin:0.1em; display: inline-block;">
              <div v-for="c in mru_colors" @click="change_color(c)" :style="{ 'background-color': c }" class="mru-color">
              </div>
            </div>
            <div style="display: inline-block;">
              <label for="penSize">Size</label>
              <input id="penSize" type="range" v-model="penSize" min="1" max="96" />
              <p style="display: inline-block; margin:0; width: 1em;">
                {{ penSize }}
              </p>
            </div>
            <button class="clear-button" @click="clear()">Clear</button>
          </div>
          <div>
            <textarea v-model="prompt" @keyup="submit_prompt"
              oninput='this.style.height = ""; this.style.height = this.scrollHeight + 3 + "px"'
              style="width:100%"></textarea>
          </div>
          <div class="param">
            <label for="seed" class="label">Seed</label>
            <input v-model="seed" id="seed" type="range" min="-549755813888" max="549755813888" step="1"
              @change="on_param_change" />
            {{ seed }}
          </div>
          <div class="param">
            <label for="steps" class="label">Steps</label>
            <input v-model="steps" id="steps" type="range" min="1" max="50" step="1" @change="on_param_change" />
            {{ steps }}
          </div>
          <div class="param">
            <label for="strength" class="label">Strength</label>
            <input v-model="strength" id="strength" type="range" min="0.1" max="1.0" step="0.025"
              @change="on_param_change" />
            {{ strength }}
          </div>
        </div>
        <div style="display: inline-block; vertical-align: top;">
          <canvas id="output" ref="output" width="512px" height="512px"></canvas>
        </div>
        <div>
          <button class="export-button" @click="xport"
            style="background-color: transparent; border: 1px solid black; margin: 0.5em; padding: 1em;font-weight: bold;">Export</button>
        </div>
      </div>
    </div>
  </main>
</template>

<style>
body {
  font-family: 'Arial';
}
</style>

<style scoped>
canvas {
  outline: 1px solid black;
  width: 512px;
  height: 512px;
  margin: 0 1em 0 0;
}

#output {
  outline: 1px solid #666;
}

.color-picker {
  vertical-align: top;
  display: inline-block;
  padding: 0;
  border: none;
}

#foreground,
#background {
  visibility: hidden;
  display: none;
}

input:hover,
button:hover {
  cursor: pointer;
}

.param .label {
  width: 100px;
  display: inline-block;
  text-align: right;
  vertical-align: top;
  margin: .25em;
}

.param>input {
  width: 50%;
}

.mru-color {
  width: 24px;
  height: 24px;
  display: inline-block;
}

.mru-color:hover {
  cursor: pointer;
}

.clear-button {
  background-color: transparent;
  border: 1px solid transparent;
  color: red;
  margin: 0 0 .25em 1em;
}

.clear-button:hover {
  text-decoration: underline;
  border: 1px solid red;
}

#penSize {
  width: 10em;
}
</style>