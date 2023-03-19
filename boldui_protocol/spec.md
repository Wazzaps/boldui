# BoldUI Spec v0.1 (DRAFT)

The BoldUI architecture is split into three main entities and the transport between them:

- The Renderer
- The App
- The Window Manager/WM (Optional)

They may all be in-process for performance.

The state framework and widget kit used by the Python implementation is not described in this document.

## BoldUI Renderer Spec v0.1

This component is responsible for presenting apps to the user.

### CLI Usage Example

```shell
# Run APP-CMD and use the BoldUI Protocol over stdin/stdout
boldui -- <APP-CMD>

# Open specific URI instead of "/"
boldui --uri='/foo/bar?some=params' -- <APP-CMD>

# Also open devtools
boldui --devtools -- <APP-CMD>
```

### Renderer State

- A tree of <u>**Scenes**</u>
    - Each scene consists of:
        - A unique non-zero 32-bit Scene ID
        - A <u>**Transform**</u> (2D transformation matrix)
        - A <u>**Paint**</u> (Affects how the scene is rendered, e.g. foreground blur)
        - A <u>**Backdrop Paint**</u> (Affects how parts under the scene are rendered, e.g. background blur)
        - A <u>**Clip**</u> (Masks the scene)
        - A list of <u>**Renderer Variable Declarations**</u>
        - A list of <u>**Operations**</u>
        - A list of <u>**Commands**</u>
        - A list of <u>**Watches**</u>
        - A list of <u>**Sub-Scenes**</u> (Scenes that are rendered after this scene)
        - A URI for the current scene
- A list of root scenes, each producing a window if applicable (or just the first one filling the framebuffer)

## BoldUI App Spec v0.1

See the Protocol spec for information about implementing an app that will connect to a renderer successfully.

### Reconnectable Scenes

The URI of a scene should lead to the same synchronized scene even when connected-to simultaneously from multiple renderers.

This should be handled by adding a query parameter named `session` with a random UUID when creating the scene.

e.g. `/` -> `/?session={UUID}`, or `/contacts/1/edit` -> `/contacts/1/edit?session={UUID}`

This is so root scenes can be moved between renderers on-the-fly, for features such as Remote Desktop, Extend Desktop, Unified Drag-and-Drop, and for reconnection over alternative transports.

### Window IDs

The renderer may pass the `window_id` query parameter, the app should pass it as-it as the `:window_id` variable on the root scene.

This is used to associate `open` requests with the opened window

## BoldUI Protocol Spec v0.1

**Note:** All references to messages by name refer to bincode-serialized structs, see `/boldui_protocol/src/lib.rs` and `/boldui_protocol_bindings/python/boldui_protocol/`.

**Note:** The current protocol version is 0.1.

**Note:** All numeric fields are sent as little-endian unless specified otherwise.

### Connection: Preamble

The renderer should send the following buffers:

- `magic` (raw bytes) = `BOLDUI\x00`
- `R2AHello` (contains length of `R2AExtendedHello` in `extra_len` field)
- `R2AExtendedHello`

The app should check if it supports any protocol version in the requested range, then reply the following fields:

- `magic` (raw bytes) = `BOLDUI\x01`
- `A2RHelloResponse` (contains length of `A2RExtendedHelloResponse` in `extra_len` field)
- `A2RExtendedHelloResponse`

All following messages should be length-prefixed (`u32`, little endian) `R2AMessage` and `A2RMessage` messages respectively.

### Connection: Initial scene

The renderer issues an "open" command like so:

```python
R2AMessage__Open(R2AOpen(path='/'))
```

Then the app replies with the requested scene:

```python
A2RMessage__Update(A2RUpdate(
    updated_scenes=[
        A2RUpdateScene(
            id=1,
            paint=0,
            backdrop=0,
            transform=0,
            clip=0,
            uri='/?session=...',
            ops=[],  # ...
            cmds=[],  # ...
            var_decls={},  # ...
            watches=[],  # ...
            event_handlers=[],  # ...
        )
    ],
    run_blocks=[
        HandlerBlock(
            ops=[],
            cmds=[
                HandlerCmd__ReparentScene(
                    scene=1,
                    to=A2RReparentScene__Root()
                )
            ]
        )
    ]
))
```

