from dataclasses import dataclass
from typing import List, Optional

import lmdb

from boldui import Expr, var

DEBUG = False


class BaseModel:
    def __init__(
            self,
            db: lmdb.Environment,
            txn: List[Optional[lmdb.Transaction]],
            prefix: str = 'd',
            parent=None,
            field_counter=None
    ):
        if field_counter is None:
            field_counter = [0]

        default_values = {
            f: getattr(type(self), f)
            for f in type(self).__dict__ if f in type(self).__annotations__
        }

        for f in default_values:
            delattr(type(self), f)

        self.__dict__['_ids'] = {}
        self.__dict__['_types'] = {}
        self.__dict__['_defaults'] = {}
        self.__dict__['_db'] = db
        self.__dict__['_txn'] = txn

        if parent is not None:
            self.__dict__['_read_items'] = parent.__dict__['_read_items']
            self.__dict__['_written_items'] = parent.__dict__['_written_items']
            self.__dict__['_bound_items'] = parent.__dict__['_bound_items']
        else:
            self.__dict__['_read_items'] = set()
            self.__dict__['_written_items'] = set()
            self.__dict__['_bound_items'] = set()

        for field_name, field_type in type(self).__annotations__.items():
            # print(f'- #{field_counter[0]}: {field_name}: {field_type}')
            if issubclass(field_type, BaseModel):
                self.__dict__[field_name] = field_type(db, txn, prefix, self, field_counter)
            else:
                self.__dict__['_ids'][field_name] = f'{prefix}:{field_counter[0]}'
                self.__dict__['_types'][field_name] = field_type
                if field_name in default_values:
                    self.__dict__['_defaults'][field_name] = default_values[field_name]

            field_counter[0] += 1

        self.__dict__['_last_id'] = field_counter[0]

    def __hash__(self):
        return self.__dict__['_last_id']

    @classmethod
    def open_db(cls, path: str, prefix: str = 'd'):
        return cls(db=lmdb.Environment(path), txn=[None], prefix=prefix)

    def key_of(self, item):
        return self.__dict__['_ids'][item]

    def bind(self, item):
        self.__dict__['_bound_items'].add((self, item))
        return var(self.__dict__['_ids'][item])

    def begin_txn(self, write=False):
        db: lmdb.Environment = self.__dict__['_db']
        self.__dict__['_txn'][0] = db.begin(write=write)
        self.__dict__['_read_items'].clear()
        self.__dict__['_written_items'].clear()
        self.__dict__['_bound_items'].clear()

    def commit_txn(self):
        txn: lmdb.Transaction = self.__dict__['_txn'][0]
        assert txn, 'Tried to commit, but no transaction in progress'
        txn.commit()

    def abort_txn(self):
        txn: lmdb.Transaction = self.__dict__['_txn'][0]
        assert txn, 'Tried to abort, but no transaction in progress'
        txn.abort()

    def __getattr__(self, item):
        if DEBUG:
            print('GET:', item)
        if item in self.__dict__['_ids']:
            self.__dict__['_read_items'].add((self, item))
            return self.__dict__['_types'][item](self.__dict__['_txn'][0].get(
                self.__dict__['_ids'][item].encode(),
                default=str(
                    self.__dict__['_defaults'].get(item, self.__dict__['_types'][item]())
                ).encode()
            ).decode())
        elif item in self.__dict__:
            return self.__dict__[item]
        else:
            raise AttributeError(f'{item} not found')

    def __setattr__(self, key, value):
        if DEBUG:
            print('SET:', key, '=', value)
        if key in self.__dict__['_ids']:
            self.__dict__['_written_items'].add((self, key))
            self.__dict__['_txn'][0].put(
                self.__dict__['_ids'][key].encode(),
                str(value).encode(),
            )
        else:
            raise AttributeError(f'{key} not found')
