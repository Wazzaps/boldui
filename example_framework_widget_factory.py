#!/usr/bin/env python3
from boldui.adwaita import Switch
from boldui.app import App, stateful_widget
from boldui.framework import Rectangle, Padding, Stack
from boldui.store import BaseModel


class Model(BaseModel):
    switch_state: Switch.State


@stateful_widget
def main_page(model):
    # Buttons
    return Stack([
        # Background
        Rectangle(color=0xff242424),

        Padding(
            Switch(state=model.switch_state),
            all=10
        ),
    ])


if __name__ == '__main__':
    app_model = Model.open_db('/run/user/1000/example_app.db')
    app = App(lambda: main_page(app_model), durable_model=app_model)
    app.run()
