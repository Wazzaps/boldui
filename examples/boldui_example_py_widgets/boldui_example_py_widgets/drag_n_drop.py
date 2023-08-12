import dataclasses
from typing import Callable, Tuple, cast

from numpy import uint32

from boldui import get_current_scene, BoldUIApplication, eprint, print
from boldui.scene_mgmt import (
    Model,
    field,
    ClientSide,
    CurrentHandler,
    ClientVar,
    CurrentScene,
    SceneIdAlloc,
    make_handler_block_factory,
)
from boldui.widgets import Widget, Padding, Row, DBGHighlight, SizedBox, Text, Stack, Rectangle
from boldui_protocol import (
    EventType__MouseDown,
    EventType__MouseMove,
    VarId,
    Value__Point,
    Value__Rect,
    A2RReparentScene__Inside,
    SceneAttr__Transform,
    EventType__MouseUp,
    Value__VarRef,
    Value__Color,
    SceneAttr__Size,
)


# ------ App ------


class DragController(Widget):
    BUILDS_CHILDREN = True

    @dataclasses.dataclass
    class State(Model):
        drag_pos: ClientVar[Value__Point] = field(Value__Point(0, 0))
        drag_offset: ClientVar[Value__Point] = field(Value__Point(0, 0))
        is_dragging: ClientVar[int] = field(0)
        scene_being_dragged: ClientVar[int] = field(0)
        drag_source: ClientVar[int] = field(0)
        drag_source_scene_inside: ClientVar[Value__VarRef] = field(Value__VarRef(VarId("")))
        subscene_id: SceneIdAlloc = field(SceneIdAlloc)

    def __init__(self, child: Widget, state: State):
        self.child = child
        self._built_child = None
        self.state = state

    def build(self) -> Widget:
        self._built_child = self.child.build_recursively()
        return self

    def layout(
        self,
        scn: CurrentScene,
        min_width: ClientSide,
        min_height: ClientSide,
        max_width: ClientSide,
        max_height: ClientSide,
    ) -> Tuple[ClientSide, ClientSide]:
        return self._built_child.layout(scn, min_width, min_height, max_width, max_height)

    def render(
        self,
        scn: CurrentScene,
        left: ClientSide,
        top: ClientSide,
        right: ClientSide,
        bottom: ClientSide,
    ):
        # Event handler under children
        def on_mouse_up(h: CurrentHandler) -> ClientSide[int]:
            condition = self.state.is_dragging

            @lambda f: h.if_(condition, f)
            def if_droppable(then: CurrentHandler):
                then.set_var(self.state.is_dragging, then.value(0))
                then.set_var(self.state.drag_offset, ClientSide.point(0, 0))
                then.set_var_by_ref(
                    self.state.drag_source_scene_inside, self.state.scene_being_dragged
                )
                then.set_var(self.state.scene_being_dragged, then.value(0))
                then.set_var(self.state.drag_source, then.value(0))
                then.set_var(
                    self.state.drag_source_scene_inside, then.value(Value__VarRef(VarId("")))
                )
                then.reparent_scene(
                    self.state.scene_being_dragged,
                    A2RReparentScene__Inside(then.value(self.state.drag_source).op),
                )

            # Continue handling events if not handled here
            return condition.not_()

        scn.add_event_handler(
            EventType__MouseUp(scn.rect((left, top), (right, bottom)).op), on_mouse_up
        )

        # The child
        self._built_child.render(scn, left, top, right, bottom)

        # Event handler over the child
        def on_move(h: CurrentHandler):
            h.set_var(
                self.state.drag_pos, ClientSide.point(scn.var(":mouse_x"), scn.var(":mouse_y"))
            )
            return h.value(1)

        scn.add_event_handler(
            EventType__MouseMove(scn.rect((left, top), (right, bottom)).op), on_move
        )

        sub_scene = scn.sub_scene(
            self.state.subscene_id,
            lambda inner_scn: inner_scn.cmd_draw_rect(
                inner_scn.hex_color(0xAAFFAA), inner_scn.rect((0, 0), (5, 5))
            ),
        )
        sub_scene.set_attr(SceneAttr__Transform, self.state.drag_pos + self.state.drag_offset)
        sub_scene.set_attr(SceneAttr__Size, ClientSide.point(300, 300))


