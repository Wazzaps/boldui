#!/usr/bin/env python3
from boldui.app import App
from boldui.framework import Rectangle, SizedBox, Text, Stack, Widget, Flexible, Row, ListView, Padding, Column
from boldui.store import BaseModel


class Model(BaseModel):
    list_state1: ListView.State
    list_state2: ListView.State


class MainPage(Widget):
    def __init__(self, model):
        self.model = model

    def build(self):
        PADDING = 200
        return Stack([
            # Background
            Rectangle(color=0xff222222),

            # List
            Row([
                Stack([
                    Rectangle(color=0xff202090),
                    Padding(
                        ListView(
                            state=self.model.list_state1,
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
                            ),
                            clip=False,
                        ),
                        vertical=PADDING,
                    ),

                    # Highlight padding
                    Column([
                        SizedBox(Rectangle(color=0xaa202090), height=PADDING),
                        Rectangle(color=0x0),
                        SizedBox(Rectangle(color=0xaa202090), height=PADDING),
                    ])
                ]),
                Stack([
                    Rectangle(color=0xff202060),
                    ListView(
                        state=self.model.list_state2,
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
    app_model = Model.open_db('/run/user/1000/example_app.db')
    app = App(lambda: MainPage(app_model), durable_model=app_model)
    app.run()
