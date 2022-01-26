#!/usr/bin/env python3
from boldui.adwaita import TextButton
from boldui.app import App, widget
from boldui.framework import Row, Rectangle, SizedBox, Padding, Stack, Image, Column


@widget
def main_page():
    # def greet():
    #     print(f'Hello, {Store["firstname"]} {Store["lastname"]}!')
    #     Store['firstname'] = ''
    #     Store['lastname'] = ''

    # return Clear(
    #     color=0xff402020,
    #     child=Column([
    #         # Row([
    #         #     Text(text='First Name'),
    #         #     # TextInput(model=Store.bind('firstname')),
    #         # ]),
    #         # Row([
    #         #     Text(text='Last Name'),
    #         #     # TextInput(model=Store.bind('lastname')),
    #         # ]),
    #         # Row([
    #             # Flexible(),
    #             Rectangle(color=0xff222222),
    #             Rectangle(color=0xff999999),
    #             Rectangle(color=0xffdddddd),
    #             # Button(label='Greet', on_click=greet),
    #         # ]),
    #     ]),
    # )

    # Buttons
    return Stack([
        # Background
        Rectangle(color=0xff242424),
        # Image(uri='/home/david/Pictures/Wallpapers/void_4k_desktop.jpg'),

        Padding(
            all=17,
            child=Column([
                Row([
                    TextButton('Hello', on_mouse_down=lambda _: None),
                    SizedBox(child=None, width=4),
                    TextButton('World', on_mouse_down=lambda _: None),
                ]),
                Row([
                    TextButton('Label', on_mouse_down=lambda _: None),
                    SizedBox(child=None, width=4),
                    TextButton('Foo', on_mouse_down=lambda _: None),
                ]),
            ]),
        ),
    ])


if __name__ == '__main__':
    app = App(main_page)
    app.run()
