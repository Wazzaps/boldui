#!/usr/bin/env python3
from boldui import Expr, Ops, stringify_op, ProtocolServer
from boldui.framework import Clear, Column, Padding, Center, SizedBox, Rectangle, Text, Flexible


def main():
    root = Clear(
        color=0xff202030,
        child=Column([
            Padding(
                Text(
                    'Hello, World!',
                    font_size=18,
                    color=0xffa0a0a0,
                ),
                all=10,
            ),
            Padding(
                Center(
                    SizedBox(
                        Rectangle(0xffa0a0a0),
                        width=abs((Expr.var('time') % 1) - 0.5) * 50 + 100,
                        height=abs(((Expr.var('time') + 0.5) % 1) - 0.5) * 50 + 100,
                    ),
                ),
                all=10,
            ),
            Padding(
                Rectangle(
                    color=Expr(Ops.if_(Expr.var('height') > 600, 0xffa0a0a0, 0xff9090d0))
                ),
                all=10
            ),
            Flexible(
                Padding(
                    Rectangle(
                        color=Expr(Ops.if_(Expr.var('width') > 800, 0xffa0a0a0, 0xffd09090))
                    ),
                    all=10
                ),
                flex_x=3,
            ),
        ]),
    )

    built_root = root.build()
    size = built_root.layout(Expr(0), Expr(0), Expr.var('width'), Expr.var('height'))
    scene = built_root.render(Expr(0), Expr(0), size[0], size[1])
    for op in scene:
        print(stringify_op(op))
    server = ProtocolServer("/tmp/boldui.hello_world.sock")
    server.scene = scene
    server.serve()


if __name__ == '__main__':
    main()
