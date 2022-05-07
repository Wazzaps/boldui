from simplexp import var

from boldui import Expr
from boldui.framework import Widget, RoundRect, EventHandler, Stack, Text, Padding, SizedBox, PositionOffset, Row
from boldui.store import BaseModel


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


def lerp(a, b, t):
    return a + (b - a) * t


class Switch(Widget):
    class State(BaseModel):
        is_active: int
        animation_start: float

    def __init__(self, state: State):
        self.state = state
        super().__init__()

    def __repr__(self):
        return 'Switch()'

    def get_flex_x(self) -> float:
        return 0

    def get_flex_y(self) -> float:
        return 0

    def build(self) -> Widget:
        animation_progress = ((var('time') - self.state.bind.animation_start) / 0.1).min(1.0).max(0.0)
        if self.state.is_active:
            track_color = 0xff3584e4
            thumb_color = 0xffffffff
            offset = lerp(Expr(-11.0), Expr(11.0), animation_progress)
        else:
            track_color = 0xff545454
            thumb_color = 0xffd2d2d2
            offset = lerp(Expr(11.0), Expr(-11.0), animation_progress)

        return EventHandler(
            SizedBox(
                width=48,
                height=26,
                child=Stack([
                    RoundRect(
                        color=track_color,
                        radius=13.0,
                    ),
                    PositionOffset(
                        SizedBox(
                            Padding(
                                RoundRect(
                                    color=thumb_color,
                                    radius=13.0,
                                ),
                                all=2,
                            ),
                            width=26,
                            height=26,
                        ),

                        x=offset,
                    )
                ])
            ),
            on_mouse_down=self._on_mouse_down,
        )

    def _on_mouse_down(self, event):
        _, _, press_time = event
        self.state.animation_start = press_time
        self.state.is_active = 0 if self.state.is_active else 1
