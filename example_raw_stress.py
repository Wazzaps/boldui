#!/usr/bin/env python3
import random

from boldui import Ops, Expr, var, ProtocolServer

if __name__ == '__main__':
    scene = [Ops.clear(0xff000000)]
    for i in range(500):
        w = random.random()
        h = random.random()
        x = random.random() * (1 - w)
        y = random.random() * (1 - h)
        color = random.randint(0x000000, 0xffffff) | 0xff000000
        scene.append(Ops.rect(
            (
                var('width') * x,
                var('height') * y,
                var('width') * (w + x),
                var('height') * (h + y),
            ),
            color
        ))

    server = ProtocolServer("/tmp/boldui.hello_world.sock")
    server.scene = scene
    server.serve()
