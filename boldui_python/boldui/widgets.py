import abc
from typing import List, Optional, Tuple, Literal, Callable, TypeVar
from boldui.scene_mgmt import CurrentScene, ClientSide, ClientVar, CurrentHandler
from boldui_protocol import Color, EventType__MouseDown, EventType__MouseUp

# noinspection PyUnresolvedReferences
from boldui.utils import eprint

T = TypeVar("T")


class Widget:
    BUILDS_CHILDREN = False

    def layout(
        self,
        scn: CurrentScene,
        min_width: ClientSide,
        min_height: ClientSide,
        max_width: ClientSide,
        max_height: ClientSide,
    ) -> Tuple[ClientSide, ClientSide]:
        raise RuntimeError("This widget shouldn't be rendered directly")

    def render(
        self,
        scn: CurrentScene,
        left: ClientSide,
        top: ClientSide,
        right: ClientSide,
        bottom: ClientSide,
    ) -> None:
        raise RuntimeError("This widget shouldn't be rendered directly")

    @abc.abstractmethod
    def build(self) -> "Widget":
        pass

    def build_recursively(self) -> "Widget":
        if self.BUILDS_CHILDREN:
            return self.build()
        else:
            built = self.build()
            while not type(built).BUILDS_CHILDREN:
                built = built.build()
            return built.build()

    def get_flex_x(self, scn: CurrentScene) -> float:
        return 0

    def get_flex_y(self, scn: CurrentScene) -> float:
        return 0


class Row(Widget):
    BUILDS_CHILDREN = True

    def __init__(self, children, perp_align="middle"):
        self.children = children
        self.perp_align = perp_align
        self._built_children = []
        super(Row, self).__init__()

    def __repr__(self):
        return "Row(perp_align={}, children={})".format(self.perp_align, self.children)

    def get_flex_x(self, scn: CurrentScene) -> float:
        total_flex_x = sum((child.get_flex_x(scn) for child in self._built_children), scn.value(0))
        return 1 if total_flex_x else 0

    def get_flex_y(self, scn: CurrentScene) -> float:
        total_flex_y = sum((child.get_flex_y(scn) for child in self._built_children), scn.value(0))
        return 1 if total_flex_y else 0

    def build(self) -> Widget:
        self._built_children = []
        for child in self.children:
            self._built_children.append(child.build_recursively())
        return self

    def layout(self, scn: CurrentScene, min_width, min_height, max_width, max_height):
        children_flex_x = [child.get_flex_x(scn) for child in self._built_children]
        children_flex_y = [child.get_flex_y(scn) for child in self._built_children]
        total_flex_x = sum(children_flex_x, scn.value(0))
        total_flex_y = sum(children_flex_y, scn.value(0))

        width = max_width
        height = max_height

        # One of the axis are not flexible, need to calculate actual size
        children_sizes = [[scn.value(0), scn.value(0)] for _ in self._built_children]
        for i, (child, child_flex_x, child_flex_y) in enumerate(
            zip(self._built_children, children_flex_x, children_flex_y)
        ):
            get_layout = lazy(lambda: child.layout(scn, 0, min_height, max_width, max_height))
            children_sizes[i][0] = scn.if_(
                child_flex_x == 0, lambda: get_layout()[0], lambda: scn.value(0)
            )
            children_sizes[i][1] = scn.if_(
                child_flex_y == 0, lambda: get_layout()[1], lambda: scn.value(0)
            )

        width = scn.if_(
            total_flex_x == 0,
            lambda: sum((size[0] for size in children_sizes), scn.value(0)),
            lambda: width,
        )

        def get_biggest_height() -> ClientSide:
            result = scn.value(0)
            for size in children_sizes:
                result = result.max(size[1])
            return result

        height = scn.if_(total_flex_y == 0, get_biggest_height, lambda: height)

        return width, height

    def render(self, scn: CurrentScene, left, top, right, bottom):
        start = left
        end = right
        perp_start = top
        perp_end = bottom
        get_flex = lambda w: w.get_flex_x(scn)
        get_flex_perp = lambda w: w.get_flex_y(scn)
        norm_axis = lambda p: (p[0], p[1])
        # ----
        free_space = end - start

        children_flex = [get_flex(child) for child in self._built_children]
        children_flex_perp = [get_flex_perp(child) for child in self._built_children]
        total_flex = sum(children_flex, scn.value(0))

        # = (Our axis, Perpendicular axis)
        children_sizes = [[scn.value(0), scn.value(0)] for _ in self._built_children]

        for i, (child, child_flex, child_flex_perp) in enumerate(
            zip(self._built_children, children_flex, children_flex_perp)
        ):
            cond = child_flex == 0 or child_flex_perp == 0
            get_layout = lazy(
                lambda: norm_axis(
                    child.layout(
                        scn,
                        scn.value(0),
                        scn.value(0),
                        right - left,
                        bottom - top,
                    )
                )
            )
            children_sizes[i][0] = scn.if_(
                cond,
                lambda: get_layout()[0],
                lambda: children_sizes[i][0],
            )
            children_sizes[i][1] = scn.if_(
                cond,
                lambda: get_layout()[1],
                lambda: children_sizes[i][1],
            )
            free_space = scn.if_(
                child_flex == 0,
                lambda: free_space - children_sizes[i][0],
                lambda: free_space,
            )

        get_per_flex_unit_size = lazy(lambda: free_space.max(0) / total_flex)

        # eprint("--------------", free_space)
        # eprint("--------------", per_flex_unit_size)
        # leftovers = free_space - (per_flex_unit_size * total_flex)
        # eprint("--------------", leftovers)
        floating_size_so_far = scn.value(0)

        children_starts: List[Optional[ClientSide]] = [None for _ in self._built_children]
        children_ends: List[Optional[ClientSide]] = [None for _ in self._built_children]
        for i, child_flex_x in enumerate(children_flex):
            children_sizes[i][0] = scn.if_(
                child_flex_x > 0,
                # = per_flex_unit_size * child_flex_x
                lambda: get_per_flex_unit_size() * child_flex_x,
                lambda: children_sizes[i][0],
            )
            new_size_so_far = floating_size_so_far + children_sizes[i][0]
            children_starts[i] = start + floating_size_so_far // 1
            children_ends[i] = start + new_size_so_far // 1
            floating_size_so_far = new_size_so_far

        for i, child_flex_perp in enumerate(children_flex_perp):
            children_sizes[i][1] = scn.if_(
                child_flex_perp > 0,
                lambda: perp_end - perp_start,
                lambda: children_sizes[i][1],
            )

        for i, (child, child_size, child_start, child_end) in enumerate(
            zip(self._built_children, children_sizes, children_starts, children_ends)
        ):
            if self.perp_align == "middle":
                item_perp_start = perp_start + (perp_end - perp_start - child_size[1]) // 2
            elif self.perp_align == "start":
                item_perp_start = perp_start
            else:
                raise RuntimeError("Unknown alignment: {}".format(self.perp_align))
            item_perp_end = item_perp_start + child_size[1]

            child.render(
                scn,
                children_starts[i],
                item_perp_start,
                children_ends[i],
                item_perp_end,
            )

        # ///

        # current_left_coord = left
        # for i, (child, child_size) in enumerate(
        #     zip(self._built_children, children_sizes)
        # ):
        #     if self.perp_align == "middle":
        #         item_top = top + (bottom - top - child_size[1]) // 2
        #         item_bottom = top + (bottom - top + child_size[1]) // 2
        #     elif self.perp_align == "start":
        #         item_top = top
        #         item_bottom = top + child_size[1]
        #     else:
        #         raise RuntimeError("Unknown alignment: {}".format(self.align))
        #     child.render(
        #         scn,
        #         current_left_coord,
        #         item_top,
        #         current_left_coord + child_size[0],
        #         item_bottom,
        #     )
        #     current_left_coord += child_size[0]


