#!/usr/bin/env python3

from boldui import Ops, Expr
from boldui.adwaita import Button
from boldui.app import App
from boldui.framework import Row, Rectangle, SizedBox, Text, Center, Stack, Widget


class MainPage(Widget):
    def build(self):
        return Stack([
            # Background
            Rectangle(color=0xff242424),

            # Counter
            Center(
                Row([
                    SizedBox(
                        width=80, height=80,
                        child=Button(
                            Text(text='-', font_size=24),
                            on_mouse_down=[Ops.set_var('counter', var('counter') - 1)],
                        ),
                    ),
                    SizedBox(
                        width=130, height=80,
                        child=Text(text=var('counter').to_str(), font_size=24)
                    ),
                    SizedBox(
                        width=80, height=80,
                        child=Button(
                            Text(text='+', font_size=24),
                            on_mouse_down=[Ops.set_var('counter', var('counter') + 1)],
                        ),
                    ),
                ]),
            ),
        ])


if __name__ == '__main__':
    app = App(MainPage)
    app.run()
