#!/usr/bin/env python3

from boldui.app import App
from boldui.framework import Row, Rectangle, SizedBox, Text, Center, Stack, EventHandler, Widget
from boldui.store import BaseModel


class Model(BaseModel):
    counter: int


class MainPage(Widget):
    def build(self):
        def dec():
            Model.counter -= 1

        def inc():
            Model.counter += 1

        return Stack([
            # Background
            Rectangle(color=0xff222222),

            # Counter
            Center(
                Row([
                    SizedBox(
                        width=80, height=80,
                        child=EventHandler(
                            on_mouse_down=lambda _: dec(),
                            child=Stack([
                                Rectangle(color=0xff555555),
                                Text(text='-', font_size=24),
                            ]),
                        ),
                    ),
                    SizedBox(
                        width=130, height=80,
                        child=Text(text=Model.bind.counter.to_str(), font_size=24)
                    ),
                    SizedBox(
                        width=80, height=80,
                        child=EventHandler(
                            on_mouse_down=lambda _: inc(),
                            child=Stack([
                                Rectangle(color=0xff555555),
                                Text(text='+', font_size=24),
                            ]),
                        ),
                    ),
                ]),
            ),
        ])


if __name__ == '__main__':
    app = App(MainPage, durable_store='/home/david/.local/example_app.db', durable_model=Model)
    app.run()