Then the renderer and the app exchange messages (e.g. `R2AUpdate` for new inputs and `A2RUpdate` for scene updates, etc.).

### Handler commands

Imperative commands that affect the state of the scene tree and can send replies to the app.

**Command list:**

- `Nop`: Does nothing
- `ReparentScene`: Changes the parent of the scene (or makes it a root scene, or disconnects it, or hides it)
- `UpdateVar`: Changes the value of a variable in a given scene
- `DebugMessage`: Logs a constant message in the renderer
- `Reply`: Sends an `R2AUpdate` to the app with a path and a list of `Value`s
- `If`: Depending on a given condition, executes on of two given lists of handler commands
  - NOTE: The handler command lists are not handler blocks, they reuse the same operation list as the parent handler block

### Handler blocks

A list of operations and a list of handler commands.

When the block is executed, the operation list is evaluated, and the results are available as scene #0 in the handler commands.

Can be triggered in response to events, watches, or by updates from the app.

### Operations

List of mathematical operations performed when a scene is drawn, or a handler is triggered.

It's not turing-complete on purpose, to ensure finite runtime, and limit heavy renderer-side computations.

TODO: Also defines primitives such as "Transformation Matrix", "Paint", "Clip", (etc.) for the respective scene fields.

TODO: Expand and list them, meanwhile see `protocol/src/lib.rs`.

### Commands

Draw primitives, event handler regions, (etc.), that use the results from previous **operations** to actually define the scene.

**Partial list:**

- `Clear`: Clears the screen
- `Rect`: Draws a colored rectangle
- `RoundRect`: Draws a colored round-rectangle
- `Text`: Draws text
- `Image`: Draws an image

TODO: Expand and list all of them

### Variables

Scene-attached state that can be referenced inside operations.

Can be one of the following types: `SInt64`, `Double`, `String`, `Color`, `Point`, `Rect`.

Created by a declaration in `A2RUpdateScene.var_decls`, and get deleted if their declaration is removed.

The value given in the declaration is the default value, replaced by `HandlerCmd::UpdateVar` handler commands during the lifetime of the scene.

Some special values affect the rendering of root scenes:

- `:width`, `:height`: Created by the renderer on root windows, specifies the current width of the window
- `:click_x`, `:click_y`, `:click_button`: Created by the renderer on root windows during handling of a click event, specifies the click info
- `:window_initial_size_x`, `:window_initial_size_y`: Supplied by the app (optional), specifies the initial window size of the window (if windowing supported)
- `:window_title`: Supplied by the app (optional), specifies the window title (if windowing supported)
- `:window_id`: Supplied by the app (optional), mirrors the value of the `window_id` query parameter during the `Open` that opened the window(s)

### Watches

Handlers that execute when a given (variable-dependent) condition becomes true.

**Example usages:**

- Fetch more items in a list view when needed.
- Notify a music player to buffer the next song when the current song is nearing completion.

### Event handlers

Lists of handler commands that trigger when a certain condition is met

TODO: Expand

## BoldUI Window Manager Spec v0.1

This component is responsible for combining multiple apps into a single connection for the renderer.

It implements both the app-side protocol (connected to a renderer) and the renderer-side protocol (connected to the multiple apps).

Window managers should be transparent to both the apps and the renderer, only providing extra features and multiplexing the scenes. Generally apps should work without a window manager.

The main features of a window manager are:

- App multiplexing: Allow multiple apps to connect to one renderer, mapping the scene ids between them
- Compositing: Move all the root scenes under one (per display?) root scene, to provide a desktop environment for full-screen and remote-desktop use cases 
- Embedding: Combine scenes from different apps under one root scene (like OLE in Windows)
  - It should provide an API to map scene ids between apps so this can work 
- "Server-side" decorations: Adding window frames to root scenes (mainly used with Compositing)
- Rendezvous: Provide a central source for apps and renderers to reconnect to on failure

TODO: Expand and specify API