# class Column(Widget):
#     # FIXME: flex is not clientside settable due to ifs
#     BUILDS_CHILDREN = True
#
#     def __init__(self, children, align="center"):
#         self.children = children
#         self.align = align
#         self._built_children = []
#         super(Column, self).__init__()
#
#     def __repr__(self):
#         return "Column(align={}, children={})".format(self.align, repr(self.children))
#
#     def get_flex_x(self, scn: CurrentScene) -> float:
#         total_flex = sum((child.get_flex_x(scn) for child in self._built_children), scn.value(0))
#         return 1 if total_flex else 0
#
#     def get_flex_y(self, scn: CurrentScene) -> float:
#         total_flex = sum((child.get_flex_y(scn) for child in self._built_children), scn.value(0))
#         return 1 if total_flex else 0
#
#     def build(self) -> Widget:
#         self._built_children = []
#         for child in self.children:
#             self._built_children.append(child.build_recursively())
#         return self
#
#     def layout(self, scn: CurrentScene, min_width, min_height, max_width, max_height):
#         children_flex_x = [child.get_flex_x(scn) for child in self._built_children]
#         children_flex_y = [child.get_flex_y(scn) for child in self._built_children]
#         total_flex_x = sum(children_flex_x, scn.value(0))
#         total_flex_y = sum(children_flex_y, scn.value(0))
#
#         width = max_width
#         height = max_height
#
#         # One of the axis are not flexible, need to calculate actual size
#         if total_flex_x == 0 or total_flex_y == 0:
#             children_sizes = [[scn.value(0), scn.value(0)] for _ in self._built_children]
#             for i, (child, child_flex_x, child_flex_y) in enumerate(
#                 zip(self._built_children, children_flex_x, children_flex_y)
#             ):
#                 if child_flex_x == 0 or child_flex_y == 0:
#                     children_sizes[i] = list(child.layout(scn, 0, min_height, scn.value(float("inf")), max_height))
#
#             if total_flex_x == 0:
#                 width = scn.value(0)
#                 for size in children_sizes:
#                     width = width.max(size[0])
#             if total_flex_y == 0:
#                 height = sum((size[1] for size in children_sizes), scn.value(0))
#
#         return width, height
#
#     def render(self, scn: CurrentScene, left, top, right, bottom):
#         free_space = bottom - top
#
#         children_flex_x = [child.get_flex_x(scn) for child in self._built_children]
#         children_flex_y = [child.get_flex_y(scn) for child in self._built_children]
#         children_sizes = [[scn.value(0), scn.value(0)] for _ in self._built_children]
#         total_flex = sum(children_flex_y, scn.value(0))
#
#         for i, (child, child_flex_x, child_flex_y) in enumerate(
#             zip(self._built_children, children_flex_x, children_flex_y)
#         ):
#             if child_flex_x == 0 or child_flex_y == 0:
#                 children_sizes[i] = list(
#                     child.layout(
#                         scn,
#                         scn.value(0),
#                         scn.value(0),
#                         right - left,
#                         scn.value(float("inf")),
#                     )
#                 )
#                 if child_flex_y == 0:
#                     free_space -= children_sizes[i][1]
#
#         per_flex_unit_size = abs(free_space) // total_flex
#         for i, child_flex_y in enumerate(children_flex_y):
#             if child_flex_y > 0:
#                 children_sizes[i][1] = per_flex_unit_size * child_flex_y
#
#         for i, child_flex_x in enumerate(children_flex_x):
#             if child_flex_x > 0:
#                 children_sizes[i][0] = right - left
#
#         current_top_coord = top
#         for i, (child, child_size) in enumerate(zip(self._built_children, children_sizes)):
#             if self.align == "center":
#                 item_left = left + (right - left - child_size[0]) // 2
#                 item_right = left + (right - left + child_size[0]) // 2
#             elif self.align == "top":
#                 item_left = left
#                 item_right = left + child_size[0]
#             else:
#                 raise RuntimeError("Unknown alignment: {}".format(self.align))
#             child.render(
#                 scn,
#                 item_left,
#                 current_top_coord,
#                 item_right,
#                 current_top_coord + child_size[1],
#             )
#             current_top_coord += child_size[1]