class DragSlot(Widget):
    BUILDS_CHILDREN = True

    @dataclasses.dataclass
    class State(Model):
        subscene_id: SceneIdAlloc = field(SceneIdAlloc)
        scene_inside: ClientVar[int] = field(0)

    def __init__(self, drag_controller: DragController.State, state: State):
        self.drag_controller = drag_controller
        self.state = state

    def build(self) -> "Widget":
        return self

    def layout(
        self,
        scn: CurrentScene,
        min_width: ClientSide,
        min_height: ClientSide,
        max_width: ClientSide,
        max_height: ClientSide,
    ) -> Tuple[ClientSide, ClientSide]:
        return min_width, min_height

    def render(
        self,
        scn: CurrentScene,
        left: ClientSide,
        top: ClientSide,
        right: ClientSide,
        bottom: ClientSide,
    ) -> None:
        # Add empty subscene
        sub_scene = scn.sub_scene(self.state.subscene_id, lambda _: None)
        sub_scene.set_attr(SceneAttr__Transform, ClientSide.point(left, top))
        sub_scene.set_attr(SceneAttr__Size, ClientSide.point(right - left, bottom - top))

        def on_mouse_up(h: CurrentHandler) -> ClientSide[int]:
            condition = self.drag_controller.is_dragging & (self.state.scene_inside == 0)

            @lambda f: h.if_(condition, f)
            def if_droppable(then: CurrentHandler):
                then.set_var(self.drag_controller.is_dragging, then.value(0))
                then.set_var(self.drag_controller.drag_offset, ClientSide.point(0, 0))
                then.set_var(self.state.scene_inside, self.drag_controller.scene_being_dragged)
                then.set_var(self.drag_controller.scene_being_dragged, then.value(0))
                then.set_var(self.drag_controller.drag_source, then.value(0))
                then.set_var(
                    self.drag_controller.drag_source_scene_inside,
                    then.value(Value__VarRef(VarId(""))),
                )
                then.reparent_scene(
                    self.drag_controller.scene_being_dragged,
                    A2RReparentScene__Inside(then.value(int(self.state.subscene_id)).op),
                )

            # Continue handling events if not handled here
            return condition.not_()

        scn.add_event_handler(
            EventType__MouseUp(scn.rect((left, top), (right, bottom)).op), on_mouse_up
        )

        def on_mouse_down(h: CurrentHandler):
            not_condition = self.drag_controller.is_dragging | (self.state.scene_inside == 0)

            @lambda f: h.if_(not_condition, or_else=f)
            def if_draggable(then: CurrentHandler):
                then.set_var(
                    self.drag_controller.drag_offset,
                    ClientSide.point(-scn.var(":click_x") + left, -scn.var(":click_y") + top),
                )
                then.reparent_scene(
                    self.state.scene_inside,
                    A2RReparentScene__Inside(then.value(int(self.drag_controller.subscene_id)).op),
                )
                then.set_var(self.drag_controller.is_dragging, then.value(1))
                then.set_var(self.drag_controller.scene_being_dragged, self.state.scene_inside)
                then.set_var(self.drag_controller.drag_source, then.value(int(sub_scene.scene.id)))
                then.set_var(
                    self.drag_controller.drag_source_scene_inside,
                    then.var_ref(self.state.scene_inside),
                )
                then.set_var(self.state.scene_inside, then.value(0))

            # Continue handling events if not handled here
            return not_condition

        scn.add_event_handler(
            EventType__MouseDown(scn.rect((left, top), (right, bottom)).op), on_mouse_down
        )


