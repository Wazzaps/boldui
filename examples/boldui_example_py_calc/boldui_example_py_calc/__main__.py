import boldui
import dataclasses
import sys
from functools import partial
from typing import Dict
from boldui_protocol import Value__String
from boldui import OpWrapper

eprint = partial(print, file=sys.stderr)


def print():
    raise NotImplementedError("Use eprint() instead of print(), since stdout is used for BoldUI protocol")


app = boldui.BoldUIApplication()


@dataclasses.dataclass
class CalculatorState:
    a: float = 123.0
    b: float = 0.0
    curr_op: str = "\0"
    should_show_b: bool = False


@app.view("/")
def calc_view(state: CalculatorState, _query_params: Dict[str, str]):
    s = boldui.get_current_scene()

    s.cmd_clear(s.hex_color(0x242424))

    # Results box
    results_width = s.var(":width")
    results_height = 65.0
    results_rect = s.rect(
        left_top=(0.0, 1.0),
        right_bottom=(results_width, results_height),
    )
    s.cmd_draw_rect(paint=s.hex_color(0x363636), rect=results_rect)

    # Results text
    s.decl_var("result_bar", Value__String(str(state.b if state.should_show_b else state.a)))
    s.cmd_draw_centered_text(
        text=s.var("result_bar"),
        paint=s.hex_color(0xFFFFFF),
        center=s.point(results_width / 2.0, results_height / 2.0),
    )

    # Buttons
    action_button_color = s.hex_color(0x3A3A3A)
    action_button_disabled_color = s.hex_color(0x2A2A2A)
    number_button_color = s.hex_color(0x505050)
    equals_button_color = s.hex_color(0xE66100)
    button_text_color = s.hex_color(0xFFFFFF)
    button_text_disabled_color = s.hex_color(0x808080)

    def make_btn(color: OpWrapper, x: int, y: int, height: int, text: str, text_color: OpWrapper):
        TOP_PADDING = 79.0
        LEFT_PADDING = 12.0
        X_PADDING = 4.0
        Y_PADDING = 4.0
        BTN_WIDTH = 59.0
        BTN_HEIGHT = 44.0

        rect = s.rect(
            left_top=(
                LEFT_PADDING + x * (X_PADDING + BTN_WIDTH),
                TOP_PADDING + y * (Y_PADDING + BTN_HEIGHT),
            ),
            right_bottom=(
                LEFT_PADDING + x * (X_PADDING + BTN_WIDTH) + BTN_WIDTH,
                TOP_PADDING + (y + height - 1) * (Y_PADDING + BTN_HEIGHT) + BTN_HEIGHT,
            ),
        )
        s.cmd_draw_rect(paint=color, rect=rect)

        text_pos = s.point(
            left=LEFT_PADDING + x * (X_PADDING + BTN_WIDTH) + BTN_WIDTH / 2.0,
            top=TOP_PADDING + y * (Y_PADDING + BTN_HEIGHT) + (BTN_HEIGHT * height) / 2.0,
        )
        s.cmd_draw_centered_text(text=s.value(text), paint=text_color, center=text_pos)

        # TODO: Event handler

    def make_disabled_action_btn(x: int, y: int, text: str):
        make_btn(action_button_disabled_color, x, y, 1, text, button_text_disabled_color)

    def make_action_btn(x: int, y: int, text: str):
        make_btn(action_button_color, x, y, 1, text, button_text_color)

    def make_number_btn(x: int, y: int, text: str):
        make_btn(number_button_color, x, y, 1, text, button_text_color)

    def make_equals_btn(x: int, y: int, text: str):
        make_btn(equals_button_color, x, y, 2, text, button_text_color)

    make_action_btn(0, 0, "⌫")
    make_disabled_action_btn(1, 0, "(")
    make_disabled_action_btn(2, 0, ")")
    make_action_btn(3, 0, "mod")
    make_action_btn(4, 0, "π")
    make_number_btn(0, 1, "7")
    make_number_btn(1, 1, "8")
    make_number_btn(2, 1, "9")
    make_action_btn(3, 1, "÷")
    make_action_btn(4, 1, "sqrt")
    make_number_btn(0, 2, "4")
    make_number_btn(1, 2, "5")
    make_number_btn(2, 2, "6")
    make_action_btn(3, 2, "×")
    make_action_btn(4, 2, "x²")
    make_number_btn(0, 3, "1")
    make_number_btn(1, 3, "2")
    make_number_btn(2, 3, "3")
    make_action_btn(3, 3, "-")
    make_equals_btn(4, 3, "=")
    make_number_btn(0, 4, "0")
    make_action_btn(1, 4, ".")
    make_action_btn(2, 4, "%")
    make_action_btn(3, 4, "+")

    s.create_window(title="Calculator", initial_size=(334, 327))


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
#         return Stack([
#             # Background
#             Rectangle(color=0xff242424),
#
#             # Counter
#             Center(
#                 Row([
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
#                 ]),
#             ),
#         ])