class Padding(Widget):
    BUILDS_CHILDREN = True

    # noinspection PyShadowingBuiltins
    def __init__(
        self,
        child,
        left=0,
        top=0,
        right=0,
        bottom=0,
        horizontal=None,
        vertical=None,
        all=None,
    ):
        self.child = child
        self._built_child = None

        if all is not None:
            self.left = all
            self.top = all
            self.right = all
            self.bottom = all
        else:
            self.left = left
            self.top = top
            self.right = right
            self.bottom = bottom
        if horizontal is not None:
            self.left = horizontal
            self.right = horizontal
        if vertical is not None:
            self.top = vertical
            self.bottom = vertical

        super(Padding, self).__init__()

    def __repr__(self):
        return "Padding(left={}, top={}, right={}, bottom={}, child={})".format(
            self.left, self.top, self.right, self.bottom, repr(self.child)
        )

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

    def layout(self, scn, min_width, min_height, max_width, max_height):
        left = scn.value(self.left)
        right = scn.value(self.right)
        top = scn.value(self.top)
        bottom = scn.value(self.bottom)
        child_min_width = scn.value(min_width) - left - right
        child_min_height = scn.value(min_height) - top - bottom
        child_max_width = scn.value(max_width) - left - right
        child_max_height = scn.value(max_height) - top - bottom
        child_width, child_height = self._built_child.layout(
            scn, child_min_width, child_min_height, child_max_width, child_max_height
        )
        return child_width + left + right, child_height + top + bottom

    def render(self, scn, left, top, right, bottom):
        self._built_child.render(
            scn,
            left + scn.value(self.left),
            top + scn.value(self.top),
            right - scn.value(self.right),
            bottom - scn.value(self.bottom),
        )


class PositionOffset(Widget):
    BUILDS_CHILDREN = True

    def __init__(self, child, x=0, y=0):
        self.child = child
        self._built_child = None
        self.x = x
        self.y = y

        super(PositionOffset).__init__()

    def __repr__(self):
        return "PositionOffset(x={}, y={}, child={})".format(self.x, self.y, repr(self.child))

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

    def layout(self, scn, min_width, min_height, max_width, max_height):
        return self._built_child.layout(scn, min_width, min_height, max_width, max_height)

    def render(self, scn, left, top, right, bottom):
        self._built_child.render(scn, left + self.x, top + self.y, right + self.x, bottom + self.y)


class Center(Widget):
    BUILDS_CHILDREN = True

    def __init__(self, child):
        self.child = child
        self._built_child = None
        super(Center, self).__init__()

    def __repr__(self):
        return "Center(child={})".format(repr(self.child))

    def get_flex_x(self, scn: CurrentScene) -> float:
        return 1

    def get_flex_y(self, scn: CurrentScene) -> float:
        return 1

    def build(self) -> Widget:
        self._built_child = self.child.build_recursively()
        return self

    def layout(self, scn, min_width, min_height, max_width, max_height):
        return max_width, max_height

    def render(self, scn, left, top, right, bottom):
        child_width, child_height = self._built_child.layout(
            scn, scn.value(0), scn.value(0), right - left, bottom - top
        )
        child_left = left + (right - left - child_width) // 2
        child_top = top + (bottom - top - child_height) // 2
        self._built_child.render(
            scn,
            child_left,
            child_top,
            child_left + child_width,
            child_top + child_height,
        )


class SizedBox(Widget):
    BUILDS_CHILDREN = True

    def __init__(self, child, width=None, height=None):
        self.child = child
        self._built_child = None
        self.width = width
        self.height = height
        super(SizedBox, self).__init__()

    def __repr__(self):
        return "SizedBox(width={}, height={}, child={})".format(
            self.width, self.height, repr(self.child)
        )

    def get_flex_x(self, scn: CurrentScene) -> float:
        return 1 if self.width is None else 0

    def get_flex_y(self, scn: CurrentScene) -> float:
        return 1 if self.height is None else 0

    def build(self) -> Widget:
        if self.child:
            self._built_child = self.child.build_recursively()
        return self

    def layout(self, scn, min_width, min_height, max_width, max_height):
        width = scn.value(self.width) if self.width is not None else max_width
        height = scn.value(self.height) if self.height is not None else max_height
        return width, height

    def render(self, scn, left, top, right, bottom):
        if self._built_child:
            self._built_child.render(scn, left, top, right, bottom)


class Rectangle(Widget):
    BUILDS_CHILDREN = True

    def __init__(self, color):
        self.color = color
        super(Rectangle, self).__init__()

    def __repr__(self):
        return "Rectangle(color={})".format(repr(self.color))

    def get_flex_x(self, scn: CurrentScene) -> float:
        return 1

    def get_flex_y(self, scn: CurrentScene) -> float:
        return 1

    def build(self) -> Widget:
        return self

    def layout(self, _scn, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, scn: CurrentScene, left, top, right, bottom):
        if isinstance(self.color, int):
            color = scn.hex_color(self.color)
        elif isinstance(self.color, ClientSide):
            color = self.color
        else:
            raise TypeError()

        scn.cmd_draw_rect(
            paint=color,
            rect=scn.rect(
                left_top=(left, top),
                right_bottom=(right, bottom),
            ),
        )


