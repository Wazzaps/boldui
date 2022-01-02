#!/usr/bin/env python3
import random

from boldui import Ops, Expr, ProtocolServer

if __name__ == '__main__':
    def make_scene(rect_color):
        return [
            Ops.clear(0xff202030),

            # Left rectangle
            Ops.rect(
                (
                    20,
                    20,
                    Expr.var('width') // 2 - 10,
                    Expr.var('height') - 20,
                ),
                0xffa0a0a0
            ),

            # Right rectangle
            Ops.rect(
                (
                    Expr.var('width') // 2 + 10,
                    20,
                    Expr.var('width') - 20,
                    Expr.var('height') - 20,
                ),
                0xffa0a0a0
            ),

            # Rect in the middle (border)
            Ops.rect(
                (
                    (Expr.var('width') // 2) - 70,
                    (Expr.var('height') // 2) - 70,
                    (Expr.var('width') // 2) + 70,
                    (Expr.var('height') // 2) + 70,
                ),
                0xff202030,
            ),

            # Rect in the middle
            Ops.rect(
                (
                    (Expr.var('width') // 2) - 50,
                    (Expr.var('height') // 2) - 50,
                    (Expr.var('width') // 2) + 50,
                    (Expr.var('height') // 2) + 50,
                ),
                rect_color,
            ),

            # On click handler for middle rect
            Ops.event_handler(
                rect=(
                    (Expr.var('width') // 2) - 50,
                    (Expr.var('height') // 2) - 50,
                    (Expr.var('width') // 2) + 50,
                    (Expr.var('height') // 2) + 50,
                ),
                events=0x1,
                handler=[
                    Ops.reply(0x123, [Expr.var('event_x'), Expr.var('event_y'), Expr.var('time')]),
                ],
            ),
        ]

    def handle_reply(ident, data):
        if ident == 0x123:
            click_x, click_y, click_time = data
            print('Click at pos ({}, {}) at time {}'.format(click_x, click_y, click_time))
            color = random.randint(0x000000, 0xffffff)
            server.scene = make_scene(0xff000000 | color)

    server = ProtocolServer("/tmp/boldui.hello_world.sock", make_scene(0xffc08080), handle_reply)
    server.serve()
