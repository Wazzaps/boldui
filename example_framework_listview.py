#!/usr/bin/env python3
from boldui import Ops, Expr
from boldui.app import App
from boldui.framework import Rectangle, SizedBox, Text, Stack, Widget, Padding, \
    Flexible, Row, ListView
from boldui.store import BaseModel


class Model(BaseModel):
    list_state: ListView.State


class MainPage(Widget):
    def build(self):
        return Stack([
            # Background
            Rectangle(color=0xff222222),

            # List
            Padding(
                Stack([
                    Rectangle(color=0xff202090),
                    ListView(
                        state=Model.list_state,
                        builder=lambda i: SizedBox(
                            Row([
                                Flexible(),
                                Stack([
                                    Rectangle(color=0x80ff0000 if (i % 2 == 0) else 0x8000ff00),
                                    Text(text=f"{i}", color=0xffffffff, font_size=24),
                                ]),
                                Flexible(),
                            ]),
                            height=48 + (80 if (i % 5 == 0) else 0),
                        )
                    ),
                ]),
                all=200,
            ),
        ])


if __name__ == '__main__':
    app = App(MainPage, durable_store='/run/user/1000/example_app.db', durable_model=Model)
    app.run()