# class Image(Widget):
#     BUILDS_CHILDREN = True
#
#     def __init__(self, uri):
#         self.uri = Expr(uri)
#         super().__init__()
#
#     def __repr__(self):
#         return 'Image(uri={})'.format(repr(self.uri))
#
#     def get_flex_x(self, scn: CurrentScene) -> float:
#         return 1
#
#     def get_flex_y(self, scn: CurrentScene) -> float:
#         return 1
#
#     def build(self) -> Widget:
#         return self
#
#     def layout(self, _min_width, _min_height, max_width, max_height):
#         return max_width, max_height
#
#     def render(self, oplist, left, top, right, bottom):
#         return [
#             Ops.image(
#                 self.uri,
#                 (oplist.append(left), oplist.append(top), oplist.append(right), oplist.append(bottom))
#             )
#         ]
#
#
# class RoundRect(Widget):
#     BUILDS_CHILDREN = True
#
#     def __init__(self, color, radius=10.0):
#         self.color = color
#         self.radius = radius
#         super().__init__()
#
#     def __repr__(self):
#         return 'RoundRect(color={}, radius={})'.format(repr(self.color), self.radius)
#
#     def get_flex_x(self, scn: CurrentScene) -> float:
#         return 1
#
#     def get_flex_y(self, scn: CurrentScene) -> float:
#         return 1
#
#     def build(self) -> Widget:
#         return self
#
#     def layout(self, _min_width, _min_height, max_width, max_height):
#         return max_width, max_height
#
#     def render(self, oplist, left, top, right, bottom):
#         return [
#             Ops.rrect(
#                 (oplist.append(left), oplist.append(top), oplist.append(right), oplist.append(bottom)),
#                 oplist.append(self.color),
#                 oplist.append(self.radius),
#             )
#         ]
#
#


class Text(Widget):
    BUILDS_CHILDREN = True

    def __init__(self, text: ClientVar[str], color: ClientVar[Color]):
        self.text = text
        self.color = color

    def __repr__(self):
        return "Text({}, color={})".format(repr(self.text), repr(self.color))

    def get_flex_x(self, scn: CurrentScene) -> float:
        return 0

    def get_flex_y(self, scn: CurrentScene) -> float:
        return 0

    def build(self) -> Widget:
        return self

    def layout(
        self, scn: CurrentScene, min_width: int, min_height: int, max_width: int, max_height: int
    ):
        return max_width, max_height

    def render(self, scn: CurrentScene, left: int, top: int, right: int, bottom: int):
        if isinstance(self.color, int):
            color = scn.hex_color(self.color)
        elif isinstance(self.color, ClientSide):
            color = self.color
        else:
            raise TypeError("color must be an int or ClientSide[Color]")

        scn.cmd_draw_centered_text(
            text=scn.value(self.text),
            paint=color,
            center=scn.point(
                left=(left + right) // 2,
                top=(top + bottom) // 2,
            ),
        )


# class Text(Widget):
#     BUILDS_CHILDREN = True
#
#     def __init__(self, text, font_size=14, color=0xffffffff):
#         self.text = Expr(text)
#         self.font_size = font_size
#         self.color = color
#         super(Text, self).__init__()
#
#     def __repr__(self):
#         return 'Text({}, font_size={}, color={})'.format(
#             repr(self.text), self.font_size, self.color
#         )
#
#     def get_flex_x(self, scn: CurrentScene) -> float:
#         return 0
#
#     def get_flex_y(self, scn: CurrentScene) -> float:
#         return 0
#
#     def build(self) -> Widget:
#         return self
#
#     def layout(self, min_width, min_height, max_width, max_height):
#         return (
#             Expr.measure_text_x(self.text, self.font_size).min(max_width).max(min_width),
#             Expr.measure_text_y(self.text, self.font_size).min(max_height).max(min_height)
#         )
#
#     def render(self, oplist, left, top, right, bottom):
#         # TODO: Add alignment parameter
#         return [
#             Ops.text(
#                 oplist.append(self.text),
#                 oplist.append((left + right) // 2),
#                 oplist.append((bottom + top) // 2),
#                 oplist.append(self.font_size),
#                 oplist.append(self.color),
#             )
#         ]
#
#
class Flexible(Widget):
    BUILDS_CHILDREN = True

    def __init__(self, child=None, flex_x=1, flex_y=1):
        self.child = child
        self._built_child = None
        self.flex_x = flex_x
        self.flex_y = flex_y
        super(Flexible, self).__init__()

    def __repr__(self):
        return "Flexible(flex_x={}, flex_y={}, child={})".format(
            self.flex_x, self.flex_y, repr(self.child)
        )

    def get_flex_x(self, scn: CurrentScene) -> float:
        return self.flex_x

    def get_flex_y(self, scn: CurrentScene) -> float:
        return self.flex_y

    def build(self) -> Widget:
        if self.child:
            self._built_child = self.child.build_recursively()
        return self

    def layout(self, scn, min_width, min_height, max_width, max_height):
        width = max_width
        height = max_height

        if self._built_child:
            get_layout = lazy(
                lambda: self._built_child.layout(scn, min_width, min_height, max_width, max_height)
            )
            width = scn.if_(self.flex_x == 0, lambda: get_layout()[0], lambda: width)
            height = scn.if_(self.flex_y == 0, lambda: get_layout()[1], lambda: height)

        return width, height

    def render(self, scn, left, top, right, bottom):
        if self._built_child:
            self._built_child.render(scn, left, top, right, bottom)


class EventHandler(Widget):
    BUILDS_CHILDREN = True

    def __init__(
        self,
        child=None,
        on_mouse_down: Optional[Callable[[CurrentHandler], None]] = None,
        on_mouse_up: Optional[Callable[[CurrentHandler], None]] = None,
    ):
        self.child = child
        self.on_mouse_down = on_mouse_down
        self.on_mouse_up = on_mouse_up

        self._built_child = None

    def __repr__(self):
        return "EventHandler(child={}, on_mouse_down={}, on_mouse_up={})".format(
            repr(self.child), repr(self.on_mouse_down), repr(self.on_mouse_up)
        )

    def get_flex_x(self, scn: CurrentScene) -> float:
        return self._built_child.get_flex_x(scn)

    def get_flex_y(self, scn: CurrentScene) -> float:
        return self._built_child.get_flex_y(scn)

    def build(self) -> Widget:
        if self.child:
            self._built_child = self.child.build_recursively()
        return self

    def layout(self, scn, min_width, min_height, max_width, max_height):
        return self._built_child.layout(scn, min_width, min_height, max_width, max_height)

    def render(self, scn, left, top, right, bottom):
        self._built_child.render(scn, left, top, right, bottom)
        rect = lazy(lambda: scn.rect(left_top=(left, top), right_bottom=(right, bottom)).op)
        if self.on_mouse_down:
            scn.add_event_handler(EventType__MouseDown(rect()), self.on_mouse_down)
        if self.on_mouse_up:
            scn.add_event_handler(EventType__MouseUp(rect()), self.on_mouse_up)


