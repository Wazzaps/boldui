import logging
import re

import math

import boldui
import dataclasses
from typing import Dict, List
from boldui_protocol import *
from boldui import OpWrapper, st

# noinspection PyUnresolvedReferences
from boldui import eprint, print

app = boldui.BoldUIApplication()


@dataclasses.dataclass
class CalculatorState:
    expr: str = ""
    scene_id: int = -1


@app.reply_handler("/")
def calc_reply_handler(state: CalculatorState, _query_params: Dict[str, str], value_params: List[Value]):
    [pressed_btn] = value_params
    assert isinstance(pressed_btn, Value__String)
    pressed_btn = pressed_btn.value

    assert state.scene_id != -1

    match pressed_btn:
        case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "+" | "-" | "×" | "÷" | "." | "√" | "%" | "π" | "(" | ")":
            state.expr += pressed_btn
        case "mod":
            state.expr += " mod "
        case "x²":
            state.expr += "²"
        case "=":
            state.expr = calculate(state.expr)
            if state.expr.endswith(".0"):
                state.expr = state.expr[:-2]
        case "⌫":
            state.expr = ""
        case btn:
            raise RuntimeError(f"Unknown button: {btn}")

    s = boldui.get_current_scene()
    update = A2RUpdate(
        updated_scenes=[],
        run_blocks=[
            HandlerBlock(
                ops=[OpsOperation__Value(value=Value__String(state.expr))],
                cmds=[
                    HandlerCmd__UpdateVar(
                        var=VarId(key="expr_bar", scene=st.uint32(state.scene_id)),
                        value=OpId(scene_id=st.uint32(0), idx=st.uint32(0)),
                    )
                ],
            ),
        ],
        external_app_requests=[],
    )

    s.app.send_update(update)


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
    s.decl_var("expr_bar", Value__String(str(state.expr)))
    s.cmd_draw_centered_text(
        text=s.var("expr_bar"),
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

        text_val = s.value(text)
        text_pos = s.point(
            left=LEFT_PADDING + x * (X_PADDING + BTN_WIDTH) + BTN_WIDTH / 2.0,
            top=TOP_PADDING + y * (Y_PADDING + BTN_HEIGHT) + (BTN_HEIGHT * height) / 2.0,
        )
        s.cmd_draw_centered_text(text=text_val, paint=text_color, center=text_pos)

        s.scene.event_handlers.append(
            (
                EventType__Click(rect=rect.op),
                HandlerBlock(
                    ops=[],
                    cmds=[HandlerCmd__Reply(f"/?session={s.session_id}", [text_val.op])],
                ),
            )
        )

    def make_disabled_action_btn(x: int, y: int, text: str):
        make_btn(action_button_disabled_color, x, y, 1, text, button_text_disabled_color)

    def make_action_btn(x: int, y: int, text: str):
        make_btn(action_button_color, x, y, 1, text, button_text_color)

    def make_number_btn(x: int, y: int, text: str):
        make_btn(number_button_color, x, y, 1, text, button_text_color)

    def make_equals_btn(x: int, y: int, text: str):
        make_btn(equals_button_color, x, y, 2, text, button_text_color)

    make_action_btn(0, 0, "⌫")
    make_action_btn(1, 0, "(")
    make_action_btn(2, 0, ")")
    make_action_btn(3, 0, "mod")
    make_action_btn(4, 0, "π")
    make_number_btn(0, 1, "7")
    make_number_btn(1, 1, "8")
    make_number_btn(2, 1, "9")
    make_action_btn(3, 1, "÷")
    make_action_btn(4, 1, "√")
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

    state.scene_id = s.scene.id
    s.create_window(title="Calculator", initial_size=(334, 327))


def calculate(expr: str) -> str:
    if expr.count("(") != expr.count(")"):
        return "Error"

    expr = expr.strip().replace("π", str(math.pi))

    while "(" in expr:
        # Evaluate inner parentheses
        expr = re.sub(r"\(([^()]*)\)", lambda match: " " + calculate(match.group(1)) + " ", expr)

    # modulo
    a, op, b = expr.rpartition(" mod ")
    if op == " mod ":
        a = float(calculate(a))
        b = float(calculate(b))
        expr = str(float(a) % float(b))

    # division & multiplication
    if "÷" in expr or "×" in expr:
        res = 0.0
        for expr_part in re.finditer("([÷×]?)([^÷×]+)", expr):
            if expr_part.group(1) == "":
                res = float(calculate(expr_part.group(2)))
            elif expr_part.group(1) == "÷":
                res /= float(calculate(expr_part.group(2)))
            elif expr_part.group(1) == "×":
                res *= float(calculate(expr_part.group(2)))
            else:
                assert False
        expr = str(res)

    # addition & subtraction
    if "+" in expr or "-" in expr:
        res = 0.0
        for expr_part in re.finditer("([+-]?)([^+-]+)", expr):
            if expr_part.group(1) == "":
                res = float(calculate(expr_part.group(2)))
            elif expr_part.group(1) == "+":
                res += float(calculate(expr_part.group(2)))
            elif expr_part.group(1) == "-":
                res -= float(calculate(expr_part.group(2)))
            else:
                assert False
        expr = str(res)

    if percent_match := re.match(r"([0-9]*(\.[0-9]*)?) *%", expr.strip()):
        expr = str(float(percent_match.group(1)) / 100)

    if squared_match := re.match(r"([0-9]*(\.[0-9]*)?) *²", expr.strip()):
        expr = str(float(squared_match.group(1)) ** 2)

    if sqrt_match := re.match(r"√ *([0-9]*(\.[0-9]*)?)", expr.strip()):
        expr = str(float(sqrt_match.group(1)) ** 0.5)

    return expr.strip()


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
