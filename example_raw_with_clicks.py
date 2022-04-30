#!/usr/bin/env python3
import random

from boldui import Ops, Oplist, Expr, var, ProtocolServer

if __name__ == '__main__':
    def make_scene(rect_color):
        oplist = Oplist()
        reply_oplist = Oplist()
        scene = [
            Ops.clear(0xff202030),

            # Left rectangle
            Ops.rect(
                (
                    oplist.append(20),
                    oplist.append(20),
                    oplist.append(var('width') // 2 - 10),
                    oplist.append(var('height') - 20),
                ),
                oplist.append(0xffa0a0a0),
            ),

            # Right rectangle
            Ops.rect(
                (
                    oplist.append(var('width') // 2 + 10),
                    oplist.append(20),
                    oplist.append(var('width') - 20),
                    oplist.append(var('height') - 20),
                ),
                oplist.append(Expr.if_(var('width') > 500, 0xffa0a0a0, 0xffe0e0e0)),
            ),

            # Rect in the middle (border)
            Ops.rect(
                (
                    oplist.append((var('width') // 2) - 70),
                    oplist.append((var('height') // 2) - 70),
                    oplist.append((var('width') // 2) + 70),
                    oplist.append((var('height') // 2) + 70),
                ),
                oplist.append(0xff202030),
            ),

            # Rect in the middle
            Ops.rect(
                (
                    oplist.append((var('width') // 2) - 50),
                    oplist.append((var('height') // 2) - 50),
                    oplist.append((var('width') // 2) + 50),
                    oplist.append((var('height') // 2) + 50),
                ),
                oplist.append(rect_color),
            ),

            # On click handler for middle rect
            Ops.event_handler(
                rect=(
                    oplist.append((var('width') // 2) - 50),
                    oplist.append((var('height') // 2) - 50),
                    oplist.append((var('width') // 2) + 50),
                    oplist.append((var('height') // 2) + 50),
                ),
                events=0x1,
                handler=[
                    Ops.reply(0x123, [
                        reply_oplist.append(var('event_x')),
                        reply_oplist.append(var('event_y')),
                        reply_oplist.append(var('time')),
                    ]),
                ],
                oplist=reply_oplist.to_list()
            ),
        ]
        return {'oplist': oplist.to_list(), 'scene': scene}

    def handle_reply(ident, data):
        if ident == 0x123:
            click_x, click_y, click_time = data
            print('Click at pos ({}, {}) at time {}'.format(click_x, click_y, click_time))
            color = random.randint(0x000000, 0xffffff)
            server.scene = make_scene(0xff000000 | color)

    server = ProtocolServer("/tmp/boldui.hello_world.sock", handle_reply)
    server.scene = make_scene(0xffc08080)
    server.serve()