# class EventHandler(Widget):
#     BUILDS_CHILDREN = True
#     COUNTER = 1
#
#     def __init__(self, child=None, on_mouse_down=None, on_scroll=None):
#         self.child = child
#         self.on_mouse_down = on_mouse_down
#         self.on_scroll = on_scroll
#
#         assert (self.on_mouse_down is None) != (self.on_scroll is None), \
#             'Either on_mouse_down or on_scroll must be specified'
#
#         self._built_child = None
#         self._id = EventHandler.COUNTER
#         EventHandler.COUNTER += 1
#
#         super(EventHandler, self).__init__()
#
#     @staticmethod
#     def fix_handler(oplist, handler):
#         if isinstance(handler, (Expr, int, float, str)):
#             return oplist.append(Expr.wrap(handler))
#         elif isinstance(handler, dict):
#             result = {}
#             for key, value in handler.items():
#                 # FIXME: Too hardcoded, maybe add abstraction?
#                 if key == 'type' or (handler.get('type', None) == 'setVar' and key == 'name'):
#                     result[key] = value
#                 else:
#                     result[key] = EventHandler.fix_handler(oplist, value)
#             return result
#         elif isinstance(handler, list):
#             return [EventHandler.fix_handler(oplist, value) for value in handler]
#         else:
#             raise ValueError('Invalid handler: {}'.format(handler))
#
#     def __repr__(self):
#         return 'EventHandler(child={})'.format(repr(self.child))
#
#     def get_flex_x(self, scn: CurrentScene) -> float:
#         if self._built_child:
#             return self._built_child.get_flex_x(scn)
#         else:
#             return 1
#
#     def get_flex_y(self, scn: CurrentScene) -> float:
#         if self._built_child:
#             return self._built_child.get_flex_y(scn)
#         else:
#             return 1
#
#     def build(self) -> Widget:
#         if self.on_mouse_down:
#             Context['_reply_handlers'][self._id] = self.on_mouse_down
#         elif self.on_scroll:
#             Context['_reply_handlers'][self._id] = self.on_scroll
#
#         if self.child:
#             self._built_child = self.child.build_recursively()
#         return self
#
#     def layout(self, min_width, min_height, max_width, max_height):
#         if self._built_child:
#             return self._built_child.layout(min_width, min_height, max_width, max_height)
#         else:
#             return max_width, max_height
#
#     def render(self, oplist, left, top, right, bottom):
#         events = 0
#         handlers = None
#         handler_oplist = Oplist()
#
#         if self.on_mouse_down:
#             events |= 1 << 0
#             if isinstance(self.on_mouse_down, list):
#                 handlers = EventHandler.fix_handler(handler_oplist, self.on_mouse_down)
#             else:
#                 handlers = [
#                     Ops.reply(self._id, [
#                         handler_oplist.append(var('event_x')),
#                         handler_oplist.append(var('event_y')),
#                         handler_oplist.append(var('time'))
#                     ])
#                 ]
#
#         if self.on_scroll:
#             events |= 1 << 1
#             if isinstance(self.on_scroll, list):
#                 handlers = EventHandler.fix_handler(handler_oplist, self.on_scroll)
#             else:
#                 handlers = [
#                     Ops.reply(self._id, [
#                         handler_oplist.append(var('event_x')),
#                         handler_oplist.append(var('event_y')),
#                         handler_oplist.append(var('scroll_x')),
#                         handler_oplist.append(var('scroll_y')),
#                         handler_oplist.append(var('time'))
#                     ])
#                 ]
#
#         event_hnd_op = Ops.event_handler(
#             (oplist.append(left), oplist.append(top), oplist.append(right), oplist.append(bottom)),
#             events,
#             handlers,
#             handler_oplist.to_list(),
#         )
#         if self._built_child:
#             return [
#                 event_hnd_op,
#                 *self._built_child.render(oplist, left, top, right, bottom),
#             ]
#         else:
#             return [event_hnd_op]
#
#
# class WatchVar(Widget):
#     BUILDS_CHILDREN = True
#     ACK_ID_COUNTER = 1
#
#     def __init__(self, cond: Expr, data: List[Expr], handler=None, wait_for_roundtrip=True, wait_for_rebuild=False, child=None):
#         self.cond = cond
#         self.data = data
#         self.handler = handler
#         self.wait_for_roundtrip = wait_for_roundtrip
#         self.wait_for_rebuild = wait_for_rebuild
#         self.child = child
#
#         self._built_child = None
#         self._hnd_id = EventHandler.COUNTER
#         EventHandler.COUNTER += 1
#
#         self._ack_id = WatchVar.ACK_ID_COUNTER
#         WatchVar.ACK_ID_COUNTER += 1
#
#         super(WatchVar, self).__init__()
#
#     def __repr__(self):
#         return 'WatchVar(cond={}, data={}, handler={}, wait_for_roundtrip={}, child={})'.format(
#             repr(self.cond), repr(self.data), repr(self.handler), repr(self.wait_for_roundtrip), repr(self.child)
#         )
#
#     def get_flex_x(self, scn: CurrentScene) -> float:
#         if self._built_child:
#             return self._built_child.get_flex_x(scn)
#         else:
#             return 1
#
#     def get_flex_y(self, scn: CurrentScene) -> float:
#         if self._built_child:
#             return self._built_child.get_flex_y(scn)
#         else:
#             return 1
#
#     def build(self) -> Widget:
#         if self.handler and not isinstance(self.handler, list):
#             def handler(value):
#                 Context['_app']
#                 self.handler(value)
#                 if self.wait_for_roundtrip and not self.wait_for_rebuild:
#                     Context['_app'].server.send_watch_ack(self._ack_id)
#             Context['_reply_handlers'][self._hnd_id] = handler
#
#         if self.child:
#             self._built_child = self.child.build_recursively()
#         return self
#
#     def layout(self, min_width, min_height, max_width, max_height):
#         if self._built_child:
#             return self._built_child.layout(min_width, min_height, max_width, max_height)
#         else:
#             return max_width, max_height
#
#     def render(self, oplist, left, top, right, bottom):
#         handlers = None
#
#         if self.handler:
#             if isinstance(self.handler, list):
#                 handlers = self.handler
#             else:
#                 handlers = [
#                     Ops.reply(self._hnd_id, [oplist.append(d) for d in self.data])
#                 ]
#
#         watch_op = Ops.watch_var(self._ack_id, oplist.append(self.cond), self.wait_for_roundtrip, handlers)
#         if self._built_child:
#             return [
#                 watch_op,
#                 *self._built_child.render(oplist, left, top, right, bottom),
#             ]
#         else:
#             return [watch_op]


