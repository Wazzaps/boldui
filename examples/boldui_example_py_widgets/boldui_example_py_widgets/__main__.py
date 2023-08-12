import boldui
import dataclasses
from typing import Dict, List
from boldui.scene_mgmt import ClientVar, Model

from boldui.widgets import (
    Rectangle,
    # Column,
    Row,
    Flexible,
)
from boldui_protocol import *

# noinspection PyUnresolvedReferences


@dataclasses.dataclass
class WidgetsState(Model):
    offset: ClientVar[int] = 3


app = boldui.BoldUIApplication(WidgetsState)


@app.reply_handler("/")
def reply_handler(_state: WidgetsState, _query_params: Dict[str, str], _value_params: List[Value]):
    pass


@app.view("/")
def view(state: WidgetsState, _query_params: Dict[str, str]):
    s = boldui.get_current_scene()

    width = s.var(f":width_{s.scene.id}")
    height = s.var(f":height_{s.scene.id}")
    # widget = Padding(
    #     Rectangle(color=0xAA5555),
    #     all=30,
    # )
    # widget = Clear(
    #     Center(
    #         PositionOffset(
    #             SizedBox(
    #                 Row(
    #                     Rectangle(color=0xAA5555),
    #                     Rectangle(color=0x55AA55),
    #                     Rectangle(color=0x5555AA),
    #                 ),
    #                 width=200,
    #                 height=100,
    #             ),
    #             y=100,
    #         )
    #     ),
    #     color=0x242424,
    # )

    # try:
    #     time.sleep(10000000)
    # except KeyboardInterrupt:
    #     pass
    flex = abs(s.time().sin()) / 100 + 0.0001
    widget = Row(
        Rectangle(color=0xAA5555),
        *(
            Flexible(Rectangle(color=0x00AA00 + (i * 0x10000 + i * 0x1)), flex_x=flex)
            for i in range(3000)
        ),
        # Flexible(Rectangle(color=0x55AA55), flex_x=state.offset),
        # Flexible(Rectangle(color=0x55AA55), flex_x=abs(s.time().sin())),
        Rectangle(color=0x5555AA),
    )
    # widget = Stack(
    #     Rectangle(color=0xAA5555),
    #     SizedBox(
    #         Rectangle(color=0x55AA55),
    #         width=100,
    #         height=100,
    #     ),
    #     PositionOffset(
    #         SizedBox(
    #             Rectangle(color=0x5555AA),
    #             width=50,
    #             height=50,
    #         ),
    #         x=50,
    #         y=50,
    #     ),
    # )
    # widget = DBGHighlight(SizedBox(child=Rectangle(s.color(0, 0, 0, 0)), width=100, height=100))

    built = widget.build_recursively()
    built_width, built_height = built.layout(s, width, height, width, height)
    built.render(s, s.value(0), s.value(0), built_width, built_height)

    # s.cmd_clear(s.hex_color(0x242424))

    s.create_window(title="Widgets demo", initial_size=(600, 600))


if __name__ == "__main__":
    app.setup_logging()
    app.main_loop()


# TODO: Future API?
# class Counter(Widget):
#     def __init__(self):
#         self.counter = 0
#         super(Counter, self).__init__()
#
#     def build(self):
#         def dec(_):
#             self.counter -= 1
#             update_widget()
#
#         def inc(_):
#             self.counter += 1
#             update_widget()
#
#         return Stack(
#             # Background
#             Rectangle(color=0xff242424),
#
#             # Counter
#             Center(
#                 Row(
#                     SizedBox(
#                         width=41, height=41,
#                         child=Button(
#                             Text(text='-', font_size=18),
#                             on_mouse_down=dec,
#                         ),
#                     ),
#                     SizedBox(
#                         width=60, height=41,
#                         child=Text(text=str(self.counter), font_size=18)
#                     ),
#                     SizedBox(
#                         width=41, height=41,
#                         child=Button(
#                             Text(text='+', font_size=18),
#                             on_mouse_down=inc,
#                         ),
#                     ),
#                 ),
#             ),
#         )
