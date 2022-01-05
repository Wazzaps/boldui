import lmdb as lmdb

from boldui import stringify_op, ProtocolServer, Expr
from boldui.framework import Widget, Clear, export, Context


def update_widget():
    Context['_app'].server.scene = Context['_app'].rebuild()


def widget(fn):
    def outer(*args, **kwargs):
        class AnonWidget(Widget):
            def build(self):
                return fn(*args, **kwargs)
        return AnonWidget().build()
    return outer


class App:
    _curr_context = None

    def __init__(self, scene, durable_store=None, durable_model=None):
        self.scene = scene
        self._scene_instance = None
        self.server = None
        self.durable_store = lmdb.Environment(durable_store) if durable_store else None
        self.durable_model = durable_model
        self._reply_handlers = {}

    def rebuild(self):
        txn = self.durable_store.begin(write=True)
        model_instance = self.durable_model(txn, 'd')

        try:
            with export('_app', self):
                with export('_reply_handlers', self._reply_handlers):
                    if self._scene_instance is None:
                        self._scene_instance = self.scene()
                    else:
                        self._scene_instance.build()

                    built_scene = Clear(
                        color=0xff000000,
                        child=self._scene_instance,
                    ).build()

                    _read_items = set(model_instance._read_items)
                    for path in model_instance._bound_items:
                        item = model_instance._items_by_path[path]
                        _key = f'{item.model_name}#{item.id}'
                        _var_key = f'{model_instance._prefix}:{_key}'
                        model_instance._update_client(_var_key, item.type, model_instance._get_item(path))

            txn.commit()
            # print(f'bound_items: {model_instance._bound_items}')
            # print(f'read_items: {model_instance._read_items}')
        except BaseException:
            txn.abort()
            raise

        size = built_scene.layout(Expr(0), Expr(0), Expr.var('width'), Expr.var('height'))
        rendered_scene = built_scene.render(Expr(0), Expr(0), size[0], size[1])
        for op in rendered_scene:
            print(stringify_op(op))

        return rendered_scene

    def run(self):
        self.server = ProtocolServer("/tmp/boldui.hello_world.sock", reply_handler=self._reply_handler)
        self.server.scene = self.rebuild()
        self.server.serve()

    def _reply_handler(self, reply_id, data_array):
        txn = self.durable_store.begin(write=True)
        self.durable_model(txn, 'd')

        try:
            with export('_app', self):
                with export('_reply_handlers', self._reply_handlers):
                    self._reply_handlers[reply_id](data_array)
            txn.commit()
        except BaseException:
            txn.abort()
            raise
