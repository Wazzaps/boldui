#!/usr/bin/env python3
from boldui.adwaita import Switch
from boldui.app import App, widget
from boldui.framework import Rectangle, Padding, Stack, DBGHighlight
from boldui.store import BaseModel


class Model(BaseModel):
    switch_state: Switch.State


@widget
def main_page():

    # Buttons
    return Stack([
        # Background
        Rectangle(color=0xff242424),

        Padding(
            Switch(state=Model.switch_state),
            all=10
        ),
    ])


if __name__ == '__main__':
    app = App(main_page, durable_store='/run/user/1000/example_app.db', durable_model=Model)
    app.run()
