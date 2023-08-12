import copy
import dataclasses
import logging
import math
from typing import (
    Annotated,
    Generic,
    Optional,
    List,
    Callable,
    Any,
    Dict,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    TYPE_CHECKING,
    Type,
)
from typing_extensions import Self

from numpy import int64, uint32, float64, uint8
from boldui_protocol import *

# noinspection PyUnresolvedReferences
from boldui.utils import eprint, print

if TYPE_CHECKING:
    from boldui.boldui_app import BoldUIApplication


T = TypeVar("T")


@dataclasses.dataclass
class ClientSide(Generic[T]):
    # Unless you handle const propagation, use the `op` property instead
    # If you only handle int/float const propagation, use `_flush_var._op`
    _op: OpId

    # Basic constant propagation
    const_mul: float | int = 1
    const_add: float | int = 0
    const_var: Optional[VarId] = None

    @property
    def _flush_var(self) -> "ClientSide":
        if self.const_var is None:
            return self
        else:
            # Op Caching should make this efficient
            return get_current_scene().op(OpsOperation__Var(self.const_var))

    @property
    def op(self) -> OpId:
        # Op Caching should make this efficient
        scene = get_current_scene()
        res = self._flush_var

        if self.const_mul == -1:
            res = scene.op(OpsOperation__Neg(res._op))
        elif self.const_mul == 0:
            return self._flush_const(scene, self.const_add)._op
        elif self.const_mul == 1:
            pass
        else:
            res = scene.op(
                OpsOperation__Mul(res._op, self._flush_const(scene, self.const_mul)._op)
            )

        if self.const_add != 0:
            res = scene.op(
                OpsOperation__Add(res._op, self._flush_const(scene, self.const_add)._op)
            )

        return res._op

    @staticmethod
    def _flush_const(scene: "CurrentScene | CurrentHandler", val: int | float) -> "ClientSide":
        if type(val) is float:
            return scene.value(Value__Double(st.float64(val)))
        elif type(val) is int:
            return scene.value(Value__Sint64(st.int64(val)))
        else:
            raise TypeError()

    def __add__(self, other: "ClientVar[int | float | Value__Point]") -> "ClientSide":
        # TODO: `Value::Point` const prop
        if isinstance(other, (float, int)):
            return ClientSide(self._flush_var._op, self.const_mul, self.const_add + other)
        elif isinstance(other, ClientSide) and other.const_mul == 0:
            return ClientSide(
                self._flush_var._op, self.const_mul, self.const_add + other.const_add
            )
        elif isinstance(other, ClientSide) and self.const_mul == 0:
            return ClientSide(
                other._flush_var._op, other.const_mul, self.const_add + other.const_add
            )
        elif isinstance(other, ClientSide) and self._flush_var._op == other._flush_var._op:
            return ClientSide(
                self._flush_var._op,
                self.const_mul + other.const_mul,
                self.const_add + other.const_add,
            )
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__Add(self.op, other.op))

    def __neg__(self):
        return ClientSide(self._flush_var._op, -self.const_mul, -self.const_add)

    def __sub__(self, other: "ClientVar[int | float]") -> "ClientSide":
        return self + (-other)

    def __mul__(self, other: "ClientVar[int | float]") -> "ClientSide":
        if isinstance(other, (float, int)):
            return ClientSide(self._flush_var._op, self.const_mul * other, self.const_add * other)
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__Mul(self.op, scene.value(other).op))

    def __truediv__(self, other: "ClientVar[int | float]") -> "ClientSide":
        if isinstance(other, (float, int)):
            return ClientSide(self._flush_var._op, self.const_mul / other, self.const_add / other)
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__Div(self._flush_var.op, scene.value(other).op))

    def __floordiv__(self, other: "ClientVar[int | float]") -> "ClientSide":
        if self.const_mul == 0 and isinstance(other, (int, float)):
            return ClientSide(self._flush_var._op, self.const_mul, int(self.const_add // other))
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__FloorDiv(self.op, scene.value(other).op))

    def __abs__(self) -> "ClientSide":
        if self.const_mul == 0:
            return ClientSide(self._flush_var._op, self.const_mul, abs(self.const_add))
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__Abs(self.op))

    def not_(self):
        if self.const_mul == 0:
            return ClientSide(self._flush_var._op, self.const_mul, 0 if self.const_add else 1)
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__Eq(self.op, get_current_scene().value(0).op))

    def min(self, other: "ClientVar[int | float]") -> "ClientSide":
        if self.const_mul == 0 and isinstance(other, ClientSide) and other.const_mul == 0:
            return ClientSide(
                self._flush_var._op,
                self.const_mul,
                min(self.const_add, other.const_add),
            )
        elif self.const_mul == 0 and isinstance(other, (int, float)):
            return ClientSide(self._flush_var._op, self.const_mul, min(self.const_add, other))
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__Min(self.op, scene.value(other).op))

    def max(self, other: "ClientVar[int | float]") -> "ClientSide":
        if self.const_mul == 0 and other.const_mul == 0:
            return ClientSide(
                self._flush_var._op,
                self.const_mul,
                max(self.const_add, other.const_add),
            )
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__Max(self.op, scene.value(other).op))

    def sin(self) -> "ClientSide":
        if self.const_mul == 0:
            return ClientSide(self._flush_var._op, self.const_mul, math.sin(self.const_add))
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__Sin(self.op))

    def cos(self) -> "ClientSide":
        if self.const_mul == 0:
            return ClientSide(self._flush_var._op, self.const_mul, math.cos(self.const_add))
        else:
            scene = get_current_scene()
            return scene.op(OpsOperation__Cos(self._flush_var.op))

    def __eq__(self, other: "ClientVar") -> "ClientSide":
        # TODO: more const prop
        scn = get_current_scene()
        other = scn.value(other)
        if (
            self._op == other._op
            and self.const_mul == other.const_mul
            and self.const_add == other.const_add
            and self.const_var == other.const_var
        ):
            return scn.value(1)
        return scn.op(OpsOperation__Eq(self.op, scn.value(other).op))

    def __ne__(self, other: "ClientVar") -> "ClientSide":
        # TODO: more const prop
        scn = get_current_scene()
        other = scn.value(other)
        if (
            self._op == other._op
            and self.const_mul == other.const_mul
            and self.const_add == other.const_add
            and self.const_var == other.const_var
        ):
            return scn.value(0)
        return scn.op(OpsOperation__Neq(self.op, scn.value(other).op))

    def __or__(self, other: "ClientSide") -> "ClientSide":
        # TODO: const prop?
        scene = get_current_scene()
        return scene.op(OpsOperation__Or(self.op, scene.value(other).op))

    def __and__(self, other: "ClientSide") -> "ClientSide":
        # TODO: const prop?
        scene = get_current_scene()
        return scene.op(OpsOperation__And(self.op, scene.value(other).op))

    def __gt__(self, other: "ClientSide") -> "ClientSide":
        # TODO: const prop?
        scene = get_current_scene()
        return scene.op(OpsOperation__GreaterThan(self.op, scene.value(other).op))

    @staticmethod
    def point(left: "float | ClientSide", top: "float | ClientSide") -> "ClientSide":
        scn = get_current_scene()
        if type(left) is float and type(top) is float:
            return scn.value(Value__Point(float64(left), float64(top)))
        else:
            left = scn.value(left)._flush_var
            top = scn.value(top)._flush_var
            if left.const_mul == 0 and top.const_mul == 0:
                return scn.value(Value__Point(float64(left.const_add), float64(top.const_add)))
            else:
                return scn.op(OpsOperation__MakePoint(left.op, top.op))

    @staticmethod
    def if_(
        condition: "bool | ClientSide",
        then: Callable[[], "ClientSide"],
        or_else: Callable[[], "ClientSide"],
    ) -> "ClientSide":  # FIXME: |int|float|...
        s = get_current_scene()
        if (
            isinstance(condition, ClientSide)
            and condition.const_mul == 0
            and condition.const_var is None
        ):
            assert condition.const_add in (0, 1), "Condition must be either 0 or 1"
            condition = bool(condition.const_add)

        if condition is True:
            return then()
        elif condition is False:
            return or_else()
        else:
            return s.op(
                OpsOperation__If(
                    s.value(condition).op,
                    s.value(then()).op,
                    s.value(or_else()).op,
                )
            )


