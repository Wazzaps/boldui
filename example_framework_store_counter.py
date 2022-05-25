#!/usr/bin/env python3
from boldui.adwaita import Button
from boldui.app import App, stateful_widget
from boldui.framework import Row, Rectangle, SizedBox, Text, Center, Stack, WatchVar
from boldui.store import BaseModel


class Model(BaseModel):
    counter: int


@stateful_widget
def main_page(model):
    def dec(_):
        model.counter -= 1

    def inc(_):
        model.counter += 1

    return Stack([
        # Background
        Rectangle(color=0xff242424),

        # Counter
        Center(
            WatchVar(
                cond=model.bind('counter') == 3,
                data=[model.bind('counter')],
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
                        child=Text(text=model.bind('counter').to_str(), font_size=24)
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
    app_model = Model.open_db('/run/user/1000/example_app.db')
    app = App(lambda: main_page(app_model), durable_model=app_model)
    app.run()
