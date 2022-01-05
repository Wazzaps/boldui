from dataclasses import dataclass

import lmdb

from boldui import Expr
from boldui.framework import Context


@dataclass
class ModelItem:
    id: int
    model_name: str
    name: str
    path: str
    type: type


# Big brain moment
class _MetaBaseModel(type):
    pass


class BaseModel(metaclass=_MetaBaseModel):
    def __init__(self, txn: lmdb.Transaction, prefix: str):
        self.bind = None  # Fake variable for intellisense
        del self.bind

        self._items_by_id = {}
        self._items_by_path = {}
        self._bound_items = set()
        self._read_items = set()
        self._txn = txn
        self._prefix = prefix

        ctr = 0

        def visit_class(cls, path, is_immed=False):
            nonlocal ctr

            for field_name, field_type in cls.__annotations__.items():
                new_path = f'{path}.{field_name}'
                if issubclass(field_type, BaseModel):
                    visit_class(field_type, new_path)
                    if is_immed:
                        setattr(type(type(self)), field_name, ModelProxyDescriptor(self, field_type, new_path))
                else:
                    item = ModelItem(id=ctr, model_name=type(self).__name__,
                                     name=field_name, path=new_path, type=field_type)
                    self._items_by_id[item.id] = item
                    self._items_by_path[item.path] = item
                    if is_immed:
                        setattr(type(type(self)), field_name, ModelItemDescriptor(self, field_type, new_path))
                    ctr += 1

        visit_class(type(self), '', is_immed=True)
        setattr(type(self), 'bind', ModelProxyDescriptor(self, type(self), '', is_bind=True))

    def __getattr__(self, item: str):
        raise AttributeError(f'Invalid field "{item}" on model "{type(self).__name__}"')

    def _get_item(self, path):
        item = self._items_by_path[path]
        _key = f'{item.model_name}#{item.id}'
        _var_key = f'{self._prefix}:{_key}'
        self._read_items.add(path)
        return item.type(self._txn.get(
            _key.encode(),
            default=str(item.type()).encode()
        ).decode())

    def _bind_item(self, path):
        self._bound_items.add(path)

    def _set_item(self, path, value):
        item = self._items_by_path[path]
        _key = f'{item.model_name}#{item.id}'
        _var_key = f'{self._prefix}:{_key}'
        self._txn.put(_key.encode(), str(value).encode())
        self._update_client(_var_key, item.type, value)

    def _update_client(self, key: str, val_type: type, value):
        if val_type in (int, float):
            Context['_app'].server.set_remote_var(key, 'n', value)
        elif val_type is str:
            Context['_app'].server.set_remote_var(key, 's', value)


class ModelItemDescriptor:
    def __init__(self, base_model: BaseModel, item_type: type, path: str, is_bind: bool = False):
        self._base_model = base_model
        self._item_type = item_type
        self._path = path
        self._is_bind = is_bind

        item = self._base_model._items_by_path[self._path]
        self._key = f'{item.model_name}#{item.id}'
        self._var_key = f'{self._base_model._prefix}:{self._key}'

    def __get__(self, instance, owner=None):

        if self._is_bind:
            self._base_model._bind_item(self._path)
            return Expr.var(self._var_key)
        else:
            value = self._base_model._get_item(self._path)
            print(f'GET: {type(self._base_model).__name__}{self._path}')
            return value

    def __set__(self, instance, value):
        if self._is_bind:
            raise AttributeError('Cannot modify binding')
        else:
            if not isinstance(value, self._item_type):
                raise TypeError(f'Invalid type for field {type(self._base_model).__name__}{self._path}')
            print(f'SET: {type(self._base_model).__name__}{self._path} = {value}')
            self._base_model._set_item(self._path, value)


class ModelProxyDescriptor:
    def __init__(self, base_model: BaseModel, submodel: type, path: str, is_bind: bool = False):
        self._base_model = base_model
        self._submodel = submodel
        self._path = path
        self._is_bind = is_bind

    def __get__(self, instance, owner=None):
        return make_model_proxy()(self._base_model, self._submodel, self._path, is_bind=self._is_bind)


def make_model_proxy():
    class ModelProxy:
        def __init__(self, base_model: BaseModel, submodel: type, path: str, is_bind: bool = False):
            self._base_model = base_model
            self._submodel = submodel
            self._path = path
            self._is_bind = is_bind

            for field_name, field_type in submodel.__annotations__.items():
                new_path = f'{path}.{field_name}'
                if issubclass(field_type, BaseModel):
                    print(f'bind proxy: {field_name}')
                    setattr(type(self), field_name, ModelProxyDescriptor(base_model, field_type, new_path, is_bind=is_bind))
                else:
                    print(f'bind item: {field_name}')
                    setattr(type(self), field_name, ModelItemDescriptor(base_model, field_type, new_path, is_bind=is_bind))

        def __getattr__(self, item):
            # print(self)
            try:
                return getattr(type(self), item)
            except AttributeError:
                raise AttributeError(f'Invalid field "{self._path[1:]}.{item}" on model "{type(self._base_model).__name__}"')

        def __str__(self):
            if self._is_bind:
                return f'<Bind ModelProxy: {type(self._base_model).__name__}{self._path}>'
            else:
                return f'<ModelProxy: {type(self._base_model).__name__}{self._path}>'

    return ModelProxy


def test():
    db = lmdb.Environment('/home/david/.local/example_app.db/')

    txn = db.begin(write=True)

    class Model(BaseModel):
        a: int
        b: int

    model = Model(txn, 'd')

    model.a = 5

    return txn, model
