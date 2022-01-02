#!/usr/bin/env python3
import abc
from typing import Tuple, Dict

from boldui import Ops, Expr, ProtocolServer, stringify_op


class Widget:
    def layout(self, min_width: Expr, min_height: Expr, max_width: Expr, max_height: Expr) -> Tuple[Expr, Expr]:
        raise RuntimeError('This widget shouldn\'t be rendered directly')

    def render(self, left: Expr, top: Expr, right: Expr, bottom: Expr) -> Dict:
        raise RuntimeError('This widget shouldn\'t be rendered directly')

    @abc.abstractmethod
    def build(self):
        pass

    def get_flex_x(self) -> float:
        return 0

    def get_flex_y(self) -> float:
        return 0


class Row(Widget):
    def __init__(self, children, align='center'):
        self.children = children
        self.align = align
        self._built_children = []

    def __repr__(self):
        return 'Row(children={})'.format(repr(self.children))

    def get_flex_x(self) -> float:
        total_flex = sum(child.get_flex_x() for child in self._built_children)
        return 1 if total_flex else 0

    def get_flex_y(self) -> float:
        total_flex = sum(child.get_flex_y() for child in self._built_children)
        return 1 if total_flex else 0

    def build(self) -> Widget:
        for child in self.children:
            self._built_children.append(child.build())
        return self

    def layout(self, min_width, min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        result = []
        free_space = right - left

        children_flex_x = [child.get_flex_x() for child in self._built_children]
        children_flex_y = [child.get_flex_y() for child in self._built_children]
        children_sizes = [[Expr(0), Expr(0)] for _ in self._built_children]
        total_flex = sum(children_flex_x)

        for i, (child, child_flex_x, child_flex_y) in enumerate(zip(self._built_children, children_flex_x, children_flex_y)):
            if child_flex_x == 0 or child_flex_y == 0:
                children_sizes[i] = list(child.layout(0, bottom - top, float('inf'), bottom - top))
                if child_flex_x == 0:
                    free_space -= children_sizes[i][0]

        per_flex_unit_size = abs(free_space) // total_flex
        for i, child_flex_x in enumerate(children_flex_x):
            if child_flex_x > 0:
                children_sizes[i][0] = per_flex_unit_size * child_flex_x

        for i, child_flex_y in enumerate(children_flex_y):
            if child_flex_y > 0:
                children_sizes[i][1] = bottom - top

        current_left_coord = left
        for i, (child, child_size) in enumerate(zip(self._built_children, children_sizes)):
            if self.align == 'center':
                item_top = top + (bottom - child_size[1]) // 2
                item_bottom = top + (bottom + child_size[1]) // 2
            elif self.align == 'top':
                item_top = top
                item_bottom = top + child_size[1]
            else:
                raise RuntimeError('Unknown alignment: {}'.format(self.align))
            result += child.render(current_left_coord, item_top, current_left_coord + child_size[0], item_bottom)
            current_left_coord += child_size[0]

        return result


class Column(Widget):
    def __init__(self, children, align='center'):
        self.children = children
        self.align = align
        self._built_children = []

    def __repr__(self):
        return 'Column(children={})'.format(repr(self.children))

    def get_flex_x(self) -> float:
        total_flex = sum(child.get_flex_x() for child in self._built_children)
        return 1 if total_flex else 0

    def get_flex_y(self) -> float:
        total_flex = sum(child.get_flex_y() for child in self._built_children)
        return 1 if total_flex else 0

    def build(self) -> Widget:
        for child in self.children:
            self._built_children.append(child.build())
        return self

    def layout(self, min_width, min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        result = []
        free_space = bottom - top

        children_flex_x = [child.get_flex_x() for child in self._built_children]
        children_flex_y = [child.get_flex_y() for child in self._built_children]
        children_sizes = [[Expr(0), Expr(0)] for _ in self._built_children]
        total_flex = sum(children_flex_y)

        for i, (child, child_flex_x, child_flex_y) in enumerate(zip(self._built_children, children_flex_x, children_flex_y)):
            if child_flex_x == 0 or child_flex_y == 0:
                children_sizes[i] = list(child.layout(right - left, 0, right - left, float('inf')))
                if child_flex_y == 0:
                    free_space -= children_sizes[i][1]

        per_flex_unit_size = abs(free_space) // total_flex
        for i, child_flex_y in enumerate(children_flex_y):
            if child_flex_y > 0:
                children_sizes[i][1] = per_flex_unit_size * child_flex_y

        for i, child_flex_x in enumerate(children_flex_x):
            if child_flex_x > 0:
                children_sizes[i][0] = right - left

        current_top_coord = top
        for i, (child, child_size) in enumerate(zip(self._built_children, children_sizes)):
            if self.align == 'center':
                item_left = left + (right - child_size[0]) // 2
                item_right = left + (right + child_size[0]) // 2
            elif self.align == 'top':
                item_left = left
                item_right = left + child_size[0]
            else:
                raise RuntimeError('Unknown alignment: {}'.format(self.align))
            result += child.render(item_left, current_top_coord, item_right, current_top_coord + child_size[1])
            current_top_coord += child_size[1]

        return result


class Padding(Widget):
    def __init__(self, child, left=0, top=0, right=0, bottom=0, horizontal=None, vertical=None, all=None):
        self.child = child
        self._built_child = None

        if all is not None:
            self.left = Expr(all)
            self.top = Expr(all)
            self.right = Expr(all)
            self.bottom = Expr(all)
        else:
            self.left = Expr(left)
            self.top = Expr(top)
            self.right = Expr(right)
            self.bottom = Expr(bottom)
        if horizontal is not None:
            self.left = Expr(horizontal)
            self.right = Expr(horizontal)
        if vertical is not None:
            self.top = Expr(vertical)
            self.bottom = Expr(vertical)

    def __repr__(self):
        return 'Padding(left={}, top={}, right={}, bottom={}, child={})'.format(
            self.left, self.top, self.right, self.bottom, repr(self.child)
        )

    def get_flex_x(self) -> float:
        return self.child.get_flex_x()

    def get_flex_y(self) -> float:
        return self.child.get_flex_y()

    def build(self) -> Widget:
        self._built_child = self.child.build()
        return self

    def layout(self, min_width, min_height, max_width, max_height):
        child_min_width = Expr(min_width) - self.left - self.right
        child_min_height = Expr(min_height) - self.top - self.bottom
        child_max_width = Expr(max_width) - self.left - self.right
        child_max_height = Expr(max_height) - self.top - self.bottom
        child_width, child_height = self._built_child.layout(child_min_width, child_min_height,
                                                      child_max_width, child_max_height)
        return child_width + self.left + self.right, child_height + self.top + self.bottom

    def render(self, left, top, right, bottom):
        return self._built_child.render(left + self.left, top + self.top, right - self.right, bottom - self.bottom)


class Center(Widget):
    def __init__(self, child):
        self.child = child
        self._built_child = None

    def __repr__(self):
        return 'Center(child={})'.format(repr(self.child))

    def get_flex_x(self) -> float:
        return 1

    def get_flex_y(self) -> float:
        return 1

    def build(self) -> Widget:
        self._built_child = self.child.build()
        return self

    def layout(self, min_width, min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        child_width, child_height = self._built_child.layout(0, 0, right - left, bottom - top)
        child_left = left + (right - left - child_width) // 2
        child_top = top + (bottom - top - child_height) // 2
        return self._built_child.render(child_left, child_top, child_left + child_width, child_top + child_height)


class SizedBox(Widget):
    def __init__(self, child, width=None, height=None):
        self.child = child
        self._built_child = None
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

    def build(self) -> Widget:
        self._built_child = self.child.build()
        return self

    def layout(self, min_width, min_height, max_width, max_height):
        width = self.width if self.width is not None else max_width
        height = self.height if self.height is not None else max_height
        return width, height

    def render(self, left, top, right, bottom):
        return self._built_child.render(left, top, right, bottom)


class Rectangle(Widget):
    def __init__(self, color):
        self.color = color

    def __repr__(self):
        return 'Rectangle(color={})'.format(repr(self.color))

    def get_flex_x(self) -> float:
        return 1

    def get_flex_y(self) -> float:
        return 1

    def build(self) -> Widget:
        return self

    def layout(self, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        return [Ops.rect((left, top, right, bottom), self.color)]


class Text(Widget):
    def __init__(self, text, font_size=14, color=0xffffffff):
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

    def build(self) -> Widget:
        return self

    def layout(self, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        return [Ops.text(self.text, (left + right) // 2, (bottom + top) // 2, self.font_size, self.color)]


class Flexible(Widget):
    def __init__(self, child=None, flex_x=1, flex_y=1):
        self.child = child
        self._built_child = None
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

    def build(self) -> Widget:
        if self.child:
            self._built_child = self.child.build()
        return self

    def layout(self, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        if self._built_child:
            return self._built_child.render(left, top, right, bottom)
        else:
            return []


class Clear(Widget):
    def __init__(self, child, color):
        self.child = child
        self._built_child = None
        self.color = color

    def __repr__(self):
        return 'Clear(color={}, child={})'.format(repr(self.color), repr(self.child))

    def get_flex_x(self) -> float:
        return 1

    def get_flex_y(self) -> float:
        return 1

    def build(self) -> Widget:
        self._built_child = self.child.build()
        return self

    def layout(self, _min_width, _min_height, max_width, max_height):
        return max_width, max_height

    def render(self, left, top, right, bottom):
        return [
            Ops.clear(self.color),
            *self._built_child.render(left, top, right, bottom)
        ]