@dataclasses.dataclass
class CurrentContext:
    app: "BoldUIApplication"
    scene: A2RUpdateScene | HandlerBlock | None
    session_id: Optional[str]
    parent: Optional["CurrentScene"]
    _op_cache: Dict[OpsOperation, OpId] = dataclasses.field(default_factory=dict)
    _prev_ctx: Optional["CurrentContext"] = None  # Used for context manager

    def op(self, op: OpsOperation) -> ClientSide:
        if op in self._op_cache:
            return ClientSide(self._op_cache[op])

        scene_id = 0
        if isinstance(self.scene, A2RUpdateScene):
            scene_id = self.scene.id
        op_id = OpId(scene_id, st.uint32(len(self.scene.ops)))
        self._op_cache[op] = op_id
        # noinspection PyUnresolvedReferences
        self.scene.ops.append(op)
        return ClientSide(op_id)

    def value(self, val: float | int | str | bool | Value | ClientSide) -> ClientSide:
        if type(val) is ClientSide:
            return val
        elif isinstance(val, Value):
            return self.op(OpsOperation__Value(val))
        elif type(val) in (float, int):
            assert val != float("inf") and val != float("-inf"), "Infinity is temporarily disabled"
            return ClientSide(NullOpId, 0, val)
        elif type(val) is bool:
            return ClientSide(NullOpId, 0, int(val))
        elif type(val) is str:
            return self.value(Value__String(val))
        else:
            raise TypeError(
                f"Unexpected type {type(val)}, expected float, int, str, Value, or ClientSide"
            )

    def color(
        self,
        r: "ClientVar[float]",
        g: "ClientVar[float]",
        b: "ClientVar[float]",
        a: "ClientVar[float]" = 1.0,
    ) -> ClientSide:
        if all(type(x) is float for x in (r, g, b, a)):
            return self.value(
                Value__Color(
                    Color(
                        st.uint16(r * 65535),
                        st.uint16(g * 65535),
                        st.uint16(b * 65535),
                        st.uint16(a * 65535),
                    )
                )
            )
        else:
            return self.op(
                OpsOperation__MakeColor(
                    ((self.value(r) * 65535) // 1).op,
                    ((self.value(g) * 65535) // 1).op,
                    ((self.value(b) * 65535) // 1).op,
                    ((self.value(a) * 65535) // 1).op,
                )
            )

    def hex_color(self, hex_code: int) -> ClientSide:
        return self.color(
            r=((hex_code >> 16) & 0xFF) / 255.0,
            g=((hex_code >> 8) & 0xFF) / 255.0,
            b=(hex_code & 0xFF) / 255.0,
        )

    @staticmethod
    def var_value(var_id: VarId) -> ClientSide:
        return ClientSide(NullOpId, const_var=var_id)

    @staticmethod
    def var_ref(var: VarId | ClientSide) -> ClientSide:
        s = get_current_scene()
        if type(var) is ClientSide:
            assert var.const_var is not None, "Cannot create var_ref of non-variable"
            var = var.const_var
        return s.value(Value__VarRef(var))

    def time(self, clamp: Optional[Tuple["ClientVar", "ClientVar"]] = None) -> ClientSide:
        if clamp:
            return self.op(
                OpsOperation__GetTimeAndClamp(self.value(clamp[0]).op, self.value(clamp[1]).op)
            )
        else:
            return self.op(OpsOperation__GetTime())

    def rect(
        self,
        left_top: Tuple[float | ClientSide, float | ClientSide] | ClientSide,
        right_bottom: Tuple[float | ClientSide, float | ClientSide] | ClientSide,
    ) -> ClientSide:
        if type(left_top) is tuple and type(right_bottom) is tuple:
            left, top = left_top
            right, bottom = right_bottom
            if (
                type(left) is float
                and type(top) is float
                and type(right) is float
                and type(bottom) is float
            ):
                return self.value(
                    Value__Rect(
                        st.float64(left),
                        st.float64(top),
                        st.float64(right),
                        st.float64(bottom),
                    )
                )
            else:
                left = self.value(left)
                top = self.value(top)
                right = self.value(right)
                bottom = self.value(bottom)
                return self.op(
                    OpsOperation__MakeRectFromSides(left.op, top.op, right.op, bottom.op)
                )
        else:
            if type(left_top) is tuple:
                left_top = ClientSide.point(left_top[0], left_top[1])
            if type(right_bottom) is tuple:
                right_bottom = ClientSide.point(right_bottom[0], right_bottom[1])

            return self.op(OpsOperation__MakeRectFromPoints(left_top.op, right_bottom.op))

    def if_(
        self,
        condition: bool | ClientSide,
        then: Callable[[Self], None] = lambda _: None,
        or_else: Callable[[Self], None] = lambda _: None,
    ):
        if (
            isinstance(condition, ClientSide)
            and condition.const_mul == 0
            and condition.const_var is None
        ):
            assert condition.const_add in (0, 1), "Condition must be either 0 or 1"
            condition = bool(condition.const_add)

        if condition is True:
            then(self)
        elif condition is False:
            or_else(self)
        else:
            if isinstance(self, CurrentScene):
                raise NotImplementedError()
            elif isinstance(self, CurrentHandler):
                then_hnd = copy.copy(self)
                then_hnd.scene = HandlerBlock(self.scene.ops, [])
                with then_hnd:
                    then(then_hnd)
                or_else_hnd = copy.copy(self)
                or_else_hnd.scene = HandlerBlock(self.scene.ops, [])
                with or_else_hnd:
                    or_else(or_else_hnd)
                self._push_hcmd(
                    HandlerCmd__If(
                        self.value(condition).op,
                        then_hnd.scene.cmds,
                        or_else_hnd.scene.cmds,
                    )
                )

    def get_closest_scene(self):
        if isinstance(self, A2RUpdateScene):
            return self
        else:
            return self.parent.get_closest_scene()

    # def open_external_widget(self, app: ClientSide | Value__ExternalApp, uri: ClientSide | str):
    #     return self.op(
    #         OpsOperation__OpenExternalWidget(
    #             app=self.value(app).op,
    #             uri=self.value(uri).op,
    #         ),
    #     )

    def __exit__(self, exc_type, exc_val, exc_tb):
        _set_current_context(self._prev_ctx)


@dataclasses.dataclass
class CurrentHandler(CurrentContext):
    def _push_hcmd(self, cmd: HandlerCmd):
        # noinspection PyUnresolvedReferences
        self.scene.cmds.append(cmd)

    def reply(
        self,
        path: str,
        params: List[float | int | str | Value | ClientSide]
        | float
        | int
        | str
        | Value
        | ClientSide
        | None = None,
        add_session_id: bool = True,
    ):
        if params is None:
            params = []
        elif type(params) is not list:
            params = [params]
        if add_session_id:
            if "?" in path:
                path += "&"
            else:
                path += "?"
            path += f"session={self.session_id}"
        self._push_hcmd(HandlerCmd__Reply(path=path, params=[self.value(r).op for r in params]))

    def set_var(
        self,
        var: VarId | ClientSide,
        value: ClientSide,
    ):
        if type(var) is ClientSide:
            if var.const_var is None:
                self._push_hcmd(HandlerCmd__SetVarByRef(var=var.op, value=value.op))
                return
            else:
                var = var.const_var
        self._push_hcmd(HandlerCmd__SetVar(var=var, value=value.op))

    def set_var_by_ref(
        self,
        var: ClientSide,
        value: ClientSide,
    ):
        self._push_hcmd(HandlerCmd__SetVarByRef(var=var.op, value=value.op))

    def reparent_scene(self, scene: SceneId | ClientSide[int], to: A2RReparentScene):
        if not isinstance(scene, ClientSide):
            scene = self.value(int(scene))
        self._push_hcmd(HandlerCmd__ReparentScene(scene=scene.op, to=to))

    def open(self, path: str, add_session_id: bool = True):
        if add_session_id:
            if "?" in path:
                path += "&"
            else:
                path += "?"
            path += f"session={self.session_id}"
        self._push_hcmd(HandlerCmd__Open(path=path))

    def __enter__(self) -> "CurrentHandler":
        self._prev_ctx = get_current_scene()
        _set_current_context(self)
        return self


@dataclasses.dataclass
class CurrentScene(CurrentContext):
    sub_scenes: List[Tuple["CurrentScene", bool]] = dataclasses.field(default_factory=list)
    on_window_create: CurrentHandler = dataclasses.field(init=False)

    def __post_init__(self):
        self.on_window_create = CurrentHandler(
            app=self.app,
            scene=HandlerBlock([], []),
            session_id=self.session_id,
            parent=self,
        )

    def _get_all_subscenes(self) -> List["A2RUpdateScene"]:
        return [sub_scene[0].scene for sub_scene in self.sub_scenes] + sum(
            [sub_scene[0]._get_all_subscenes() for sub_scene in self.sub_scenes], []
        )

    def _get_all_subscene_reparents(self) -> List["HandlerCmd__ReparentScene"]:
        result = []
        h = get_current_handler()
        sub_scenes = [subscene[0] for subscene in self.sub_scenes if subscene[1]]
        for i, subscene in enumerate(sub_scenes):
            subscene: CurrentScene
            if i == 0:
                result.append(
                    HandlerCmd__ReparentScene(
                        scene=h.value(int(subscene.scene.id)).op,
                        to=A2RReparentScene__Inside(h.value(int(self.scene.id)).op),
                    )
                )
            else:
                result.append(
                    HandlerCmd__ReparentScene(
                        scene=h.value(int(subscene.scene.id)).op,
                        to=A2RReparentScene__After(h.value(int(sub_scenes[i - 1].scene.id)).op),
                    )
                )
            result += subscene._get_all_subscene_reparents()
        return result

    def create_window(
        self,
        title: str,
        initial_size: Tuple[int, int] = (800, 600),
        external_app_requests: Sequence[ExternalAppRequest] = (),
        resources: Dict[ResourceId, bytes] = None,
    ):
        if resources is None:
            resources = {}

        self.scene: A2RUpdateScene
        self.scene.attrs[uint32(SceneAttr__WindowTitle.INDEX)] = self.value(
            Value__String(title)
        ).op
        self.scene.attrs[uint32(SceneAttr__Size.INDEX)] = ClientSide.point(*initial_size).op

        extra_handler_block = (
            self.on_window_create.scene
            if self.scene.id not in self.app.scenes_instantiated
            else HandlerBlock([], [])
        )

        with make_handler_block_factory(self.app, extra_handler_block) as h:
            cast(list, h.scene.cmds).append(
                HandlerCmd__ReparentScene(
                    scene=h.value(int(self.scene.id)).op, to=A2RReparentScene__Root()
                )
            )
            cast(list, h.scene.cmds).extend(self._get_all_subscene_reparents())

        update = A2RUpdate(
            updated_scenes=[self.scene, *self._get_all_subscenes()],
            run_blocks=[],
            resource_chunks=(
                [
                    ResourceChunk(res_id, uint32(0), typing.cast(Sequence[uint8], res_data))
                    for res_id, res_data in resources.items()
                ]
                if not self.app.sent_resources
                else []
            ),
            resource_deallocs=[],
            external_app_requests=external_app_requests,
        )
        if extra_handler_block.ops or extra_handler_block.cmds:
            # noinspection PyUnresolvedReferences
            update.run_blocks.append(extra_handler_block)

        self.app.send_update(update)
        self.app.sent_resources = True

    def add_watch(self, condition: ClientSide, handler: Callable[["CurrentHandler"], None]):
        inner = make_handler_block_factory(self.app)
        handler(inner)
        # noinspection PyUnresolvedReferences
        self.scene.watches.append(Watch(condition=condition.op, handler=inner.scene))

    def add_event_handler(
        self,
        event: EventType,
        handler: Callable[["CurrentHandler"], ClientSide[int]],
    ):
        inner = make_handler_block_factory(self.app)
        prev_scene = get_current_scene()
        _set_current_context(inner)
        continue_handling = handler(inner)
        _set_current_context(prev_scene)

        if continue_handling is None:
            continue_handling = self.value(0)

        # noinspection PyUnresolvedReferences
        self.scene.event_handlers.append(EventHandler(event, inner.scene, continue_handling.op))

    @staticmethod
    def var(name: str) -> ClientSide:
        return CurrentScene.var_value(VarId(name))

    def sub_scene(
        self, scene_id, view: "Callable[[CurrentScene], None]", show=True
    ) -> "CurrentScene":
        curr_scene = get_current_scene()
        if show:
            if scene_id in curr_scene.app.scenes_instantiated:
                logging.warning("Same subscene was shown twice, did you reuse a SceneIdAlloc?")
            curr_scene.app.scenes_instantiated.add(scene_id)
        new_scene = CurrentScene(
            self.app,
            A2RUpdateScene(
                id=scene_id,
                attrs={},
                ops=[],
                cmds=[],
                watches=[],
                event_handlers=[],
            ),
            self.session_id,
            parent=curr_scene,
        )
        _set_current_context(new_scene)
        view(new_scene)
        _set_current_context(curr_scene)
        curr_scene.sub_scenes.append((new_scene, show))
        return new_scene

    def _push_cmd(self, cmd: CmdsCommand):
        # noinspection PyUnresolvedReferences
        self.scene.cmds.append(cmd)

    def cmd_clear(self, color: ClientSide):
        self._push_cmd(CmdsCommand__Clear(color=color.op))

    def cmd_draw_rect(self, paint: ClientSide, rect: ClientSide):
        self._push_cmd(CmdsCommand__DrawRect(paint=paint.op, rect=rect.op))

    def cmd_draw_centered_text(self, text: ClientSide, paint: ClientSide, center: ClientSide):
        self._push_cmd(
            CmdsCommand__DrawCenteredText(text=text.op, paint=paint.op, center=center.op)
        )

    def cmd_draw_image(self, resource_id: int | ClientSide, top_left: Value__Point | ClientSide):
        self._push_cmd(
            CmdsCommand__DrawImage(
                res=self.value(resource_id).op, top_left=self.value(top_left).op
            )
        )

    def set_attr(self, attr: Type[SceneAttr], value: ClientSide):
        # noinspection PyUnresolvedReferences
        self.scene.attrs[uint32(attr.INDEX)] = value.op

    def __enter__(self) -> "CurrentScene":
        self._prev_ctx = get_current_scene()
        _set_current_context(self)
        return self


def make_handler_block_factory(
    app: "BoldUIApplication", scene: Optional[HandlerBlock] = None
) -> CurrentHandler:
    current_scene = get_current_scene()
    return CurrentHandler(
        app,
        HandlerBlock(ops=[], cmds=[]) if scene is None else scene,
        session_id=current_scene.session_id,
        parent=current_scene,
    )


_CURRENT_SCENE: Optional[CurrentScene | CurrentHandler] = None


def get_current_scene() -> CurrentScene:
    assert _CURRENT_SCENE is not None, "get_current_scene() called outside of view handler"
    return _CURRENT_SCENE


def get_current_handler() -> CurrentHandler:
    assert _CURRENT_SCENE is not None, "get_current_scene() called outside of handler"
    return _CURRENT_SCENE


def _set_current_context(scene: Optional[CurrentScene | CurrentHandler]):
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
    accepts_query_params: bool


@dataclasses.dataclass
class ReplyHandler:
    path: List[str]
    handler: Callable[[Any, Dict[str, str], List[Value]], None] | Callable[
        [Any, Dict[str, str]], None
    ] | Callable[[Any], None]
    accepts_query_params: bool
    accepts_value_params: bool


class ModelNotBoundYet:
    def __init__(self, default_value: Any):
        self.default_value = default_value


@dataclasses.dataclass
class Model:
    def __post_init__(self):
        for field_name, field_type in type(self).__annotations__.items():
            if (
                hasattr(field_type, "__metadata__")
                and field_type.__metadata__[0] == "boldui-client-side"
            ):
                # Extract the T of ClientSide[T]
                annotation = field_type.__args__[0].__args__[0].__args__[0]
                default_val = getattr(self, field_name)
                if isinstance(default_val, ModelNotBoundYet):
                    default_val = default_val.default_value
                actual_type = type(default_val)

                if actual_type is int and annotation is float:
                    default_val = float(default_val)
                    actual_type = float

                assert (
                    actual_type is annotation
                ), f"Field {field_name} has type {actual_type} but expected {annotation}"

                setattr(self, field_name, ModelNotBoundYet(default_val))


ClientVar = Annotated[Union[ClientSide[T], Any], "boldui-client-side"]

SceneIdAlloc = Annotated[SceneId, "boldui-scene-id"]


def field(val: Callable[[], T] | Any = dataclasses.MISSING, init: bool = True) -> T:
    if hasattr(val, "__call__"):
        return dataclasses.field(default_factory=val, init=init)
    else:
        return dataclasses.field(default=val, init=init)