class Draggable(Widget):
    BUILDS_CHILDREN = True

    @dataclasses.dataclass
    class State(Model):
        drag_slot: DragSlot.State = field(DragSlot.State)
        subscene_id: SceneIdAlloc = field(SceneIdAlloc)

    def __init__(self, child: Widget, drag_controller: DragController.State, state: State):
        self.child = child
        self._built_child = None
        self.drag_slot = DragSlot(drag_controller, state.drag_slot)
        self.drag_controller = drag_controller
        self.state = state

    def get_flex_x(self, scn: CurrentScene) -> float:
        if self._built_child:
            return self._built_child.get_flex_x(scn)
        else:
            return 0

    def get_flex_y(self, scn: CurrentScene) -> float:
        if self._built_child:
            return self._built_child.get_flex_y(scn)
        else:
            return 0

    def build(self) -> Widget:
        self._built_child = self.child.build_recursively()
        return self

    def layout(
        self,
        scn: CurrentScene,
        min_width: ClientSide,
        min_height: ClientSide,
        max_width: ClientSide,
        max_height: ClientSide,
    ) -> Tuple[ClientSide, ClientSide]:
        return self._built_child.layout(scn, min_width, min_height, max_width, max_height)

    def render(
        self,
        scn: CurrentScene,
        left: ClientSide,
        top: ClientSide,
        right: ClientSide,
        bottom: ClientSide,
    ) -> None:
        self.drag_slot.render(scn, left, top, right, bottom)

        # Render child in a subscene
        sub_scene = scn.sub_scene(
            self.state.subscene_id,
            lambda inner_scn: self._built_child.render(
                inner_scn, scn.value(0), scn.value(0), right - left, bottom - top
            ),
            show=False,
        )

        sub_scene.set_attr(SceneAttr__Size, ClientSide.point(right - left, bottom - top))

        with scn.on_window_create as h:
            # Put draggable under drag slot
            h.reparent_scene(
                self.state.subscene_id,
                A2RReparentScene__Inside(h.value(int(self.state.drag_slot.subscene_id)).op),
            )
            h.set_var(self.state.drag_slot.scene_inside, h.value(int(self.state.subscene_id)))


@dataclasses.dataclass
class State(Model):
    drag_controller: DragController.State = field(DragController.State)
    draggable1: Draggable.State = field(Draggable.State)
    draggable2: Draggable.State = field(Draggable.State)
    draggable3: Draggable.State = field(Draggable.State)
    draggable4: Draggable.State = field(Draggable.State)
    drag_slot1: DragSlot.State = field(DragSlot.State)
    drag_slot2: DragSlot.State = field(DragSlot.State)


app = BoldUIApplication(State)


def draggable_box(
    box_size: int,
    color: ClientSide[Value__Color],
    state: Draggable.State,
    drag_controller: DragController.State,
):
    s = get_current_scene()
    return DBGHighlight(
        SizedBox(
            Draggable(
                Stack(
                    Padding(Rectangle(color), all=2),
                    Text("Drag me", s.hex_color(0xFFFFFF)),
                ),
                drag_controller,
                state,
            ),
            width=box_size,
            height=box_size,
        )
    )


def drag_slot(box_size, state: DragSlot.State, drag_controller: DragController.State):
    return DBGHighlight(
        SizedBox(
            DragSlot(drag_controller, state),
            width=box_size,
            height=box_size,
        )
    )


@app.view("/")
def main_view(state: State):
    box_size = 150
    padding = 25

    s = get_current_scene()

    widget = DragController(
        Padding(
            Row(
                draggable_box(
                    box_size, s.hex_color(0x441111), state.draggable1, state.drag_controller
                ),
                SizedBox(width=padding),
                draggable_box(
                    box_size, s.hex_color(0x114411), state.draggable2, state.drag_controller
                ),
                SizedBox(width=padding),
                draggable_box(
                    box_size, s.hex_color(0x111144), state.draggable3, state.drag_controller
                ),
                SizedBox(width=padding),
                draggable_box(
                    box_size, s.hex_color(0x441144), state.draggable4, state.drag_controller
                ),
                SizedBox(width=padding),
                drag_slot(box_size, state.drag_slot1, state.drag_controller),
                SizedBox(width=padding),
                drag_slot(box_size, state.drag_slot2, state.drag_controller),
            ),
            all=padding,
        ),
        state=state.drag_controller,
    )

    width = s.var(f":width_{s.scene.id}")
    height = s.var(f":height_{s.scene.id}")
    built = widget.build_recursively()
    built_width, built_height = built.layout(s, width, height, width, height)
    built.render(s, s.value(0), s.value(0), built_width, built_height)

    s.create_window(
        title="Drag and drop demo",
        initial_size=(1100, 300),
    )


def main():
    app.setup_logging()
    app.database("./app.db")
    app.main_loop()


if __name__ == "__main__":
    main()
