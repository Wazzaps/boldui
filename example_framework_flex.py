#!/usr/bin/env python3
from boldui.app import App, widget
from boldui.framework import Row, Rectangle, SizedBox


@widget
def main_page():
    RED = 0xffaa4444
    GREEN = 0xff44aa44
    BLUE = 0xff4444aa
    return Row([
        SizedBox(
            height=100,
            child=Rectangle(color=RED)
        ),
        SizedBox(
            width=100,
            child=Rectangle(color=GREEN)
        ),
        Rectangle(color=BLUE),
    ])


if __name__ == '__main__':
    app = App(main_page(), durable_store='/home/david/.local/example_app.db')
    app.run()
