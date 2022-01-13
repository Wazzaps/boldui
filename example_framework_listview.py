#!/usr/bin/env python3
from boldui import Ops, Expr
from boldui.app import App, update_widget
from boldui.framework import Rectangle, SizedBox, Text, Stack, EventHandler, Widget, Column, PositionOffset, WatchVar, \
    Context, Padding, Clip, ListViewInner, Flexible, Row
from boldui.store import BaseModel


class Model(BaseModel):
    scroll_pos: int
    item_offset: int
    lv_state: ListViewInner.State


class ListView(Widget):
    HEIGHT_SLACK = 64
    ITEM_HEIGHT = 32

    def build(self):
        def refresh_list(data):
            height, lv_scroll_pos, lv_list_start = data
            print('refresh_list', height, lv_scroll_pos, lv_list_start)
            item_offset = int(
                (lv_scroll_pos - ListView.HEIGHT_SLACK) // ListView.HEIGHT_SLACK
                * (ListView.HEIGHT_SLACK / ListView.ITEM_HEIGHT)
            )
            Context['_app'].server.set_remote_var('lv_list_start', 'n', item_offset * ListView.ITEM_HEIGHT)
            Model.item_offset = item_offset
            update_widget()

        item_offset = Model.item_offset
        return EventHandler(
            WatchVar(
                cond=Expr(
                    (
                        (
                            (Expr.var('lv_scroll_pos') - ListView.HEIGHT_SLACK) // ListView.HEIGHT_SLACK
                            * (ListView.HEIGHT_SLACK / ListView.ITEM_HEIGHT)
                        ) // 1
                    ) != item_offset
                ),
                data=[Expr.var('height'), Expr.var('lv_scroll_pos'), Expr.var('lv_list_start')],
                handler=refresh_list,
                wait_for_roundtrip=True,
                child=PositionOffset(
                    Column([
                        SizedBox(
                            Text(text=f"{i + item_offset}", color=0xffffffff, font_size=24),
                            height=32,
                        )
                        for i in range(20)
                    ]),
                    y=Expr.var('lv_list_start') - Expr.var('lv_scroll_pos')
                ),
            ),

            on_scroll=[
                Ops.set_var(
                    'lv_scroll_pos',
                    (Expr.var('lv_scroll_pos') - Expr.var('scroll_y') * 10).max(0)
                ),
            ],
        )


class ListView2(Widget):
    HEIGHT_SLACK = 64
    ITEM_HEIGHT = 32

    def __init__(self, builder):
        self.builder = builder
        super().__init__()

    def build(self):
        def refresh_list(data):
            height, lv_scroll_pos, lv_list_start = data
            print('refresh_list', height, lv_scroll_pos, lv_list_start)
            # item_offset = int(
            #     (lv_scroll_pos - ListView.HEIGHT_SLACK) // ListView.HEIGHT_SLACK
            #     * (ListView.HEIGHT_SLACK / ListView.ITEM_HEIGHT)
            # )
            # Context['_app'].server.set_remote_var('lv_list_start', 'n', item_offset * ListView.ITEM_HEIGHT)
            # Model.item_offset = item_offset
            # update_widget()

        # item_offset = Model.item_offset
        return EventHandler(
            # Clip(
                ListViewInner(
                    state=Model.lv_state,
                    builder=self.builder,
                    offset=Expr.var('lv_list_start') - Expr.var('lv_scroll_pos'),
                ),
            # ),

            on_scroll=[
                Ops.set_var(
                    'lv_scroll_pos',
                    (Expr.var('lv_scroll_pos') - Expr.var('scroll_y') * 10).max(0)
                ),
            ],
        )


class MainPage(Widget):
    def build(self):
        return Stack([
            # Background
            Rectangle(color=0xff222222),

            # List
            Padding(
                Clip(
                    Stack([
                        Rectangle(color=0xff202090),
                        ListView2(
                            builder=lambda i: SizedBox(
                                Row([
                                    Flexible(),
                                    Stack([
                                        Rectangle(color=0x80ff0000 if (i % 2 == 0) else 0x8000ff00),
                                        Text(text=f"{i}", color=0xffffffff, font_size=24),
                                    ]),
                                    Flexible(),
                                ]),
                                height=32 + (80 if (i % 5 == 0) else 0),
                            )
                        ),
                    ]),
                ),
                all=90,
            ),
        ])


if __name__ == '__main__':
    app = App(MainPage, durable_store='/run/user/1000/example_app.db', durable_model=Model)
    app.run()
