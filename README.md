# Bold UI

UI Framework based on a client-server scene-graph model.

This is not a Javascript framework, it is language-independent networking protocol with a Rust and Python implementation.

(TODO: Example code and more explanations)

## Code structure

### The renderer

This project connects with a supported app to display its UI and process events.

It will be cross-platform and always open-source.

### The protocol and protocol_bindings

These define how the renderer and apps communicate, particularly the `protocol/spec.md` and `protocol/src/lib.rs` files.

### Examples

Example apps for testing the renderer.


## How to run the examples

### The rust example

```shell
RUST_LOG='debug' cargo run --release -p boldui_renderer -- --frontend window -- cargo run --release -p boldui_example_rs_calc
```

### The python example

```shell
# Rebuild bindings, just in case
cargo run -p boldui_protocol_bindings
# Make venv
python3 -m venv venv
source venv/bin/activate
pip install -e ./boldui_python
ln ./boldui_protocol_bindings/python/{bincode,boldui_protocol,serde_binary,serde_types} ./venv/lib/python*/site-packages/
# Run the example
cd ./examples/boldui_example_py_calc
RUST_LOG='debug' cargo run --release -p boldui_renderer -- --frontend window -- python boldui_example_py_calc
```

## WIP

- Important flow to optimize: input to pixel (no app rtt)
  - Recv from glutin into event loop (in UI Thread)
  - Set time
  - decide which handler blocks to run
  - run them
  - figure out which scenes' ops need to be reevaluated
  - evaluate them
  - if results of draw commands changed, request redraw
  - (wait for vsync)
  - draw new frame according to draw commands

## TODO:

Touchpad interpolation: https://gitlab.gnome.org/GNOME/gtk/-/merge_requests/1117

- problem being solved: touchpad sps > fps
- low latency option: average all samples, multiply by frame time, problem: might not be accurate to movement if timing inconsistent
- quality option: interpolate over the next frame to maintain smoothness
- my touchpad (yoga 730-ikb) is about 140hz

VRR: https://gitlab.gnome.org/GNOME/gtk/-/issues/2959

- great opportunity since we control whole stack
- if focused window is fullscreen it locks the display to itself
- if focused window has a consistent framerate (e.g. movie), then the display is locked to multiples of it
- if focused window has inconsistent framerate >30hz (e.g. slightly laggy game), then lock to it
- if focused window has inconsistent framerate <30hz (e.g. ide), then lock to next fastest-updating source (e.g. movie in bg)
  - should support interrupting a slow frame with a quick update, e.g. ide in foreground and 24fps movie in background, ide writes new letter - should be instant
- VRR 165hz 2K display costs about 1.5k ils
