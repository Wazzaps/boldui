# Bold UI

UI Framework based on a client-server scene-graph model.

## What?

The framework is split into a client and a server.

- The client is turns a scene-graph into pixels on a window, and converts raw input events into high-level app events.
- The server produces a scene-graph using a flutter-like widget tree, and consumes app events to update the scene-graph.

The client and server may communicate over a local UNIX domain socket, or over the internet.

The scene-graph contains draw commands (such as `draw rectangle`, `draw path`, `define clickable area`), but instead of
constants in the parameters of the commands, it has expressions that depend on client-side data such as window size or time.

This lets the client render high-framerate graphics even in bad network conditions or unoptimized server-side programming.

## Why?

1. **A reliable app framework:** If either the UI or app crash, the other can keep running until it restarts.
    * If the data source of truth is also seperated into another process or stored in an ACID database, app crashes can be transparent to the user (with no data lost!).
2. **A remote-desktop protocol:** Networked X11 is insufficient for modern app designs, and RDP is proprietary and complex.
3. **A separately updated UI framework:** If new requirements (E.g. Fractional scaling, VR/AR, etc.) become relevant it can be implemented once for all apps.
4. **Fast startup:** A cached scene-graph can be shown while a heavy app server is loading (such as Python or Java)
5. **Instant response over remote desktop:** The client knows how to draw the UI when resizing, etc.
6. **Flexible programming style:** Multiple ways of making a scene graph can be tested (Flutter / React / HTML / etc.) without reinventing the renderer.

## How?

### The scene-graph protocol

Currently, it's a JSON list because I don't want to commit to a binary protocol yet.

Here's a small example:

```json
[
   {"type": "clear", "color": 4280295472},
   {
      "type": "rect",
      "rect": [
         10,
         10,
         {"type": "sub", "a": {"type": "var", "name": "width"}, "b": 10},
         {"type": "sub", "a": {"type": "var", "name": "height"}, "b": 10}
      ],
      "color": 4288716960
   }
]
```

The "width" and "height" variables correspond to the dimensions of the client window. Here we subtract 10 from both to
determine the right and bottom coordinates of the rect.

As you can see, after clearing the screen, this scene draws a rectangle with a 10px padding on all sides.

### The low-level Python API

Instead of manually writing the JSON scene-graph, here's the first abstraction:

```python
scene = [
   Ops.clear(color=0xff202030),
   Ops.rect(
      rect=(
         10,
         10,
         Expr.var('width') - 10,
         Expr.var('height') - 10,
      ),
      color=0xffa0a0a0
   ),
]
```

This has two abstractions:

- Builder functions for the JSON objects
- Simple expression syntax (overloaded operation methods)

### The high-level Python API

The API above isn't very scalable because all coordinates are relative to the global scene dimensions. Instead we can
use a flutter-like layout protocol to make the layout declaratively, like so:

```python
scene = Clear(
    color=0xff202030,
    child=Padding(
        child=Rectangle(0xffa0a0a0),
        left=10, top=10, right=10, bottom=10
    ),
)
```

This "compiles" to the same scene-graph from above, because of the expression abstraction from before.

Special care is needed when writing complex layouts though, to keep expressions from exploding in size.