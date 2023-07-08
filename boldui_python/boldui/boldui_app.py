import inspect
import logging
import struct
import sys
import uuid
import sqlite3
import dataclasses
import json
import dataclass_wizard
from typing import Dict, List, Any, Optional
from boldui.scene_mgmt import Session, ViewHandler, ReplyHandler, CurrentScene, _set_current_scene
from boldui_protocol import *

# noinspection PyUnresolvedReferences
from boldui.utils import setup_logging, eprint, print, _FullWriter, _FullReader, _trace, _parse_relative_path

logger = logging.getLogger(__name__)


class BoldUIApplication:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._scene_to_session: Dict[SceneId, str] = {}
        self._view_handlers: List[ViewHandler] = []
        self._reply_handlers: List[ReplyHandler] = []
        self._scene_id_counter = SceneId(1)
        self._db = None
        self.out = None
        self.inp = None

    def view(self, path: str):
        def _inner(handler):
            stripped_path = path.strip("/").split("/") if path else None
            handler_params = inspect.signature(handler).parameters

            assert (
                len(handler_params) <= 2
            ), "Handler must accept at most 2 arguments, (state: MyState, query_params), or (state: MyState)"
            accepts_query_params = len(handler_params) >= 2
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

    def reply_handler(self, path: str):
        def _inner(handler):
            stripped_path = path.strip("/").split("/") if path else None
            handler_params = inspect.signature(handler).parameters

            assert len(handler_params) <= 3, (
                "Handler must accept at most 3 arguments, (state: MyState, query_params, value_params), (state:"
                " MyState, query_params), or (state: MyState)"
            )
            accepts_query_params = len(handler_params) >= 2
            accepts_value_params = len(handler_params) >= 3
            state_factory = list(handler_params.values())[0].annotation if len(handler_params) >= 1 else (lambda: None)

            self._reply_handlers.append(
                ReplyHandler(
                    path=stripped_path,
                    handler=handler,
                    state_factory=state_factory,
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
                "  cd ./examples/boldui_example_py_calc && cargo run -p boldui_renderer -- -- python"
                " boldui_example_py_calc",
            )
            exit(1)

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
                msg: R2AUpdate = msg.value
                for reply in msg.replies:
                    path, params = _parse_relative_path(reply.path)
                    session_id = params.get("session", None)
                    self._handle_reply(path, session_id, params, list(reply.params))
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
                logger.error(f"Renderer error: {msg.code}: {msg.text}")
            else:
                raise RuntimeError(f"Unknown message type: {type(msg)}")

    def _get_view_handler_by_path(self, path: List[str]) -> Optional[ViewHandler]:
        for view_handler in self._view_handlers:
            if path == view_handler.path:
                return view_handler

    def _get_reply_handler_by_path(self, path: List[str]) -> Optional[ReplyHandler]:
        for reply_handler in self._reply_handlers:
            if path == reply_handler.path:
                return reply_handler
    
    def _fetch_raw_state(self, session_id) -> Optional[dict]:
        if not self._db:
            return None
        
        if res := self._db.execute(
            'SELECT data FROM sessions s WHERE s.sess_id = ?',
            (session_id,),
        ).fetchone():
            return json.loads(res[0])
    
    def _fetch_session(self, session_id, state_factory=None) -> Any:
        if state := self._fetch_raw_state(session_id):
            # Found session in DB
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.state = dataclass_wizard.fromdict(session.state_type, state)
                return session
            elif state_factory:
                state = dataclass_wizard.fromdict(type(state_factory()), state)
                session = Session(scene_ids=[], state=state, state_type=type(state), session_id=session_id)
                self._sessions[session_id] = session
                return session
            else:
                raise AssertionError(f"Cannot recreate session {session_id}")
        elif session_id in self._sessions:
            return self._sessions[session_id]
        elif state_factory:
            state = state_factory()
            if self._db:
                serialized = json.dumps(dataclasses.asdict(state))
                self._db.execute("INSERT INTO sessions(sess_id, data) VALUES (?, ?)", (session_id, serialized))
                self._db.commit()
            session = Session(scene_ids=[], state=state, state_type=type(state), session_id=session_id)
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
        logger.debug(f"Handling reply: path={path} query_params={query_params} value_params={value_params}")

        reply_handler = self._get_reply_handler_by_path(path)
        if reply_handler is None:
            logger.error(f"Could not find reply handler for path {path}")
            msg = A2RMessage__Error(Error(code=st.uint64(1), text=f"Not found: {path}")).bincode_serialize()
            self.stdout.write(struct.pack("<I", len(msg)))
            self.stdout.write(msg)
            return

        session = self._fetch_session(session_id)
        _set_current_scene(CurrentScene(app=self, scene=None, session_id=session_id))
        reply_handler.handler(session.state, query_params, value_params)
        if self._db:
            serialized = json.dumps(dataclasses.asdict(session.state))
            self._db.execute('UPDATE sessions SET data=? WHERE sess_id=?', (serialized, session_id))
            self._db.commit()
        _set_current_scene(None)

    def _open_window(self, scene_id: SceneId, session_id: str, path: List[str], query_params: Dict[str, str]):
        global _CURRENT_SCENE
        logger.debug(f"Opening window for scene {scene_id} for session {session_id} for path {repr(path)}")

        view_handler = self._get_view_handler_by_path(path)
        if view_handler is None:
            logger.error(f"Could not find view handler for path {path}")
            msg = A2RMessage__Error(Error(code=st.uint64(1), text=f"Not found: {path}")).bincode_serialize()
            self.stdout.write(struct.pack("<I", len(msg)))
            self.stdout.write(msg)
            return

        session = self._fetch_session(session_id, view_handler.state_factory)
        session.scene_ids.append(scene_id)

        self._scene_to_session[scene_id] = session_id

        scene = A2RUpdateScene(
            id=scene_id,
            paint=NullOpId,
            backdrop=NullOpId,
            transform=NullOpId,
            clip=NullOpId,
            dimensions=NullOpId,
            uri=f"/?session={session_id}",  # FIXME: Add actual path
            ops=[],
            cmds=[],
            var_decls={},
            watches=[],
            event_handlers=[],
        )
        if "window_id" in query_params:
            scene.var_decls[":window_id"] = Value__String(query_params["window_id"])
        _set_current_scene(CurrentScene(app=self, scene=scene, session_id=session_id))
        if view_handler.accepts_query_params:
            view_handler.handler(session.state, query_params)
        else:
            view_handler.handler(session.state)
        if self._db:
            serialized = json.dumps(dataclasses.asdict(session.state))
            self._db.execute('UPDATE sessions SET data=? WHERE sess_id=?', (serialized, session_id))
            self._db.commit()
        _set_current_scene(None)

    def send_update(self, update: A2RUpdate):
        msg = A2RMessage__Update(update).bincode_serialize()
        self.stdout.write(struct.pack("<I", len(msg)))
        self.stdout.write(msg)
