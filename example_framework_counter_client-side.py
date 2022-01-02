#!/usr/bin/env python3

from boldui import Ops, Expr
from boldui.app import App
from boldui.framework import Row, Rectangle, SizedBox, Text, Center, Stack, EventHandler, Widget


class MainPage(Widget):
    def build(self):
        return Stack([
            # Background
            Rectangle(color=0xff222222),

            # Counter
            Center(
                Row([
                    SizedBox(
                        width=80, height=80,
                        child=EventHandler(
                            on_mouse_down=[Ops.set_var('counter', Expr.var('counter') - 1)],
                            child=Stack([
                                Rectangle(color=0xff555555),
                                Text(text='-', font_size=24),
                            ]),
                        ),
                    ),
                    SizedBox(
                        width=130, height=80,
                        child=Text(text=Expr.var('counter').to_str(), font_size=24)
                    ),
                    SizedBox(
                        width=80, height=80,
                        child=EventHandler(
                            on_mouse_down=[Ops.set_var('counter', Expr.var('counter') + 1)],
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
