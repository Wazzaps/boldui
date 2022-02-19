#!/usr/bin/env python3
from boldui.adwaita import Button
from boldui.app import App
from boldui.framework import Row, Rectangle, SizedBox, Text, Center, Stack, Widget, WatchVar
from boldui.store import BaseModel


class Model(BaseModel):
    counter: int


class MainPage(Widget):
    def build(self):
        def dec(_):
            Model.counter -= 1

        def inc(_):
            Model.counter += 1

        return Stack([
            # Background
            Rectangle(color=0xff242424),

            # Counter
            Center(
                WatchVar(
                    cond=Model.bind.counter == 3,
                    data=[Model.bind.counter],
                    handler=lambda _: print('Icecream!'),
                    child=Row([
                        SizedBox(
                            width=80, height=80,
                            child=Button(
                                Text(text='-', font_size=24),
                                on_mouse_down=dec,
                            ),
                        ),
                        SizedBox(
                            width=130, height=80,
                            child=Text(text=Model.bind.counter.to_str(), font_size=24)
                        ),
                        SizedBox(
                            width=80, height=80,
                            child=Button(
                                Text(text='+', font_size=24),
                                on_mouse_down=inc,
                            ),
                        ),
                    ]),
                ),
            ),
        ])


if __name__ == '__main__':
    app = App(MainPage, durable_store='/run/user/1000/example_app.db', durable_model=Model)
    app.run()
