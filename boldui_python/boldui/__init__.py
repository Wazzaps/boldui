import dataclasses
import inspect
import logging
import struct
import sys
import uuid
from typing import Optional, Any, Dict, List, Callable, Tuple

from boldui_protocol import *

logger = logging.getLogger("boldui")


def _trace(msg, *args, **kwargs):
    logger.log(5, msg, *args, **kwargs)


def _parse_relative_path(path: str) -> (List[str], Dict[str, str]):
    import urllib.parse

    before_query, _, query = path.partition("?")
    query_dict = urllib.parse.parse_qs(query, keep_blank_values=True, strict_parsing=True) if query else {}
    query_dict = {k: v[0] for k, v in query_dict.items()}  # Ignore multiple values

    return before_query.lstrip("/").split("/"), query_dict


class _FullWriter:
    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def write(self, data: bytes):
        while data:
            wrote = self.stream.write(data)
            if wrote == 0:
                raise RuntimeError("Failed to write to stream")
            data = data[wrote:]
        self.stream.flush()


class _FullReader:
    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def read(self, size: int) -> bytes:
        data = b""
        while len(data) < size:
            chunk = self.stream.read(size - len(data))
            if not chunk:
                raise RuntimeError("Failed to read from stream")
            data += chunk
        return data

    def read_or_none(self, size: int) -> Optional[bytes]:
        data = b""
        while len(data) < size:
            chunk = self.stream.read(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data


@dataclasses.dataclass
class OpWrapper:
    op: OpId

    def __add__(self, other: "float | OpWrapper") -> "OpWrapper":
        scene = get_current_scene()
        return scene.op(OpsOperation__Add(self.op, scene.value(other).op))

    def __neg__(self):
        scene = get_current_scene()
        return scene.op(OpsOperation__Neg(self.op))

    def __sub__(self, other: "float | OpWrapper") -> "OpWrapper":
        scene = get_current_scene()
        return scene.op(OpsOperation__Add(self.op, scene.value(-other).op))

    def __mul__(self, other: "float | OpWrapper") -> "OpWrapper":
        scene = get_current_scene()
        return scene.op(OpsOperation__Mul(self.op, scene.value(other).op))

    def __truediv__(self, other: "float | OpWrapper") -> "OpWrapper":
        scene = get_current_scene()
        return scene.op(OpsOperation__Div(self.op, scene.value(other).op))


@dataclasses.dataclass
class Session:
    scene_ids: List[SceneId]
    state: Any
    session_id: str


@dataclasses.dataclass
class ViewHandler:
    path: List[str]
    handler: Callable[[Any, Dict[str, str]], None]
    state_factory: Optional[Callable[[], Any]]
    accepts_query_params: bool


@dataclasses.dataclass
class CurrentScene:
    app: "BoldUIApplication"
    scene: A2RUpdateScene
    children: List[A2RUpdateScene] = dataclasses.field(default_factory=list)

    def create_window(self, title: str, initial_size: (int, int) = (800, 600)):
        self.scene.var_decls[":window_title"] = Value__String(title)
        self.scene.var_decls[":window_initial_size_x"] = Value__Sint64(initial_size[0])
        self.scene.var_decls[":window_initial_size_y"] = Value__Sint64(initial_size[1])
        self.app.send_update(
            A2RUpdate(
                updated_scenes=[self.scene],
                run_blocks=[
                    HandlerBlock(
                        ops=[],
                        cmds=[
                            HandlerCmd__ReparentScene(scene=self.scene.id, to=A2RReparentScene__Root()),
                        ],
                    ),
                ],
            )
        )

    def decl_var(self, name: str, default_val: Value):
        self.scene.var_decls[name] = default_val

    def op(self, op: OpsOperation) -> OpWrapper:
        op_id = OpId(self.scene.id, st.uint32(len(self.scene.ops)))
        # noinspection PyUnresolvedReferences
        self.scene.ops.append(op)
        return OpWrapper(op_id)

    def value(self, val: float | int | str | Value | OpWrapper) -> OpWrapper:
        if type(val) is OpWrapper:
            return val
        elif isinstance(val, Value):
            return self.op(OpsOperation__Value(val))
        elif type(val) is float:
            return self.value(Value__Double(st.float64(val)))
        elif type(val) is int:
            return self.value(Value__Sint64(st.int64(val)))
        elif type(val) is str:
            return self.value(Value__String(val))
        else:
            raise TypeError(f"Unexpected type {type(val)}, expected float, int, str, Value, or OpWrapper")

    def color(self, r: float, g: float, b: float, a: float = 1.0) -> OpWrapper:
        return self.value(
            Value__Color(Color(st.uint16(r * 65535), st.uint16(g * 65535), st.uint16(b * 65535), st.uint16(a * 65535)))
        )

    def hex_color(self, hex_code: int) -> OpWrapper:
        return self.color(
            r=((hex_code >> 16) & 0xFF) / 255.0,
            g=((hex_code >> 8) & 0xFF) / 255.0,
            b=(hex_code & 0xFF) / 255.0,
        )

    def var_binding(self, name: str) -> VarId:
        return VarId(scene=self.scene.id, key=name)

    def var_value(self, var_id: VarId) -> OpWrapper:
        return self.op(OpsOperation__Var(var_id))

    def var(self, name: str) -> OpWrapper:
        return self.var_value(self.var_binding(name))

    def rect(
        self,
        left_top: Tuple[float | OpWrapper, float | OpWrapper] | OpWrapper,
        right_bottom: Tuple[float | OpWrapper, float | OpWrapper] | OpWrapper,
    ) -> OpWrapper:
        if type(left_top) is tuple and type(right_bottom) is tuple:
            left, top = left_top
            right, bottom = right_bottom
            if type(left) is float and type(top) is float and type(right) is float and type(bottom) is float:
                return self.value(Value__Rect(st.float64(left), st.float64(top), st.float64(right), st.float64(bottom)))
            else:
                left = self.value(left)
                top = self.value(top)
                right = self.value(right)
                bottom = self.value(bottom)
                return self.op(OpsOperation__MakeRectFromSides(left.op, top.op, right.op, bottom.op))
        else:
            if type(left_top) is tuple:
                left_top = self.point(left_top[0], left_top[1])
            if type(right_bottom) is tuple:
                right_bottom = self.point(right_bottom[0], right_bottom[1])

            return self.op(OpsOperation__MakeRectFromPoints(left_top.op, right_bottom.op))

    def point(self, left: float | OpWrapper, top: float | OpWrapper) -> OpWrapper:
        if type(left) is float and type(top) is float:
            return self.value(Value__Point(st.float64(left), st.float64(top)))
        else:
            return self.op(OpsOperation__MakePoint(self.value(left).op, self.value(top).op))

    def push_cmd(self, cmd: CmdsCommand):
        # noinspection PyUnresolvedReferences
        self.scene.cmds.append(cmd)

    def cmd_clear(self, color: OpWrapper):
        self.push_cmd(CmdsCommand__Clear(color=color.op))

    def cmd_draw_rect(self, paint: OpWrapper, rect: OpWrapper):
        self.push_cmd(CmdsCommand__DrawRect(paint=paint.op, rect=rect.op))

    def cmd_draw_centered_text(self, text: OpWrapper, paint: OpWrapper, center: OpWrapper):
        self.push_cmd(CmdsCommand__DrawCenteredText(text=text.op, paint=paint.op, center=center.op))


_CURRENT_SCENE: Optional[CurrentScene] = None


class BoldUIApplication:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._scene_to_session: Dict[SceneId, str] = {}
        self._view_handlers: List[ViewHandler] = []
        self._scene_id_counter = SceneId(1)
        self.stdout = None
        self.stdin = None

    def view(self, path: str):
        def _inner(handler):
            stripped_path = path.strip("/").split("/") if path else None
            handler_params = inspect.signature(handler).parameters

            assert (
                len(handler_params) <= 2
            ), "Handler must accept at most 2 arguments, (state: MyState, query_params), or (state: MyState)"
            accepts_query_params = len(handler_params) == 2
            state_factory = list(handler_params.values())[0].annotation if len(handler_params) >= 1 else (lambda: None)

            self._view_handlers.append(
                ViewHandler(
                    path=stripped_path,
                    handler=handler,
                    state_factory=state_factory,
                    accepts_query_params=accepts_query_params,
                )
            )

            def _blocker(*_args, **_kwargs):
                # TODO: Replace with nested scenes
                raise RuntimeError("This function should not be called")

            return _blocker

        return _inner

    @staticmethod
    def setup_logging():
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.DEBUG,
        )
        logging.addLevelName(5, "TRACE")

    def main_loop(self):
        if sys.stdout.isatty() or sys.stdin.isatty():
            print("Run this app like so:", file=sys.stderr)
            print(
                (
                    "  cd ./examples/boldui_example_py_calc && cargo run -p boldui_renderer -- -- python"
                    " boldui_example_py_calc"
                ),
                file=sys.stderr,
            )
            exit(1)

        self.stdout = _FullWriter(sys.stdout.buffer)
        self.stdin = _FullReader(sys.stdin.buffer)

        # Get hello
        logging.debug("reading hello")
        magic = self.stdin.read(len(R2A_MAGIC))
        assert magic == R2A_MAGIC, "Missing magic"
        # noinspection PyTypeChecker
        hello = R2AHello.bincode_deserialize_stream(self.stdin)
        assert LATEST_MAJOR_VER <= hello.max_protocol_major_version and (
            LATEST_MAJOR_VER > hello.min_protocol_major_version
            or (
                LATEST_MAJOR_VER == hello.min_protocol_major_version
                and LATEST_MINOR_VER >= hello.min_protocol_minor_version
            )
        ), "Incompatible version"
        assert hello.extra_len == 0, "This protocol version specifies no extra data"

        # Reply with A2RHelloResponse
        logging.debug("sending hello response")
        self.stdout.write(A2R_MAGIC)
        self.stdout.write(
            A2RHelloResponse(
                protocol_major_version=st.uint16(LATEST_MAJOR_VER),
                protocol_minor_version=st.uint16(LATEST_MINOR_VER),
                extra_len=st.uint32(0),
                error=None,
            ).bincode_serialize()
        )
        logging.debug("connected!")

        # Run app
        while True:
            msg_len = self.stdin.read_or_none(4)
            if msg_len is None:
                logging.debug("connection closed, bye!")
                return
            msg_len = struct.unpack("<I", msg_len)[0]
            _trace(f"reading message of size {msg_len}")

            msg: Any = R2AMessage.bincode_deserialize(self.stdin.read(msg_len))
            _trace(f"R2A: {msg}")

            if type(msg) == R2AMessage__Update:
                msg: R2AUpdate = msg.value
                for reply in msg.replies:
                    path, params = _parse_relative_path(reply.path)
                    self._handle_reply(path, params, list(reply.params))
            elif type(msg) == R2AMessage__Open:
                msg: R2AOpen = msg.value
                path, params = _parse_relative_path(msg.path)

                session_id = params.get("session", str(uuid.uuid4()))
                scene_id = self._scene_id_counter
                self._scene_id_counter += 1

                self._open_window(
                    scene_id=scene_id,
                    session_id=session_id,
                    path=path,
                    query_params=params,
                )
            elif type(msg) == R2AMessage__Error:
                msg: Error = msg.value
                logging.error(f"Renderer error: {msg.code}: {msg.text}")
            else:
                raise RuntimeError(f"Unknown message type: {type(msg)}")

    def _handle_reply(self, path: List[str], _query_params: Dict[str, str], _value_params: List[Value]):
        logging.info(f"TODO: handle_reply: {path}")

    def _get_view_handler_by_path(self, path: List[str]) -> Optional[ViewHandler]:
        for view_handler in self._view_handlers:
            if path == view_handler.path:
                return view_handler

    def _open_window(self, scene_id: SceneId, session_id: str, path: List[str], query_params: Dict[str, str]):
        global _CURRENT_SCENE
        logging.debug(f"Opening window for scene {scene_id} for session {session_id} for path {repr(path)}")

        view_handler = self._get_view_handler_by_path(path)
        if view_handler is None:
            logging.error(f"Could not find view handler for path {path}")
            msg = A2RMessage__Error(Error(code=st.uint64(1), text=f"Not found: {path}")).bincode_serialize()
            self.stdout.write(struct.pack("<I", len(msg)))
            self.stdout.write(msg)
            return

        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.scene_ids.append(scene_id)
        else:
            session = Session(scene_ids=[scene_id], state=view_handler.state_factory(), session_id=session_id)
            self._sessions[session_id] = session

        self._scene_to_session[scene_id] = session_id

        scene = A2RUpdateScene(
            id=scene_id,
            paint=NullOpId,
            backdrop=NullOpId,
            transform=NullOpId,
            clip=NullOpId,
            uri=f"/?session={session_id}",  # FIXME: Add actual path
            ops=[],
            cmds=[],
            var_decls={},
            watches=[],
            event_handlers=[],
        )
        if "window_id" in query_params:
            scene.var_decls[":window_id"] = Value__String(query_params["window_id"])
        _CURRENT_SCENE = CurrentScene(app=self, scene=scene)
        view_handler.handler(session.state, query_params)
        _CURRENT_SCENE = None

    def send_update(self, update: A2RUpdate):
        msg = A2RMessage__Update(update).bincode_serialize()
        self.stdout.write(struct.pack("<I", len(msg)))
        self.stdout.write(msg)


def get_current_scene() -> CurrentScene:
    assert _CURRENT_SCENE is not None, "get_current_scene() called outside of view handler"
    return _CURRENT_SCENE
