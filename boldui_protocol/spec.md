# BoldUI Spec v0.1 (DRAFT)

The BoldUI architecture is split into two main entities and the transport between them:

- The Renderer
- The App

They may both be in-process for performance.

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
        - A per-connection-unique 64-bit ID
        - A <u>**Transform**</u> (2D transformation matrix)
        - A <u>**Paint**</u> (Affects how the scene is rendered, e.g. foreground blur)
        - A <u>**Backdrop Paint**</u> (Affects how parts under the scene are rendered, e.g. background blur)
        - A list of <u>**Renderer Variable Declarations**</u>
        - A list of <u>**Operations**</u>
        - A list of <u>**Commands**</u>
        - A list of <u>**Watches**</u>
        - A list of <u>**Sub-Scenes**</u> (Scenes that are rendered after this scene)
        - A URI for the current scene

## BoldUI App Spec v0.1

See the Protocol spec for information about implementing an app that will connect to a renderer successfully.

### Reconnectable Scene

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

Then the renderer and the app exchange messages (e.g. `R2AUpdate` for new inputs and `A2RUpdate` for scene and var updates).

### Operations

List of mathematical operations performed when a scene is drawn, or a handler is triggered.

It's not turing-complete on purpose, to ensure finite runtime, and limit heavy renderer-side computations.

TODO: Also defines primitives such as "Transformation Matrix", "Paint", "Clip", (etc.) for the respective scene fields.

TODO: Expand and list them, meanwhile see `protocol/src/lib.rs`.

### Commands

Draw primitives, event handler regions, (etc.), that use the results from previous **operations** to actually define the scene.

**Partial list:**

- `clear`: Clears the screen
- `rect`: Draws a colored rectangle
- `roundRect`: Draws a colored round-rectangle
- `text`: Draws text
- `image`: Draws an image
- `eventHandler`: Defines an area that evaluates a handler when an input event happens

TODO: Expand and list all of them

### Variables

Scene-attached state that can be referenced inside operations.

Can be one of the following types: `Int64`, `Float64`, `String`.

Created by a declaration in `A2RUpdateScene.var_decls`, and get deleted if their declaration is removed.

The value given in the declaration is the default value, replaced by `VarUpdate`s in `A2RUpdate.updated_vars` during the lifetime of the scene.

Note that `VarUpdate` have no access to results of ops in the parent scene, only to other variables.

### Watches

Handlers that execute when a given (variable-dependent) condition becomes true.

**Example usages:**

- Fetch more items in a list view when needed.
- Notify a music player to buffer the next song when the current song is nearing completion.

TODO: Expand