class Clear(Widget):
    BUILDS_CHILDREN = True

    def __init__(self, child, color):
        self.child = child
        self._built_child = None
        self.color = color
        super(Clear, self).__init__()

    def __repr__(self):
        return "Clear(color={}, child={})".format(repr(self.color), repr(self.child))

    def get_flex_x(self, scn: CurrentScene) -> float:
        return 1

    def get_flex_y(self, scn: CurrentScene) -> float:
        return 1

    def build(self) -> Widget:
        self._built_child = self.child.build_recursively()
        return self

    def layout(self, scn, min_width, min_height, max_width, max_height):
        if self._built_child:
            return self._built_child.layout(scn, min_width, min_height, max_width, max_height)

    def render(self, scn, left, top, right, bottom):
        scn.cmd_clear(scn.hex_color(self.color))
        self._built_child.render(scn, left, top, right, bottom)


# class Clip(Widget):
#     BUILDS_CHILDREN = True
#
#     def __init__(self, child):
#         self.child = child
#         self._built_child = None
#         super().__init__()
#
#     def __repr__(self):
#         return 'Clip(child={})'.format(repr(self.child))
#
#     def get_flex_x(self, scn: CurrentScene) -> float:
#         return self._built_child.get_flex_x(scn)
#
#     def get_flex_y(self, scn: CurrentScene) -> float:
#         return self._built_child.get_flex_y(scn)
#
#     def build(self) -> Widget:
#         self._built_child = self.child.build_recursively()
#         return self
#
#     def layout(self, min_width, min_height, max_width, max_height):
#         return self._built_child.layout(min_width, min_height, max_width, max_height)
#
#     def render(self, oplist, left, top, right, bottom):
#         return [
#             Ops.save(),
#             Ops.clip_rect((oplist.append(left), oplist.append(top), oplist.append(right), oplist.append(bottom))),
#             *self._built_child.render(oplist, left, top, right, bottom),
#             Ops.restore(),
#         ]


class Stack(Widget):
    BUILDS_CHILDREN = True

    def __init__(self, children, align="center", fit: Literal["expand", "tight"] = "expand"):
        self.children = children
        self.align = align
        self.fit = fit
        self._built_children = []
        super(Stack, self).__init__()

    def __repr__(self):
        return "Stack(align={}, fit={}, children={})".format(
            self.align, self.fit, repr(self.children)
        )

    def get_flex_x(self, scn: CurrentScene) -> float:
        if self.fit == "expand":
            total_flex = sum(
                (child.get_flex_x(scn) for child in self._built_children), scn.value(0)
            )
            return 1 if total_flex else 0
        elif self.fit == "tight":
            return 0
        else:
            assert False

    def get_flex_y(self, scn: CurrentScene) -> float:
        if self.fit == "expand":
            total_flex = sum(
                (child.get_flex_y(scn) for child in self._built_children), scn.value(0)
            )
            return 1 if total_flex else 0
        elif self.fit == "tight":
            return 0
        else:
            assert False

    def build(self) -> Widget:
        self._built_children = []
        for child in self.children:
            self._built_children.append(child.build_recursively())
        return self

    def layout(self, scn, min_width, min_height, max_width, max_height):
        children_flex_x = [child.get_flex_x(scn) for child in self._built_children]
        children_flex_y = [child.get_flex_y(scn) for child in self._built_children]
        total_flex_x = sum(children_flex_x, scn.value(0))
        total_flex_y = sum(children_flex_y, scn.value(0))

        if self.fit == "expand":
            width = max_width
            height = max_height
        elif self.fit == "tight":
            width = scn.value(0)
            height = scn.value(0)
        else:
            assert False

        children_sizes = [[scn.value(0), scn.value(0)] for _ in self._built_children]
        # One of the axis are not flexible, need to calculate actual size
        if total_flex_x == 0 or total_flex_y == 0 or self.fit == "tight":
            for i, (child, child_flex_x, child_flex_y) in enumerate(
                zip(self._built_children, children_flex_x, children_flex_y)
            ):
                if child_flex_x == 0 or child_flex_y == 0:
                    children_sizes[i] = list(
                        child.layout(
                            scn,
                            scn.value(0),
                            scn.value(0),
                            max_width,
                            max_height,
                        )
                    )

            if children_sizes and (total_flex_x == 0 or self.fit == "tight"):
                width = children_sizes[0][0]
                for child_size in children_sizes:
                    width = width.max(child_size[0])
            elif not children_sizes:
                width = scn.value(0)

            if children_sizes and (total_flex_y == 0 or self.fit == "tight"):
                height = children_sizes[0][1]
                for child_size in children_sizes:
                    height = height.max(child_size[1])
            elif not children_sizes:
                height = scn.value(0)
        else:
            for i, child in enumerate(self._built_children):
                children_sizes[i] = list(child.layout(scn, min_width, min_height, width, height))

        return width, height

    def render(self, scn, left, top, right, bottom):
        children_flex_x = [child.get_flex_x(scn) for child in self._built_children]
        children_flex_y = [child.get_flex_y(scn) for child in self._built_children]
        children_sizes = [[scn.value(0), scn.value(0)] for _ in self._built_children]

        for i, (child, child_flex_x, child_flex_y) in enumerate(
            zip(self._built_children, children_flex_x, children_flex_y)
        ):
            if child_flex_x == 0 or child_flex_y == 0:
                children_sizes[i] = list(
                    child.layout(
                        scn,
                        scn.value(0),
                        scn.value(0),
                        right - left,
                        bottom - top,
                    )
                )

        for i, child_flex_y in enumerate(children_flex_y):
            if child_flex_y > 0:
                children_sizes[i][1] = bottom - top

        for i, child_flex_x in enumerate(children_flex_x):
            if child_flex_x > 0:
                children_sizes[i][0] = right - left

        for i, (child, child_size) in enumerate(zip(self._built_children, children_sizes)):
            if self.align == "center":
                child_left = (right + left - child_size[0]) // 2
                child_top = (bottom + top - child_size[1]) // 2
                child_right = (right + left + child_size[0]) // 2
                child_bottom = (bottom + top + child_size[1]) // 2
                child.render(scn, child_left, child_top, child_right, child_bottom)
            elif self.align == "topleft":
                child.render(scn, left, top, left + child_size[0], top + child_size[1])


