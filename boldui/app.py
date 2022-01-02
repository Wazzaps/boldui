import typing
from typing import Dict

import lmdb as lmdb

from boldui import stringify_op, ProtocolServer, Expr
from boldui.framework import Widget, Clear


def widget(fn):
    def outer(*args, **kwargs):
        class AnonWidget(Widget):
            def build(self):
                return fn(*args, **kwargs)
        return AnonWidget().build()
    return outer


class App:
    _curr_context = None

    def __init__(self, scene, durable_store=None):
        self.scene = Clear(
            color=0xff000000,
            child=scene,
        )
        self.durable_store = lmdb.Environment(durable_store) if durable_store else None

    def run(self):
        built_scene = self.scene.build()
        size = built_scene.layout(Expr(0), Expr(0), Expr.var('width'), Expr.var('height'))
        rendered_scene = built_scene.render(Expr(0), Expr(0), size[0], size[1])
        for op in rendered_scene:
            print(stringify_op(op))
        server = ProtocolServer("/tmp/boldui.hello_world.sock", rendered_scene)
        server.serve()
