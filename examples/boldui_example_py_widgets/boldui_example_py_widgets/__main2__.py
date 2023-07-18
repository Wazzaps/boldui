import dataclasses
from typing import ClassVar, Callable

from boldui import get_current_scene, BoldUIApplication, eprint, print
from boldui.scene_mgmt import (
    ClientVar,
    Model,
    field,
    CurrentScene,
    get_current_handler,
    CurrentHandler,
)
from boldui.widgets import (
    Widget,
    Stack,
    Rectangle,
    Padding,
    Text,
    EventHandler,
    Row,
    DBGHighlight,
    SizedBox,
    Flexible,
)

# ------ Base Widgets ------


@dataclasses.dataclass
class AnimatedValue(Model):
    a: ClientVar[float]
    b: ClientVar[float]
    start_time: ClientVar[float] = 0.0
    duration_sec: ClientVar[float] = 0.0

    def __init__(self, initial_value: float):
        self.a = initial_value
        self.b = initial_value
        super().__init__()

    @property
    def value(self):
        scn = get_current_scene()
        lerp = (
            (scn.time((self.start_time, self.start_time + self.duration_sec)) - self.start_time)
            / self.duration_sec
        ).min(1.0)
        return self.a * (-lerp + 1) + self.b * lerp

    def set(self, new_value: ClientVar[float], duration_sec: ClientVar[float]):
        ctx = get_current_handler()
        ctx.update_var(self.a, self.value)
        ctx.update_var(self.b, ctx.value(new_value))
        ctx.update_var(self.duration_sec, ctx.value(duration_sec))
        ctx.update_var(self.start_time, ctx.time())


class Button(Widget):
    DEFAULT_BRIGHTNESS: ClassVar = 0.5
    PRESSED_BRIGHTNESS: ClassVar = 0.3
    ANIMATION_DURATION_SEC: ClassVar = 0.1

    @dataclasses.dataclass
    class State(Model):
        brightness: AnimatedValue = field(lambda: AnimatedValue(Button.DEFAULT_BRIGHTNESS))

        @property
        def bgcolor(self):
            scn = get_current_scene()
            brightness = self.brightness.value
            return scn.color(brightness, brightness, brightness, 1.0)

    def __init__(self, text, on_mouse_down: Callable[[CurrentHandler], None], state: State):
        self.text = text
        self.on_mouse_down = on_mouse_down
        self.state = state

    def build(self):
        return EventHandler(
            Stack(
                [
                    Rectangle(color=self.state.bgcolor),
                    Padding(
                        SizedBox(
                            Text(text=self.text, color=0xFFFFFF),
                            width=100,
                            height=100,
                        ),
                        all=10,
                    ),
                ],
                fit="tight",
            ),
            on_mouse_down=self._on_mouse_down,
            on_mouse_up=self._on_mouse_up,
        )

    def _on_mouse_down(self, scn):
        self.on_mouse_down(scn)
        self.state.brightness.set(
            new_value=Button.PRESSED_BRIGHTNESS,
            duration_sec=Button.ANIMATION_DURATION_SEC,
        )

    def _on_mouse_up(self, _scn):
        self.state.brightness.set(
            new_value=Button.DEFAULT_BRIGHTNESS,
            duration_sec=Button.ANIMATION_DURATION_SEC,
        )


# ------ App ------


@dataclasses.dataclass
class State(Model):
    count: int = 0
    dec_btn: Button.State = field(Button.State)
    inc_btn: Button.State = field(Button.State)


app = BoldUIApplication(State)


@app.reply_handler("dec")
def dec(state: State):
    state.count -= 1


@app.reply_handler("inc")
def inc(state: State):
    state.count += 1


@app.view("/")
def main_view(state: State):
    widget = Padding(
        Row(
            [
                Button(
                    "-",
                    on_mouse_down=lambda h: h.reply("dec"),
                    state=state.dec_btn,
                ),
                Flexible(Text(text=str(state.count), color=0xFFFFFF), flex_x=1),
                Button(
                    "+",
                    on_mouse_down=lambda h: h.reply("inc"),
                    state=state.inc_btn,
                ),
            ]
        ),
        all=30,
    )

    s = get_current_scene()
    width = s.var(":width")
    height = s.var(":height")
    built = widget.build_recursively()
    built_width, built_height = built.layout(s, width, height, width, height)
    built.render(s, s.value(0), s.value(0), built_width, built_height)
    s.create_window(title="Widgets demo", initial_size=(600, 600))


def main():
    app.setup_logging()
    app.database("./app.db")
    app.main_loop()


if __name__ == "__main__":
    main()
