#!/usr/bin/env python3
import random

from boldui import Ops, Oplist, Expr, var, ProtocolServer

if __name__ == '__main__':
    oplist = Oplist()
    scene = [Ops.clear(0xff000000)]
    for i in range(500):
        w = random.random()
        h = random.random()
        x = random.random() * (1 - w)
        y = random.random() * (1 - h)
        color = random.randint(0x000000, 0xffffff) | 0xff000000
        scene.append(Ops.rect(
            (
                oplist.append(var('width') * x),
                oplist.append(var('height') * y),
                oplist.append(var('width') * (w + x)),
                oplist.append(var('height') * (h + y)),
            ),
            oplist.append(color)
        ))

    server = ProtocolServer("/tmp/boldui.hello_world.sock")
    server.scene = {'oplist': oplist.to_list(), 'scene': scene, 'vars': {}}
    server.serve()
