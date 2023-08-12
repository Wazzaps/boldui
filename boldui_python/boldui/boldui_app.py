import inspect
import json
import logging
import sqlite3
import struct
import sys
import time
import uuid
from typing import Dict, List, Any, Optional, Sequence, Callable, Tuple

from numpy import unsignedinteger, signedinteger, int64, floating, float64

from boldui.scene_mgmt import (
    Model,
    Session,
    ViewHandler,
    ReplyHandler,
    CurrentScene,
    _set_current_context,
    ClientSide,
    ModelNotBoundYet,
)

# noinspection PyUnresolvedReferences
from boldui.utils import (
    setup_logging,
    eprint,
    _FullWriter,
    _FullReader,
    _trace,
    _parse_relative_path,
)
from boldui_protocol import *
from serde_types import uint32

logger = logging.getLogger(__name__)


def _pack_state(source: Model) -> Dict[str, Any]:
    result = {}

    for field_name, field_type in type(source).__annotations__.items():
        if hasattr(field_type, "__metadata__") and field_type.__metadata__[0] in (
            "boldui-client-side",
            "boldui-scene-id",
        ):
            pass  # Skip client-side vars and scene IDs
        elif issubclass(field_type, Model):
            packed = _pack_state(getattr(source, field_name))
            if packed:
                result[field_name] = packed
        elif issubclass(field_type, unsignedinteger):
            result[field_name] = int(getattr(source, field_name))
        else:
            result[field_name] = getattr(source, field_name)

    return result


def _rehydrate_state(source: Dict[str, Any], dest: Model, ctx: str, app: "BoldUIApplication"):
    for field_name, field_type in type(dest).__annotations__.items():
        if typing.get_origin(field_type) is ClientSide:
            raise AssertionError(
                f"You probably meant ClientVar[...] as the type of '{field_name}'"
            )

        if hasattr(field_type, "__metadata__") and field_type.__metadata__[0] in (
            "boldui-client-side",
            "boldui-scene-id",
        ):
            if field_type.__metadata__[0] == "boldui-client-side":
                pass  # Skip client-side vars
        elif issubclass(field_type, Model):
            _rehydrate_state(
                source.get(field_name, {}),
                getattr(dest, field_name),
                f"{ctx}/{field_name}",
                app,
            )
        else:
            setattr(dest, field_name, source[field_name])
    dest.__post_init__()


def serialize_state(state: Model) -> str:
    return json.dumps(_pack_state(state) | {"_fmt_ver": 0})


def deserialize_state(serialized: str, state_factory: type, app: "BoldUIApplication") -> Model:
    new_state = state_factory()
    data = json.loads(serialized)
    fmt_ver = data.pop("_fmt_ver")
    assert fmt_ver == 0, "Invalid format version"
    _rehydrate_state(data, new_state, "", app)
    return new_state


@dataclass
class SceneState:
    session_id: str
    original_uri: str
    query_params: Dict[str, str]
    view_handler: ViewHandler


