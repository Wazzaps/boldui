#!/usr/bin/env python3
import random

from boldui import Ops, Expr, var, ProtocolServer

if __name__ == '__main__':
    def make_scene(rect_color):
        return [
            Ops.clear(0xff202030),

            # Left rectangle
            Ops.rect(
                (
                    20,
                    20,
                    var('width') // 2 - 10,
                    var('height') - 20,
                ),
                0xffa0a0a0
            ),

            # Right rectangle
            Ops.rect(
                (
                    var('width') // 2 + 10,
                    20,
                    var('width') - 20,
                    var('height') - 20,
                ),
                0xffa0a0a0
            ),

            # Rect in the middle (border)
            Ops.rect(
                (
                    (var('width') // 2) - 70,
                    (var('height') // 2) - 70,
                    (var('width') // 2) + 70,
                    (var('height') // 2) + 70,
                ),
                0xff202030,
            ),

            # Rect in the middle
            Ops.rect(
                (
                    (var('width') // 2) - 50,
                    (var('height') // 2) - 50,
                    (var('width') // 2) + 50,
                    (var('height') // 2) + 50,
                ),
                rect_color,
            ),

            # On click handler for middle rect
            Ops.event_handler(
                rect=(
                    (var('width') // 2) - 50,
                    (var('height') // 2) - 50,
                    (var('width') // 2) + 50,
                    (var('height') // 2) + 50,
                ),
                events=0x1,
                handler=[
                    Ops.reply(0x123, [var('event_x'), var('event_y'), var('time')]),
                ],
            ),
        ]

    def handle_reply(ident, data):
        if ident == 0x123:
            click_x, click_y, click_time = data
            print('Click at pos ({}, {}) at time {}'.format(click_x, click_y, click_time))
            color = random.randint(0x000000, 0xffffff)
            server.scene = make_scene(0xff000000 | color)

    server = ProtocolServer("/tmp/boldui.hello_world.sock", handle_reply)
    server.scene = make_scene(0xffc08080)
    server.serve()
