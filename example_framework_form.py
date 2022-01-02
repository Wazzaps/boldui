#!/usr/bin/env python3
from boldui.app import App, widget
from boldui.framework import Clear, Column, Row, Text, Flexible, Rectangle, SizedBox

Store = {}



@widget
def main_page():
    def greet():
        print(f'Hello, {Store["firstname"]} {Store["lastname"]}!')
        Store['firstname'] = ''
        Store['lastname'] = ''

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

    # # Flex test
    # return Clear(
    #     color=0xff402020,
    #     child=Column([
    #         Row([
    #             Rectangle(color=0xff222222),
    #             Rectangle(color=0xff999999),
    #             Rectangle(color=0xffdddddd),
    #         ]),
    #         Row([
    #             Rectangle(color=0xffdddddd),
    #             Rectangle(color=0xff222222),
    #             Rectangle(color=0xff999999),
    #         ]),
    #         Row([
    #             Rectangle(color=0xff999999),
    #             Rectangle(color=0xffdddddd),
    #             Rectangle(color=0xff222222),
    #         ]),
    #     ]),
    # )

    # # Sized test
    # return Clear(
    #     color=0xff402020,
    #     child=Column([
    #         Row([
    #             Rectangle(color=0xff222222),
    #             SizedBox(
    #                 width=100, height=100,
    #                 child=Rectangle(color=0xff999999)
    #             ),
    #             Rectangle(color=0xffdddddd),
    #         ]),
    #         Row([
    #             SizedBox(
    #                 width=100, height=100,
    #                 child=Rectangle(color=0xffdddddd)
    #             ),
    #             SizedBox(
    #                 width=100, height=100,
    #                 child=Rectangle(color=0xff222222)
    #             ),
    #             SizedBox(
    #                 width=100, height=100,
    #                 child=Rectangle(color=0xff999999)
    #             ),
    #         ]),
    #         Row([
    #             Rectangle(color=0xff999999),
    #             Rectangle(color=0xffdddddd),
    #             Rectangle(color=0xff222222),
    #         ]),
    #     ]),
    # )




    # Sized test 2
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