class BoldUIApplication:
    def __init__(self, state_factory: Callable[[], Model]):
        self._state_factory = state_factory
        self._sessions: Dict[str, Session] = {}
        self._scenes: Dict[SceneId, SceneState] = {}
        self._view_handlers: List[ViewHandler] = []
        self._reply_handlers: List[ReplyHandler] = []
        self._scene_id_counter = SceneId(1)
        self._db = None
        self.sent_resources = False  # FIXME: Hacky
        self.scenes_instantiated: set[SceneId] = set()
        self.state_initialized = False
        self.out = None
        self.stdout = None
        self.inp = None

    def alloc_scene_id(self) -> SceneId:
        result = self._scene_id_counter
        self._scene_id_counter += 1
        eprint(f"alloc_scene_id: {result}")
        return result

    def view(self, path: str):
        def _inner(handler):
            # TODO: Anonymous views?
            stripped_path = path.strip("/").split("/")
            handler_params = inspect.signature(handler).parameters

            assert len(handler_params) <= 2, (
                "Handler must accept at most 2 arguments, (state: MyState, query_params), or"
                " (state: MyState)"
            )
            accepts_query_params = len(handler_params) >= 2

            self._view_handlers.append(
                ViewHandler(
                    path=stripped_path,
                    handler=handler,
                    accepts_query_params=accepts_query_params,
                )
            )

            def _blocker(*_args, **_kwargs):
                # TODO: Replace with nested scenes
                raise RuntimeError("This function should not be called")

            return _blocker

        return _inner

    def reply_handler(self, path: str):
        def _inner(handler):
            # TODO: Anonymous views?
            stripped_path = path.strip("/").split("/")
            handler_params = inspect.signature(handler).parameters

            assert len(handler_params) <= 3, (
                "Handler must accept at most 3 arguments, (state: MyState, query_params,"
                " value_params), (state: MyState, query_params), or (state: MyState)"
            )
            accepts_query_params = len(handler_params) >= 2
            accepts_value_params = len(handler_params) >= 3

            self._reply_handlers.append(
                ReplyHandler(
                    path=stripped_path,
                    handler=handler,
                    accepts_query_params=accepts_query_params,
                    accepts_value_params=accepts_value_params,
                )
            )

            def _blocker(*_args, **_kwargs):
                # TODO: Replace with nested scenes
                raise RuntimeError("This function should not be called")

            return _blocker

        return _inner

    @staticmethod
    def setup_logging():
        setup_logging()

    def database(self, path):
        self._db = sqlite3.connect(path)

    def main_loop(self):
        if sys.stdout.isatty() or sys.stdin.isatty():
            eprint("Run this app like so:")
            eprint(
                (
                    "  cd ./examples/boldui_example_py_calc && cargo run -p boldui_renderer -- --"
                    " python boldui_example_py_calc"
                ),
            )
            exit(1)

        # Initialize DB
        if self._db:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS sessions (sess_id TEXT PRIMARY KEY,data TEXT NOT NULL)"
            )
            self._db.commit()

        self.stdout = _FullWriter(sys.stdout.buffer)
        self.inp = _FullReader(sys.stdin.buffer)

        # Get hello
        logger.debug("reading hello")
        magic = self.inp.read(len(R2A_MAGIC))
        assert magic == R2A_MAGIC, "Missing magic"
        # noinspection PyTypeChecker
        hello = R2AHello.bincode_deserialize_stream(self.inp)
        assert LATEST_MAJOR_VER <= hello.max_protocol_major_version and (
            LATEST_MAJOR_VER > hello.min_protocol_major_version
            or (
                LATEST_MAJOR_VER == hello.min_protocol_major_version
                and LATEST_MINOR_VER >= hello.min_protocol_minor_version
            )
        ), "Incompatible version"
        assert hello.extra_len == 0, "This protocol version specifies no extra data"

        # Reply with A2RHelloResponse
        logger.debug("sending hello response")
        self.stdout.write(A2R_MAGIC)
        self.stdout.write(
            A2RHelloResponse(
                protocol_major_version=st.uint16(LATEST_MAJOR_VER),
                protocol_minor_version=st.uint16(LATEST_MINOR_VER),
                extra_len=st.uint32(0),
                error=None,
            ).bincode_serialize()
        )
        logger.debug("connected!")

        # Run app
        try:
            while True:
                msg_len = self.inp.read_or_none(4)
                if msg_len is None:
                    logger.debug("connection closed, bye!")
                    return
                msg_len = struct.unpack("<I", msg_len)[0]
                _trace(f"reading message of size {msg_len}")

                msg: Any = R2AMessage.bincode_deserialize(self.inp.read(msg_len))
                _trace(f"R2A: {msg}")

                if type(msg) == R2AMessage__Update:
                    update: R2AUpdate = msg.value
                    for reply in update.replies:
                        path, params = _parse_relative_path(reply.path)
                        session_id = params.get("session", None)
                        self._handle_reply(path, session_id, params, list(reply.params))
                elif type(msg) == R2AMessage__Open:
                    open: R2AOpen = msg.value
                    path, params = _parse_relative_path(open.path)

                    session_id = params.get("session", str(uuid.uuid4()))
                    scene_id = self.alloc_scene_id()

                    time_start = time.time()
                    self._open_window(
                        scene_id=scene_id,
                        session_id=session_id,
                        raw_path=open.path,
                        path=path,
                        query_params=params,
                    )
                    time_end = time.time()
                    eprint(f"Open took {(time_end - time_start)*1000:.1f} ms in total")
                elif type(msg) == R2AMessage__Error:
                    err: Error = msg.value
                    logger.error(f"Renderer error: {err.code}: {err.text}")
                else:
                    raise RuntimeError(f"Unknown message type: {type(msg)}")
        except Exception as e:
            msg = A2RMessage__Error(
                Error(code=st.uint64(1), text=str(type(e).__name__) + ": " + str(e))
            ).bincode_serialize()
            self.stdout.write(struct.pack("<I", len(msg)))
            self.stdout.write(msg)
            raise

    def _get_view_handler_by_path(self, path: List[str]) -> Optional[ViewHandler]:
        for view_handler in self._view_handlers:
            if path == view_handler.path:
                return view_handler

    def _get_reply_handler_by_path(self, path: List[str]) -> Optional[ReplyHandler]:
        for reply_handler in self._reply_handlers:
            if path == reply_handler.path:
                return reply_handler

    def _fetch_raw_state(self, session_id, state_factory) -> Optional[Model]:
        if not self._db:
            return None

        if res := self._db.execute(
            "SELECT data FROM sessions s WHERE s.sess_id = ?",
            (session_id,),
        ).fetchone():
            return deserialize_state(res[0], state_factory, self)

    def _fetch_session(self, session_id, state_factory) -> Session:
        if session_id in self._sessions:
            return self._sessions[session_id]
        elif state_factory:
            if state := self._fetch_raw_state(session_id, state_factory):
                session = Session(
                    scene_ids=[],
                    state=state,
                    session_id=session_id,
                )
                self._sessions[session_id] = session
                return session
            else:
                state = state_factory()
                if self._db:
                    serialized = serialize_state(state)
                    self._db.execute(
                        "INSERT INTO sessions(sess_id, data) VALUES (?, ?)",
                        (session_id, serialized),
                    )
                    self._db.commit()
                session = Session(scene_ids=[], state=state, session_id=session_id)
                self._sessions[session_id] = session
                return session
        else:
            raise AssertionError(f"Unknown session {session_id}")

    def _handle_reply(
        self,
        path: List[str],
        session_id: Optional[str],
        query_params: Dict[str, str],
        value_params: List[Value],
    ):
        logger.debug(
            f"Handling reply: path={path} query_params={query_params} value_params={value_params}"
        )

        reply_handler = self._get_reply_handler_by_path(path)
        if reply_handler is None:
            raise RuntimeError(f"Could not find reply handler for path {path}")

        session = self._fetch_session(session_id, self._state_factory)
        _set_current_context(
            CurrentScene(app=self, scene=None, session_id=session_id, parent=None)
        )

        if reply_handler.accepts_value_params:
            reply_handler.handler(session.state, query_params, value_params)
        elif reply_handler.accepts_query_params:
            reply_handler.handler(session.state, query_params)
        else:
            reply_handler.handler(session.state)

        for scene_id in session.scene_ids:
            # FIXME: only rerun if relevant vars changed
            self._rerun_view_handler(scene_id)

        if self._db:
            serialized = serialize_state(session.state)
            self._db.execute(
                "UPDATE sessions SET data=? WHERE sess_id=?", (serialized, session_id)
            )
            self._db.commit()
        _set_current_context(None)

    def _rerun_view_handler(self, scene_id: SceneId):
        state = self._scenes[scene_id]
        session = self._sessions[state.session_id]
        query_params = state.query_params
        view_handler = state.view_handler
        scene = A2RUpdateScene(
            id=scene_id,
            attrs={},
            ops=[],
            cmds=[],
            watches=[],
            event_handlers=[],
        )
        ctx = CurrentScene(app=self, scene=scene, session_id=session.session_id, parent=None)
        _set_current_context(ctx)
        scene.attrs[uint32(SceneAttr__Uri.INDEX)] = ctx.value(state.original_uri).op
        if "window_id" in query_params:
            scene.attrs[uint32(SceneAttr__WindowId.INDEX)] = ctx.value(
                query_params["window_id"]
            ).op

        if session.state is not None and not self.state_initialized:
            new_vars: List[Tuple[VarId, Value]] = []
            self._bind_model_client_vars(session.state, "", new_vars)
            if new_vars:
                update = A2RUpdate(
                    updated_scenes=[],
                    run_blocks=[
                        HandlerBlock(
                            ops=[OpsOperation__Value(val) for _var, val in new_vars],
                            cmds=[
                                HandlerCmd__SetVar(var=var, value=OpId(uint32(0), uint32(i)))
                                for i, (var, _val) in enumerate(new_vars)
                            ],
                        ),
                    ],
                    resource_chunks=[],
                    resource_deallocs=[],
                    external_app_requests=[],
                )

                self.send_update(update)
            self.state_initialized = True

        time_start = time.time()
        if view_handler.accepts_query_params:
            view_handler.handler(session.state, query_params)
        else:
            view_handler.handler(session.state)
        time_end = time.time()
        eprint(f"View handler took {(time_end - time_start)*1000:.1f} ms")
        _set_current_context(None)

    def _open_window(
        self,
        scene_id: SceneId,
        session_id: str,
        raw_path: str,
        path: List[str],
        query_params: Dict[str, str],
    ):
        logger.debug(
            f"Opening window for scene {scene_id} for session {session_id} for path {repr(path)}"
        )

        view_handler = self._get_view_handler_by_path(path)
        if view_handler is None:
            logger.error(f"Could not find view handler for path {path}")
            msg = A2RMessage__Error(
                Error(code=st.uint64(1), text=f"Not found: {path}")
            ).bincode_serialize()
            self.stdout.write(struct.pack("<I", len(msg)))
            self.stdout.write(msg)
            return

        session = self._fetch_session(session_id, self._state_factory)
        session.scene_ids.append(scene_id)

        # Fix raw path
        raw_path = "/" + raw_path
        if "session" not in query_params:
            if len(query_params):
                raw_path += "&"
            else:
                raw_path += "?"
            raw_path += f"session={session_id}"

        self._scenes[scene_id] = SceneState(
            session_id=session_id,
            original_uri=raw_path,
            query_params=query_params,
            view_handler=view_handler,
        )

        self._rerun_view_handler(scene_id)
        self.scenes_instantiated.add(scene_id)

        if self._db:
            time_start = time.time()
            serialized = serialize_state(session.state)
            self._db.execute(
                "UPDATE sessions SET data=? WHERE sess_id=?", (serialized, session_id)
            )
            self._db.commit()
            time_end = time.time()
            eprint(f"DB commit took {(time_end - time_start)*1000:.1f} ms")

    def _bind_model_client_vars(self, model: Model, ctx: str, out_vars: List[Tuple[VarId, Value]]):
        for field_name, field_type in type(model).__annotations__.items():
            if typing.get_origin(field_type) is ClientSide:
                raise AssertionError(
                    f"You probably meant ClientVar[...] as the type of '{field_name}'"
                )

            if hasattr(field_type, "__metadata__") and field_type.__metadata__[0] in (
                "boldui-client-side",
                "boldui-scene-id",
            ):
                if field_type.__metadata__[0] == "boldui-client-side":
                    inner_val = typing.cast(
                        ModelNotBoundYet, getattr(model, field_name)
                    ).default_value
                    default_val = BoldUIApplication._wrap_value(inner_val)
                    assert default_val is not None
                    var_id = VarId(f"{ctx}/{field_name}")
                    out_vars.append((var_id, default_val))
                    setattr(model, field_name, ClientSide(_op=NullOpId, const_var=var_id))
                elif field_type.__metadata__[0] == "boldui-scene-id":
                    setattr(model, field_name, self.alloc_scene_id())
            elif issubclass(field_type, Model):
                self._bind_model_client_vars(
                    getattr(model, field_name), f"{ctx}/{field_name}", out_vars
                )

    @staticmethod
    def _wrap_value(val):
        if isinstance(val, Value):
            return val
        elif isinstance(val, (int, signedinteger)):
            return Value__Sint64(int64(val))
        elif isinstance(val, (float, floating)):
            return Value__Double(float64(val))
        elif isinstance(val, str):
            return Value__String(val)
        elif val is None:
            return None
        else:
            raise NotImplementedError(
                f"Value of type {type(val)} cannot be stored in a clientside field"
            )

    @staticmethod
    def find_unused_ops(update: A2RUpdate):
        seen_ops = set()
        used_ops = set()

        def visit(op_like: OpsOperation | CmdsCommand | HandlerCmd):
            for field in dir(op_like):
                if field.startswith("_"):
                    continue
                value = getattr(op_like, field)
                if isinstance(value, OpId):
                    used_ops.add(value)

        for scn in update.updated_scenes:
            for op_id, op in enumerate(scn.ops):
                seen_ops.add(OpId(scn.id, uint32(op_id)))
                visit(op)

            for cmd in scn.cmds:
                visit(cmd)

            for evt_hnd in scn.event_handlers:
                for cmd in evt_hnd.handler.cmds:
                    visit(cmd)

            for watch in scn.watches:
                seen_ops.add(watch.condition)
                for cmd in watch.handler.cmds:
                    visit(cmd)

        eprint("Unused ops:", repr(seen_ops - used_ops))

    def send_update(self, update: A2RUpdate):
        # FIXME: remove
        for scn in update.updated_scenes:
            OpListVisualizer(scn.ops, scn.cmds, scn.id).print()
            logging.info(f"{len(scn.cmds)} cmds")
        # self.find_unused_ops(update)

        msg = A2RMessage__Update(update).bincode_serialize()
        self.stdout.write(struct.pack("<I", len(msg)))
        self.stdout.write(msg)


