#!/usr/bin/env python3

from boldui.app import App, update_widget
from boldui.framework import Row, Rectangle, SizedBox, Text, Center, Stack, EventHandler, Widget


class MainPage(Widget):
    def __init__(self):
        self.counter = 0
        super(MainPage, self).__init__()

    def build(self):
        def dec():
            self.counter -= 1
            update_widget()

        def inc():
            self.counter += 1
            update_widget()

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
                        child=Text(text=str(self.counter), font_size=24)
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
    app = App(MainPage, durable_store='/home/david/.local/example_app.db')
    app.run()
