#!/usr/bin/env python3
import abc
from typing import Tuple, Dict

from boldui import Ops, Expr, ProtocolServer, stringify_op


class Widget:
    @abc.abstractmethod
    def layout(self, min_width: Expr, min_height: Expr, max_width: Expr, max_height: Expr) -> Tuple[Expr, Expr]:
        pass

    @abc.abstractmethod
    def render(self, left: Expr, top: Expr, right: Expr, bottom: Expr) -> Dict:
        pass

    def get_flex_x(self) -> float:
        return 0

    def get_flex_y(self) -> float:
        return 0


class HBox(Widget):
    def __init__(self, children):
        self.children = children

    def __repr__(self):
        return 'HBox(children={})'.format(repr(self.children))

    def get_flex_x(self) -> float:
        return 0

    def get_flex_y(self) -> float:
        return 0

    def layout(self, min_width, min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        result = []
        free_space = right - left

        children_flex = [child.get_flex_x() for child in self.children]
        children_sizes = [0 for _ in self.children]
        total_flex = sum(children_flex)

        for i, (child, child_flex) in enumerate(zip(self.children, children_flex)):
            if child_flex == 0:
                children_sizes[i] = child.layout(0, top - bottom, float('inf'), top - bottom)[0]
                free_space -= children_sizes[i]

        per_flex_unit_size = abs(free_space) // total_flex
        for i, child_flex in enumerate(children_flex):
            if child_flex > 0:
                children_sizes[i] = per_flex_unit_size * child_flex

        current_left_coord = left
        for i, (child, child_size) in enumerate(zip(self.children, children_sizes)):
            result += child.render(current_left_coord, top, current_left_coord + child_size, bottom)
            current_left_coord += children_sizes[i]

        return result


class Padding(Widget):
    def __init__(self, child, left=0, top=0, right=0, bottom=0):
        self.child = child
        self.left = Expr(left)
        self.top = Expr(top)
        self.right = Expr(right)
        self.bottom = Expr(bottom)

    def __repr__(self):
        return 'Padding(left={}, top={}, right={}, bottom={}, child={})'.format(
            self.left, self.top, self.right, self.bottom, repr(self.child)
        )

    def get_flex_x(self) -> float:
        return self.child.get_flex_x()

    def get_flex_y(self) -> float:
        return self.child.get_flex_y()

    def layout(self, min_width, min_height, max_width, max_height):
        child_min_width = Expr(min_width) - self.left - self.right
        child_min_height = Expr(min_height) - self.top - self.bottom
        child_max_width = Expr(max_width) - self.left - self.right
        child_max_height = Expr(max_height) - self.top - self.bottom
        child_width, child_height = self.child.layout(child_min_width, child_min_height,
                                                      child_max_width, child_max_height)
        return child_width + self.left + self.right, child_height + self.top + self.bottom

    def render(self, left, top, right, bottom):
        return self.child.render(left + self.left, top + self.top, right - self.right, bottom - self.bottom)


class Center(Widget):
    def __init__(self, child):
        self.child = child

    def __repr__(self):
        return 'Center(child={})'.format(repr(self.child))

    def get_flex_x(self) -> float:
        return 1

    def get_flex_y(self) -> float:
        return 1

    def layout(self, min_width, min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        child_width, child_height = self.child.layout(0, 0, right - left, bottom - top)
        child_left = left + (right - left - child_width) // 2
        child_top = top + (bottom - top - child_height) // 2
        return self.child.render(child_left, child_top, child_left + child_width, child_top + child_height)


class SizedBox(Widget):
    def __init__(self, child, width=None, height=None):
        self.child = child
        self.width = Expr(width) if width is not None else None
        self.height = Expr(height) if height is not None else None

    def __repr__(self):
        return 'SizedBox(width={}, height={}, child={})'.format(
            self.width, self.height, repr(self.child)
        )

    def get_flex_x(self) -> float:
        return 1 if self.width is None else 0

    def get_flex_y(self) -> float:
        return 1 if self.height is None else 0


    def layout(self, min_width, min_height, max_width, max_height):
        width = self.width if self.width is not None else max_width
        height = self.height if self.height is not None else max_height
        return width, height

    def render(self, left, top, right, bottom):
        return self.child.render(left, top, right, bottom)


class Rectangle(Widget):
    def __init__(self, color):
        self.color = color

    def __repr__(self):
        return 'Rectangle(color={})'.format(repr(self.color))

    def get_flex_x(self) -> float:
        return 1

    def get_flex_y(self) -> float:
        return 1

    def layout(self, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        return [Ops.rect((left, top, right, bottom), self.color)]


class Text(Widget):
    def __init__(self, text, font_size, color):
        self.text = text
        self.font_size = font_size
        self.color = color

    def __repr__(self):
        return 'Text({}, font_size={}, color={})'.format(
            repr(self.text), self.font_size, self.color
        )

    def get_flex_x(self) -> float:
        return 1

    def get_flex_y(self) -> float:
        return 1

    def layout(self, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        return [Ops.text(self.text, (left + right) // 2, (bottom + top) // 2, self.font_size, self.color)]


class Flexible(Widget):
    def __init__(self, child, flex_x=1, flex_y=1):
        self.child = child
        self.flex_x = flex_x
        self.flex_y = flex_y

    def __repr__(self):
        return 'Flexible(flex_x={}, flex_y={}, child={})'.format(
            self.flex_x, self.flex_y, repr(self.child)
        )

    def get_flex_x(self) -> float:
        return self.flex_x

    def get_flex_y(self) -> float:
        return self.flex_y

    def layout(self, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        return self.child.render(left, top, right, bottom)


class Clear(Widget):
    def __init__(self, child, color):
        self.child = child
        self.color = color

    def __repr__(self):
        return 'Clear(color={}, child={})'.format(repr(self.color), repr(self.child))

    def get_flex_x(self) -> float:
        return 1

    def get_flex_y(self) -> float:
        return 1

    def layout(self, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        return [
            Ops.clear(self.color),
            *self.child.render(left, top, right, bottom)
        ]


def main():
    root = Clear(
        color=0xff202030,
        child=HBox([
            Padding(
                Text(
                    'Hello, World!',
                    font_size=18,
                    color=0xffa0a0a0,
                ),
                left=10, top=10, right=10, bottom=10,
            ),
            Padding(
                Center(
                    SizedBox(
                        Rectangle(0xffa0a0a0),
                        width=abs((Expr.var('time') % 1) - 0.5) * 50 + 100,
                        height=abs(((Expr.var('time') + 0.5) % 1) - 0.5) * 50 + 100,
                    ),
                ),
                left=10, top=10, right=10, bottom=10,
            ),
            Padding(
                Rectangle(
                    color=Expr(Ops.if_(Expr.var('height') > 600, 0xffa0a0a0, 0xff9090d0))
                ),
                left=10, top=10, right=10, bottom=10
            ),
            Flexible(
                Padding(
                    Rectangle(
                        color=Expr(Ops.if_(Expr.var('width') > 800, 0xffa0a0a0, 0xffd09090))
                    ),
                    left=10, top=10, right=10, bottom=10
                ),
                flex_x=3,
            ),
        ]),
    )

    # root = Clear(
    #     color=0xff202030,
    #     child=HBox([
    #         Padding(
    #             SizedBox(
    #                 Rectangle(0xffa0a0a0),
    #                 width=100,
    #             ),
    #             left=10, top=10, right=10, bottom=10,
    #         ),
    #         Flexible(
    #             Padding(
    #                 Rectangle(0xffa0a0a0),
    #                 left=10, top=10, right=10, bottom=10
    #             ),
    #             flex_x=3,
    #         ),
    #         Padding(
    #             Rectangle(0xffa0a0a0),
    #             left=10, top=10, right=10, bottom=10
    #         ),
    #     ]),
    # )

    # root = Clear(
    #     color=0xff202030,
    #     child=Padding(
    #         child=Rectangle(0xffa0a0a0),
    #         left=10, top=10, right=10, bottom=10
    #     ),
    # )

    # root = Clear(
    #     color=0xff202030,
    #     child=Text(
    #         'Hello, World!',
    #         font_size=32,
    #         color=0xffa0a0a0,
    #     ),
    # )

    size = root.layout(Expr(0), Expr(0), Expr.var('width'), Expr.var('height'))
    scene = root.render(Expr(0), Expr(0), size[0], size[1])
    for op in scene:
        print(stringify_op(op))
    server = ProtocolServer("/tmp/boldui.hello_world.sock", scene)
    server.serve()


if __name__ == '__main__':
    main()