class OpListVisualizer:
    def __init__(
        self,
        ops: Sequence[OpsOperation],
        cmds: Sequence[CmdsCommand],
        scene_id: SceneId,
    ):
        self.ops = ops
        self.cmds = cmds
        self.scene_id = scene_id
        self.use_counts = [0 for _ in self.ops]
        self.used_externally = [False for _ in self.ops]

        for op in self.ops:
            self._visit(op)

        for cmd in self.cmds:
            self._visit(cmd)

    def print(self):
        eprint("--- total scene ops:", len(self.ops))
        for i, op in enumerate(self.ops):
            if self.use_counts[i] == 0:
                eprint(f"[UNUSED] #{i} =", self.repr_op(op))
            elif self.use_counts[i] > 1 or self.used_externally[i]:
                eprint(f"#{i} =", self.repr_op(op))

    def repr_op(self, op: OpsOperation | OpId):
        match op:
            case OpsOperation__Value(value=value):
                match value:
                    case Value__Rect(left, top, right, bottom):
                        return f"Rect(l={left}, t={top}, r={right}, b={bottom})"
                    case Value__Color(value=value):
                        return (
                            f"rgba({int(value.r/65535*255)}, {int(value.g/65535*255)},"
                            f" {int(value.b/65535*255)}, {int(value.a/65535)})"
                        )
                    case Value__Point(left, top):
                        return f"Point({left}, {top})"
                    case _:
                        return repr(value.value)
            case OpsOperation__Var(value=var_id):
                var_id: VarId
                return f"var('{var_id.key}')"
            # case OpsOperation__GetTime():
            #     return repr(op)
            # case OpsOperation__GetTimeAndClamp():
            #     return repr(op)
            case OpsOperation__Add(a, b):
                return f"({self.repr_op(a)}) + ({self.repr_op(b)})"
            case OpsOperation__Neg(a):
                return f"-({self.repr_op(a)})"
            case OpsOperation__Mul(a, b):
                return f"({self.repr_op(a)}) * ({self.repr_op(b)})"
            case OpsOperation__Div(a, b):
                return f"({self.repr_op(a)}) / ({self.repr_op(b)})"
            case OpsOperation__FloorDiv(a, b):
                return f"({self.repr_op(a)}) // ({self.repr_op(b)})"
            case OpsOperation__Eq(a, b):
                return f"({self.repr_op(a)}) == ({self.repr_op(b)})"
            case OpsOperation__Min(a, b):
                return f"min({self.repr_op(a)}, {self.repr_op(b)})"
            case OpsOperation__Max(a, b):
                return f"max({self.repr_op(a)}, {self.repr_op(b)})"
            case OpsOperation__Or(a, b):
                return f"({self.repr_op(a)}) or ({self.repr_op(b)})"
            case OpsOperation__And(a, b):
                return f"({self.repr_op(a)}) and ({self.repr_op(b)})"
            case OpsOperation__GreaterThan(a, b):
                return f"({self.repr_op(a)}) > ({self.repr_op(b)})"
            case OpsOperation__Abs(a):
                return f"abs({self.repr_op(a)})"
            case OpsOperation__Sin(a):
                return f"sin({self.repr_op(a)})"
            case OpsOperation__Cos(a):
                return f"cos({self.repr_op(a)})"
            # case OpsOperation__MakePoint():
            #     return repr(op)
            # case OpsOperation__MakeRectFromPoints():
            #     return repr(op)
            case OpsOperation__MakeRectFromSides(left, top, right, bottom):
                return (
                    f"Rect(l=({self.repr_op(left)}), t=({self.repr_op(top)}),"
                    f" r=({self.repr_op(right)}), b=({self.repr_op(bottom)}))"
                )
            # case OpsOperation__ToString():
            #     return repr(op)
            case OpsOperation__If(condition, then, or_else):
                return (
                    f"if ({self.repr_op(condition)}) then ({self.repr_op(then)}) else"
                    f" ({self.repr_op(or_else)})"
                )
            case OpId(scene_id, idx):
                if scene_id == self.scene_id:
                    if self.use_counts[idx] == 1 and not self.used_externally[idx]:
                        return self.repr_op(self.ops[idx])
                    else:
                        return f"#{idx}"
                else:
                    return f"#{idx}@{scene_id}"
            case OpsOperation():
                # noinspection PyUnresolvedReferences
                fields = [
                    f"{f}={self.repr_op(getattr(op, f))}" for f in op.__dataclass_fields__.keys()
                ]
                return op.__class__.__name__ + "(" + ", ".join(fields) + ")"

            case _:
                return repr(op)

    def _visit(self, op_like: OpsOperation | CmdsCommand):
        for field in dir(op_like):
            if field.startswith("_"):
                continue
            value = getattr(op_like, field)
            if isinstance(value, OpId) and value.scene_id == self.scene_id:
                self.use_counts[value.idx] += 1
                if isinstance(op_like, CmdsCommand):
                    self.used_externally[value.idx] = True
