import dataclasses
from typing import Optional, List, Callable, Any, Dict, Tuple

from boldui_protocol import *

if typing.TYPE_CHECKING:
    from boldui.boldui_app import BoldUIApplication


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
class CurrentScene:
    app: "BoldUIApplication"
    scene: A2RUpdateScene | HandlerBlock | None
    session_id: Optional[str]
    children: List[A2RUpdateScene] = dataclasses.field(default_factory=list)

    def create_window(
        self,
        title: str,
        initial_size: (int, int) = (800, 600),
        extra_handler_block: Optional[HandlerBlock] = None,
        external_app_requests: List[ExternalAppRequest] = (),
    ):
        self.scene.var_decls[":window_title"] = Value__String(title)
        self.scene.var_decls[":window_initial_size_x"] = Value__Sint64(initial_size[0])
        self.scene.var_decls[":window_initial_size_y"] = Value__Sint64(initial_size[1])

        update = A2RUpdate(
            updated_scenes=[self.scene],
            run_blocks=[
                HandlerBlock(
                    ops=[],
                    cmds=[
                        HandlerCmd__ReparentScene(scene=self.scene.id, to=A2RReparentScene__Root()),
                    ],
                ),
            ],
            external_app_requests=external_app_requests,
        )
        if extra_handler_block:
            # noinspection PyUnresolvedReferences
            update.run_blocks.append(extra_handler_block)

        self.app.send_update(update)

    def decl_var(self, name: str, default_val: Value):
        self.scene.var_decls[name] = default_val

    def op(self, op: OpsOperation) -> OpWrapper:
        scene_id = 0
        if isinstance(self.scene, A2RUpdateScene):
            scene_id = self.scene.id
        op_id = OpId(scene_id, st.uint32(len(self.scene.ops)))
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

    # def open_external_widget(self, app: OpWrapper | Value__ExternalApp, uri: OpWrapper | str):
    #     return self.op(
    #         OpsOperation__OpenExternalWidget(
    #             app=self.value(app).op,
    #             uri=self.value(uri).op,
    #         ),
    #     )

    def push_cmd(self, cmd: CmdsCommand):
        # noinspection PyUnresolvedReferences
        self.scene.cmds.append(cmd)

    def push_hcmd(self, cmd: HandlerCmd):
        # noinspection PyUnresolvedReferences
        self.scene.cmds.append(cmd)

    def cmd_clear(self, color: OpWrapper):
        self.push_cmd(CmdsCommand__Clear(color=color.op))

    def cmd_draw_rect(self, paint: OpWrapper, rect: OpWrapper):
        self.push_cmd(CmdsCommand__DrawRect(paint=paint.op, rect=rect.op))

    def cmd_draw_centered_text(self, text: OpWrapper, paint: OpWrapper, center: OpWrapper):
        self.push_cmd(CmdsCommand__DrawCenteredText(text=text.op, paint=paint.op, center=center.op))

    def hcmd_reply(self, path: str, params: List[OpWrapper] | OpWrapper):
        if type(params) is not list:
            params = [params]
        self.push_hcmd(HandlerCmd__Reply(path=path, params=[r.op for r in params]))


def make_handler_block_factory(app: "BoldUIApplication"):
    return CurrentScene(app, HandlerBlock(ops=[], cmds=[]), session_id=None)


_CURRENT_SCENE: Optional[CurrentScene] = None


def get_current_scene() -> CurrentScene:
    assert _CURRENT_SCENE is not None, "get_current_scene() called outside of view handler"
    return _CURRENT_SCENE


def _set_current_scene(scene: Optional[CurrentScene]):
    global _CURRENT_SCENE
    _CURRENT_SCENE = scene


@dataclasses.dataclass
class Session:
    scene_ids: List[SceneId]
    state: Any
    session_id: str


@dataclasses.dataclass
class ViewHandler:
    path: List[str]
    handler: Callable[[Any, Dict[str, str]], None] | Callable[[Any], None]
    state_factory: Optional[Callable[[], Any]]
    accepts_query_params: bool


@dataclasses.dataclass
class ReplyHandler:
    path: List[str]
    handler: Callable[[Any, Dict[str, str], List[Value]], None] | Callable[[Any, Dict[str, str]], None] | Callable[
        [Any], None
    ]
    state_factory: Optional[Callable[[], Any]]
    accepts_query_params: bool
    accepts_value_params: bool
