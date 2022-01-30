from boldui import Expr
from boldui.framework import Widget, RoundRect, EventHandler, Stack, Text, Padding


class Button(Widget):
    def __init__(self, child, on_mouse_down=None):
        self.child = child
        self.on_mouse_down = on_mouse_down
        super().__init__()

    def __repr__(self):
        return f'Button(child={self.child})'

    def build(self) -> Widget:
        return EventHandler(
            on_mouse_down=self.on_mouse_down,
            child=Stack([
                RoundRect(color=0xff3a3a3a, radius=5.0),
                Padding(self.child, vertical=11, horizontal=18),
            ], fit='tight'),
        )


class TextButton(Widget):
    def __init__(self, text, on_mouse_down=None):
        self.text = Expr(text)
        self.on_mouse_down = on_mouse_down
        super().__init__()

    def __repr__(self):
        return f'TextButton(text={repr(self.text)})'

    def build(self) -> Widget:
        return Button(
            child=Text(text=self.text, font_size=15, color=0xffffffff),
            on_mouse_down=self.on_mouse_down,
        )
