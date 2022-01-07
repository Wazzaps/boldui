#!/usr/bin/env python3
from boldui import Ops, Expr
from boldui.app import App, update_widget
from boldui.framework import Rectangle, SizedBox, Text, Stack, EventHandler, Widget, Column, PositionOffset
from boldui.store import BaseModel


class Model(BaseModel):
    scroll_pos: int


class ListView(Widget):
    def build(self):
        return EventHandler(
            PositionOffset(
                Column([
                    SizedBox(
                        Text(text=f"{i}", color=0xffffffff, font_size=24),
                        height=32
                    )
                    for i in range(20)
                ]),
                y=Expr.var('lv_scroll_pos')
            ),
            on_scroll=[
                Ops.set_var(
                    'lv_scroll_pos',
                    (Expr.var('lv_scroll_pos') + Expr.var('scroll_y') * 10).min(0)
                )
            ],
        )


class MainPage(Widget):
    def build(self):
        return Stack([
            # Background
            Rectangle(color=0xff222222),

            # List
            ListView(),
        ])


if __name__ == '__main__':
    app = App(MainPage, durable_store='/run/user/1000/example_app.db', durable_model=Model)
    app.run()