# class ListViewInner(Widget):
#     BUILDS_CHILDREN = True
#
#     class State(BaseModel):
#         item_offset: int
#         item_count: int
#         gen: int
#         list_start: float
#         scroll_pos: float
#
#     def __init__(self, state: State, builder, offset, height_slack=128):
#         self.state = state
#         self.builder = builder
#         self.offset = Expr(offset)
#         self.height_slack = height_slack
#         self._built_children = {}
#         self._laid_out_children = {}
#         self._watch_var_top = None
#         self._watch_var = None
#         self._item_offset = None
#         self._item_count = None
#         self._gen = None
#
#         self._above_top_widget_height = None
#         self._top_widget_height = None
#         self._bot_widget_height = None
#         self._total_height = None
#         super().__init__()
#
#     def __repr__(self):
#         return 'ListViewInner(builder={}, offset={})'.format(self.builder, self.offset)
#
#     def get_flex_x(self, scn: CurrentScene) -> float:
#         return 1
#
#     def get_flex_y(self, scn: CurrentScene) -> float:
#         return 1
#
#     def build(self) -> Widget:
#         self._item_offset = self.state.item_offset
#         self._item_count = self.state.item_count
#         self._gen = self.state.gen
#
#         self._built_children = {}
#         for i in range(max(self._item_offset - 1, 0), self._item_offset + self._item_count):
#             self._built_children[i] = self.builder(i).build_recursively()
#
#         self._laid_out_children = {}
#         y = self.offset
#         self._above_top_widget_height = None
#         self._top_widget_height = None
#         self._bot_widget_height = None
#         for i in range(max(self._item_offset - 1, 0), self._item_offset + self._item_count):
#             height = self._built_children[i].layout(Expr(0), Expr(0), Expr(float('inf')), Expr(float('inf')))[1]
#             if i == self._item_offset - 1:
#                 self._above_top_widget_height = height
#             else:
#                 if i == self._item_offset:
#                     self._top_widget_height = height
#                 if i == self._item_offset + self._item_count - 1:
#                     self._bot_widget_height = height
#
#                 self._laid_out_children[i] = (y, y + height)
#                 y += height
#         self._total_height = y - self.offset
#
#         print(f'--------------------- top_widget_height={self._top_widget_height} above_top_widget_height={self._above_top_widget_height} bot_widget_height={self._bot_widget_height} gen={self._gen}')
#
#         self.state.gen += 1
#
#         return self
#
#     def layout(self, _min_width, _min_height, max_width, max_height):
#         max_height = max_height.max(0)
#
#         def update_bottom_widget(data):
#             from boldui.app import update_widget
#
#             total_height, above_top_widget_height, top_widget_height, bot_widget_height, max_height_val, list_start, scroll_pos, gen = data
#             print(f'list_start={list_start} scroll_pos={scroll_pos} gen={gen}')
#             if gen != self._gen:
#                 return
#
#             update = False
#             if scroll_pos - list_start > top_widget_height + self.height_slack:
#                 # Delete top widget
#                 print('scroll down', top_widget_height, 'px')
#                 Context['_app'].server.set_remote_var(self.state.key_of('list_start'), 'n', list_start + top_widget_height)
#                 self.state.item_offset += 1
#                 update = True
#             elif scroll_pos - list_start < self.height_slack and list_start > 0:
#                 # Add top widget
#                 print('scroll up', above_top_widget_height, 'px')
#                 Context['_app'].server.set_remote_var(self.state.key_of('list_start'), 'n', list_start - above_top_widget_height)
#                 self.state.item_offset -= 1
#                 update = True
#
#             if total_height - (scroll_pos - list_start) - self.height_slack - bot_widget_height > max_height_val:
#                 # Delete bottom widget
#                 print('delete bot widget')
#                 self.state.item_count -= 1
#                 update = True
#             elif total_height - (scroll_pos - list_start) - self.height_slack < max_height_val:
#                 # Add bottom widget
#                 print('add bot widget')
#                 self.state.item_count += 1
#                 update = True
#
#             # if update:
#             #     update_widget()
#
#         # TODO: Add/Remove multiple widgets at a time
#         print(f'============= {max_height}')
#         self._watch_var = WatchVar(
#             cond=Expr(
#                 (
#                     # Delete top widget
#                         (self.state.bind('scroll_pos') - self.state.bind('list_start')) > (Expr(self._top_widget_height or 0) + self.height_slack)
#                 ) | (
#                     # Add top widget
#                         ((self.state.bind('scroll_pos') - self.state.bind('list_start')) < self.height_slack)
#                         & (self.state.bind('list_start') > 0)
#                 ) | (
#                     # Delete bottom widget
#                         (self._total_height - (self.state.bind('scroll_pos') - self.state.bind('list_start')) - self.height_slack - (self._bot_widget_height or 0)) > max_height
#                 ) | (
#                     # Add bottom widget
#                         (self._total_height - (self.state.bind('scroll_pos') - self.state.bind('list_start')) - self.height_slack) < max_height
#                 )
#             ),
#             data=[
#                 self._total_height or 0,
#                 self._above_top_widget_height or 0,
#                 self._top_widget_height or 0,
#                 self._bot_widget_height or 0,
#                 max_height or 0,
#                 self.state.bind('list_start'), self.state.bind('scroll_pos'),
#                 self._gen
#             ],
#             handler=update_bottom_widget,
#             wait_for_roundtrip=True,
#             wait_for_rebuild=True,
#         ).build_recursively()
#
#         return max_width, max_height
#
#     def render(self, oplist, left, top, right, bottom):
#         result = []
#
#         for i in range(self._item_offset, self._item_offset + self._item_count):
#             child_top, child_bottom = self._laid_out_children[i]
#             result += self._built_children[i].render(oplist, left, top + child_top, right, top + child_bottom)
#
#         result += self._watch_var.render(oplist, left, top, right, bottom)
#
#         return result
#
#
# class ListView(Widget):
#     State = ListViewInner.State
#
#     def __init__(self, state, builder, clip=True):
#         self.state = state
#         self.builder = builder
#         self.clip = clip
#         super().__init__()
#
#     def build(self):
#         inner = ListViewInner(
#             state=self.state,
#             builder=self.builder,
#             offset=self.state.bind('list_start') - self.state.bind('scroll_pos'),
#         )
#         if self.clip:
#             inner = Clip(inner)
#
#         return EventHandler(
#             inner,
#             on_scroll=[
#                 Ops.set_var(
#                     self.state.key_of('scroll_pos'),
#                     (self.state.bind('scroll_pos') - var('scroll_y') * 10).max(0)
#                 ),
#             ],
#         )


