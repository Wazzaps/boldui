import contextlib

from boldui import ProtocolServer, Oplist, Expr, var
from boldui.framework import Widget, Clear, export, Context
from boldui.store import BaseModel

_TYPE_TO_TYPENAME = {
    int: 'int',
    float: 'float',
    str: 'string',
}


def update_widget():
    print('update_widget')
    Context['_app'].server.scene = lambda: Context['_app'].force_rebuild()


def widget(fn):
    def outer(*args, **kwargs):
        class AnonWidget(Widget):
            def build(self):
                return fn(*args, **kwargs)
        return AnonWidget().build()
    return outer


def stateful_widget(fn):
    def outer(model, *args, **kwargs):
        class AnonWidget(Widget):
            def build(self):
                return fn(model, *args, **kwargs)
        return AnonWidget()
    return outer


class App:
    _curr_context = None

    def __init__(self, scene, durable_model=None):
        self.scene = scene
        self._scene_instance = None
        self.server = None
        self.durable_model: BaseModel = durable_model
        self._reply_handlers = {}
        self._txn_active = False
        self._last_read_items = set()
        self._dirty = False

    def force_rebuild(self):
        return self.rebuild()

    def rebuild(self):
        with self._build_context(is_main_scene=True):
            if self._scene_instance is None:
                self._scene_instance = self.scene()
            else:
                self._scene_instance.build()

            built_scene = Clear(
                color=0xff000000,
                child=self._scene_instance,
            ).build_recursively()

            size = built_scene.layout(Expr(0), Expr(0), var('width'), var('height'))
        oplist = Oplist()
        rendered_scene = built_scene.render(oplist, Expr(0), Expr(0), size[0], size[1])

        variables = {}
        if self.durable_model:
            variables.update({
                key: {'type': _TYPE_TO_TYPENAME[item_type], 'default': default_val}
                for key, item_type, default_val in self.durable_model.iter_fields()
            })

        # print(oplist.to_list())
        # for op in rendered_scene:
        #     print(stringify_op(op))

        return {'oplist': oplist.to_list(), 'scene': rendered_scene, 'vars': variables}

    def run(self):
        self.server = ProtocolServer("/tmp/boldui.hello_world.sock", reply_handler=self._reply_handler)
        self.server.scene = lambda: self.force_rebuild()
        self.server.serve()

    @contextlib.contextmanager
    def _build_context(self, is_main_scene=False):
        if self.durable_model is not None and not self._txn_active:
            self.durable_model.begin_txn(write=True)
            self._txn_active = True
            my_txn = True
        else:
            my_txn = False

        try:
            with export('_app', self):
                with export('_reply_handlers', self._reply_handlers):
                    yield self.durable_model

                    if my_txn:
                        _written_items = set(self.durable_model.__dict__['_written_items'])
                        if not self._last_read_items.isdisjoint(_written_items):
                            print('should update! dirty items:', self._last_read_items.intersection(_written_items))
                            self._dirty = True

                        if is_main_scene:
                            self._last_read_items = set(self.durable_model.__dict__['_read_items'])

                        bound_or_written = self.durable_model.__dict__['_bound_items'] | _written_items
                        # bound_or_written = _written_items  # FIXME: This fixes listview example

                        for container, item_name in bound_or_written:
                            # print('newly_bound_or_written:', item_name)

                            key = container.__dict__['_ids'][item_name]
                            item_type = container.__dict__['_types'][item_name]
                            value = getattr(container, item_name)

                            if item_type in (int, float):
                                Context['_app'].server.set_remote_var(key, 'n', value)
                            elif item_type is str:
                                Context['_app'].server.set_remote_var(key, 's', value)
            if my_txn:
                self.durable_model.commit_txn()
        except BaseException:
            if my_txn:
                self.durable_model.abort_txn()
            raise

        if my_txn:
            self._txn_active = False

    def _reply_handler(self, reply_id, data_array):
        with self._build_context():
            self._reply_handlers[reply_id](data_array)

        if self._dirty:
            print('refreshing!')
            self.server.refresh_scene()
            self._dirty = False

