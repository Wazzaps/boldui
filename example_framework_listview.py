#!/usr/bin/env python3
from boldui.app import App
from boldui.framework import Rectangle, SizedBox, Text, Stack, Widget, Flexible, Row, ListView
from boldui.store import BaseModel


class Model(BaseModel):
    list_state1: ListView.State
    list_state2: ListView.State


class MainPage(Widget):
    def build(self):
        return Stack([
            # Background
            Rectangle(color=0xff222222),

            # List
            Row([
                Stack([
                    Rectangle(color=0xff202090),
                    ListView(
                        state=Model.list_state1,
                        var_prefix='lv1_',
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
                Stack([
                    Rectangle(color=0xff202060),
                    ListView(
                        state=Model.list_state2,
                        var_prefix='lv2_',
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
            ]),
        ])


if __name__ == '__main__':
    app = App(MainPage, durable_store='/run/user/1000/example_app.db', durable_model=Model)
    app.run()