class DBGHighlight(Widget):
    def __init__(self, child, color=0xFF0000):
        self.child = child
        self.color = color
        super().__init__()

    def __repr__(self):
        return f"DBGHighlight(color={hex(self.color)}, child={self.child})"

    def build(self) -> Widget:
        return Stack(
            [
                Rectangle(self.color),
                self.child,
            ],
            fit="tight",
        )


# class Button(Widget):
#     def __init__(self, child, on_mouse_down=None):
#         self.child = child
#         self.on_mouse_down = on_mouse_down
#         super().__init__()
#
#     def __repr__(self):
#         return f'Button(child={self.child})'
#
#     def build(self) -> Widget:
#         return EventHandler(
#             on_mouse_down=self.on_mouse_down,
#             child=Stack([
#                 RoundRect(color=0xff3a3a3a, radius=5.0),
#                 Padding(self.child, vertical=11, horizontal=18),
#             ], fit='tight'),
#         )
#
#
# class TextButton(Widget):
#     def __init__(self, text, on_mouse_down=None):
#         self.text = Expr(text)
#         self.on_mouse_down = on_mouse_down
#         super().__init__()
#
#     def __repr__(self):
#         return f'TextButton(text={repr(self.text)})'
#
#     def build(self) -> Widget:
#         return Button(
#             child=Text(text=self.text, font_size=15, color=0xffffffff),
#             on_mouse_down=self.on_mouse_down,
#         )
#
#
# def lerp(a, b, t):
#     return a + (b - a) * t
#
#
# class AnimatedValue(BaseModel):
#     target_value: float
#     last_value: float
#     animation_start: float
#     animation_duration: float
#
#     def set_remotely(self, value, duration):
#         return [
#             Ops.set_var(self.key_of('last_value'), self.bind('target_value')),
#             Ops.set_var(self.key_of('target_value'), value),
#             Ops.set_var(self.key_of('animation_start'), var('time')),
#             Ops.set_var(self.key_of('animation_duration'), duration),
#         ]
#
#     def get(self):
#         progress = ((var('time') - self.key_of('animation_start')) / self.key_of('duration')).min(1.0).max(0.0)
#         return progress * self.key_of('target_value') + ((1.0 - progress) * self.key_of('last_value'))
#
#
# class Switch(Widget):
#     class State(BaseModel):
#         is_active: int
#         animation_start: float
#         # position: AnimatedValue
#
#     def __init__(self, state: State):
#         self.state = state
#         super().__init__()
#
#     def __repr__(self):
#         return 'Switch()'
#
#     def get_flex_x(self, scn: CurrentScene) -> float:
#         return 0
#
#     def get_flex_y(self, scn: CurrentScene) -> float:
#         return 0
#
#     def build(self) -> Widget:
#         animation_progress = ((var('time') - self.state.bind('animation_start')) / 0.1).min(1.0).max(0.0)
#         # animation_progress = self.state.position.get()
#
#         if self.state.is_active:
#             track_color = 0xff3584e4
#             thumb_color = 0xffffffff
#             offset = lerp(Expr(-11.0), Expr(11.0), animation_progress)
#         else:
#             track_color = 0xff545454
#             thumb_color = 0xffd2d2d2
#             offset = lerp(Expr(11.0), Expr(-11.0), animation_progress)
#
#         return EventHandler(
#             SizedBox(
#                 width=48,
#                 height=26,
#                 child=Stack([
#                     RoundRect(
#                         color=track_color,
#                         radius=13.0,
#                     ),
#                     PositionOffset(
#                         SizedBox(
#                             Padding(
#                                 RoundRect(
#                                     color=thumb_color,
#                                     radius=13.0,
#                                 ),
#                                 all=2,
#                             ),
#                             width=26,
#                             height=26,
#                         ),
#
#                         x=offset,
#                     )
#                 ])
#             ),
#             on_mouse_down=self._on_mouse_down,
#         )
#
#     def _on_mouse_down(self, event):
#         _, _, press_time = event
#         self.state.animation_start = press_time
#         self.state.is_active = 0 if self.state.is_active else 1


def lazy(func: Callable[[], T]) -> Callable[[], T]:
    val = None

    def get():
        nonlocal val
        if val is None:
            val = func()
        return val

    return get
