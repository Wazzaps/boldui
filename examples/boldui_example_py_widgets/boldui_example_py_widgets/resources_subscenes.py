import dataclasses

from boldui import get_current_scene, BoldUIApplication
from boldui.scene_mgmt import (
    Model,
    field,
    CurrentHandler,
    ClientSide,
    SceneIdAlloc,
    CurrentScene,
)
from boldui.widgets import (
    Padding,
    Text,
    Row,
    Flexible,
    AnimatedValue,
    Button,
    EventHandler,
)
from boldui_protocol import (
    SceneAttr__Transform,
    SceneAttr__Size,
)
from serde_types import uint32


# ------ App ------


@dataclasses.dataclass
class BouncingSmiley(Model):
    count: int = 0
    bounce: AnimatedValue = field(lambda: AnimatedValue(0.0))
    img_pos: AnimatedValue = field(init=False)
    subscene_id: SceneIdAlloc = field(SceneIdAlloc)

    def __post_init__(self):
        self.img_pos = AnimatedValue(float(self.count))
        super().__post_init__()

    def cs_forward(self, h: CurrentHandler, ss_path: str):
        self.bounce.set(1.0, 0.3, from_value=0.0)
        self.img_pos.set(self.count + 1, 0.3, from_value=self.count)
        h.reply(ss_path)

    def ss_forward(self):
        self.count += 1

    def cs_backward(self, h: CurrentHandler, ss_path: str):
        self.bounce.set(1.0, 0.3, from_value=0.0)
        self.img_pos.set(self.count - 1, 0.3, from_value=self.count)
        h.reply(ss_path)

    def ss_backward(self):
        self.count -= 1

    def view(self):
        s = get_current_scene()

        def _inner(s2: CurrentScene):
            s2.cmd_draw_image(0, ClientSide.point(0, 0))

        sub_scene = s.sub_scene(self.subscene_id, _inner)
        sub_scene.set_attr(
            SceneAttr__Transform,
            ClientSide.point(
                self.img_pos.value * 40,
                abs((self.bounce.value * 3.1419).sin()) * -60 + 130,
            ),
        )
        # Set scene size
        sub_scene.set_attr(SceneAttr__Size, ClientSide.point(64, 64))


@dataclasses.dataclass
class State(Model):
    bouncing_smiley: BouncingSmiley = field(BouncingSmiley)
    dec_btn: Button.State = field(Button.State)
    inc_btn: Button.State = field(Button.State)


app = BoldUIApplication(State)


@app.reply_handler("dec")
def dec(state: State):
    state.bouncing_smiley.ss_backward()


@app.reply_handler("inc")
def inc(state: State):
    state.bouncing_smiley.ss_forward()


@app.view("/")
def main_view(state: State):
    s = get_current_scene()

    widget = Padding(
        Row(
            Button(
                "-",
                on_mouse_down=lambda h: state.bouncing_smiley.cs_backward(h, "dec") or s.value(0),
                state=state.dec_btn,
            ),
            EventHandler(
                Flexible(Text(text=str(state.bouncing_smiley.count), color=0xFFFFFF), flex_x=1),
                on_mouse_down=lambda h: h.open("count"),
            ),
            Button(
                "+",
                on_mouse_down=lambda h: state.bouncing_smiley.cs_forward(h, "inc") or s.value(0),
                state=state.inc_btn,
            ),
        ),
        all=30,
    )

    width = s.var(f":width_{s.scene.id}")
    height = s.var(f":height_{s.scene.id}")
    built = widget.build_recursively()
    built_width, built_height = built.layout(s, width, height, width, height)
    built.render(s, s.value(0), s.value(0), built_width, built_height)

    state.bouncing_smiley.view()

    s.create_window(
        title="Widgets demo 2",
        initial_size=(600, 600),
        resources={uint32(0): open("developer_art.png", "rb").read()},
    )


@app.view("/count")
def count_view(state: State):
    s = get_current_scene()

    widget = Padding(
        Text(text=str(state.bouncing_smiley.count), color=0xFFFFFF),
        all=30,
    )

    width = s.var(f":width_{s.scene.id}")
    height = s.var(f":height_{s.scene.id}")
    built = widget.build_recursively()
    built_width, built_height = built.layout(s, width, height, width, height)
    built.render(s, s.value(0), s.value(0), built_width, built_height)

    s.create_window(title="Widgets demo 2 - count", initial_size=(60, 60))


def main():
    app.setup_logging()
    app.database("./app.db")
    app.main_loop()


if __name__ == "__main__":
    main()
