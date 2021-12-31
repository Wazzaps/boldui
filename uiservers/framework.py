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


class HBox(Widget):
    def __init__(self, children):
        self.children = children

    def __repr__(self):
        return 'HBox(children={})'.format(repr(self.children))

    def layout(self, min_width, min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        result = []
        space_per_child = (right - left) // len(self.children)
        current_left = left
        for child in self.children:
            result += child.render(current_left, top, space_per_child + current_left, bottom)
            current_left += space_per_child
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

    def layout(self, min_width, min_height, max_width, max_height):
        child_min_width = min_width - self.left - self.right
        child_min_height = min_height - self.top - self.bottom
        child_max_width = max_width - self.left - self.right
        child_max_height = max_height - self.top - self.bottom
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

    def layout(self, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        return [Ops.rect((left, top, right, bottom), self.color)]


class Clear(Widget):
    def __init__(self, child, color):
        self.child = child
        self.color = color

    def __repr__(self):
        return 'Clear(color={}, child={})'.format(repr(self.color), repr(self.child))

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
                    color=Expr(Ops.if_(Expr.var('width') > 600, 0xffa0a0a0, 0xffd09090))
                ),
                left=10, top=10, right=10, bottom=10
            ),
            Padding(
                Rectangle(
                    color=Expr(Ops.if_(Expr.var('height') > 600, 0xffa0a0a0, 0xff9090d0))
                ),
                left=10, top=10, right=10, bottom=10
            ),
        ]),
    )
    # root = Clear(
    #     color=0xff202030,
    #     child=Padding(
    #         child=Rectangle(0xffa0a0a0),
    #         left=10, top=10, right=10, bottom=10
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
