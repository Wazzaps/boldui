#!/usr/bin/env python3
from boldui.adwaita import Button
from boldui.app import App, update_widget
from boldui.framework import Row, Rectangle, SizedBox, Text, Center, Stack, Widget


class MainPage(Widget):
    def __init__(self):
        self.counter = 0
        super(MainPage, self).__init__()

    def build(self):
        def dec(_):
            self.counter -= 1
            update_widget()

        def inc(_):
            self.counter += 1
            update_widget()

        return Stack([
            # Background
            Rectangle(color=0xff242424),

            # Counter
            Center(
                Row([
                    SizedBox(
                        width=41, height=41,
                        child=Button(
                            Text(text='-', font_size=18),
                            on_mouse_down=dec,
                        ),
                    ),
                    SizedBox(
                        width=60, height=41,
                        child=Text(text=str(self.counter), font_size=18)
                    ),
                    SizedBox(
                        width=41, height=41,
                        child=Button(
                            Text(text='+', font_size=18),
                            on_mouse_down=inc,
                        ),
                    ),
                ]),
            ),
        ])


if __name__ == '__main__':
    app = App(MainPage)
    app.run()
