#!/usr/bin/env python3
from boldui.adwaita import TextButton, Switch
from boldui.app import App, stateful_widget
from boldui.framework import Row, SizedBox, Rectangle, Clear, Column, Padding, Stack, RoundRect, Text
from boldui.store import BaseModel

FG = 0xffcccccc
FGBG = 0xff3a3a3a
BG = 0xff242424


class Model(BaseModel):
    font_size: int = 24
    bold_switch: Switch.State
    italic_switch: Switch.State

    def add_font_size(self, delta):
        self.font_size += delta


@stateful_widget
def main_page(model):
    text = 'Hello, world!'

    if model.bold_switch.is_active:
        text = f'<b>{text}</b>'
    if model.italic_switch.is_active:
        text = f'<i>{text}</i>'

    return Clear(
        color=BG,
        child=Padding(
            all=12,
            child=Column([
                Row([
                    # Font size
                    Column([
                        Text("Font size", color=FG, font_size=16),
                        Padding(
                            vertical=12,
                            child=Row([
                                TextButton('-', on_mouse_down=lambda _: model.add_font_size(-1)),
                                Padding(
                                    horizontal=18,
                                    child=Text(model.bind('font_size').to_str(), color=FG, font_size=18)
                                ),
                                TextButton('+', on_mouse_down=lambda _: model.add_font_size(1)),
                            ]),
                        ),
                    ]),

                    SizedBox(Rectangle(0), width=36, height=0),  # TODO: Empty SizedBox

                    # Bold
                    Column([
                        Text("Bold?", color=FG, font_size=16),
                        Padding(
                            vertical=12,
                            child=Switch(
                                state=model.bold_switch,
                            ),
                        ),
                    ]),

                    SizedBox(Rectangle(0), width=36, height=0),  # TODO: Empty SizedBox

                    # Italic
                    Column([
                        Text("Italics?", color=FG, font_size=16),
                        Padding(
                            vertical=12,
                            child=Switch(
                                state=model.italic_switch,
                            ),
                        ),
                    ]),
                ]),

                # Text area
                Stack([
                    RoundRect(color=FGBG, radius=8),
                    Padding(
                        all=8,
                        child=Stack([
                            # Border
                            Rectangle(0xffff0000),
                            Padding(all=1, child=Rectangle(FGBG)),

                            # Text
                            Text(
                                text=text,
                                font_size=model.bind('font_size'),
                                color=FG,
                            ),
                        ], fit='tight'),
                    )
                ]),
            ]),
        )
    )


if __name__ == '__main__':
    app_model = Model.open_db('/run/user/1000/example_app.db')
    app = App(lambda: main_page(app_model), durable_model=app_model)
    app.run()
