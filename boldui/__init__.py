#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
from typing import List


class Actions:
    UPDATE_SCENE = 0
    HANDLER_REPLY = 1


def stringify_op(obj, indent=0):
    result = ''
    if isinstance(obj, list):
        result += '['
        if len(obj) != 0:
            result += '\n'
        for op in obj:
            result += ' ' * (indent + 2) + stringify_op(op, indent + 2) + ',\n'
        if len(obj) != 0:
            result += ' ' * indent
        result += ']'
        return result
    elif isinstance(obj, dict) and 'type' in obj:
        if obj['type'] in ('add', 'sub', 'mul', 'div', 'b_or', 'b_and', 'mod', 'abs', 'gt', 'lt', 'ge', 'le', 'eq',
                           'ne', 'neg', 'b_and', 'b_or', 'b_invert', 'if'):
            return str(Expr(obj))

        if obj['type'] in ('clear', 'rect', 'text'):
            result += 'Ops.' + obj['type'] + '('
            if len(obj.keys()) != 1:
                result += '\n'
                for key in obj.keys():
                    if key == 'type':
                        continue
                    result += ' ' * (indent + 2) + f'{key}={stringify_op(obj[key], indent + 2)},\n'
                result += ' ' * indent
            result += ')'
            return result

    return repr(obj)


class Ops:
    @staticmethod
    def clear(color):
        return {'type': 'clear', 'color': Expr.unwrap(color)}

    @staticmethod
    def rect(rect, color):
        return {'type': 'rect', 'rect': list(map(Expr.unwrap, rect)), 'color': Expr.unwrap(color)}

    @staticmethod
    def reply(ident: int, data: List[Expr | int | float]):
        return {'type': 'reply', 'id': ident, 'data': list(map(Expr.unwrap, data))}

    @staticmethod
    def event_handler(rect, events, handler):
        return {
            'type': 'evt_hnd',
            'rect': list(map(Expr.unwrap, rect)),
            'events': events,
            'handler': handler
        }

    @staticmethod
    def text(text, x, y, font_size, color):
        return {
            'type': 'text',
            'text': text,
            'x': Expr.unwrap(x),
            'y': Expr.unwrap(y),
            'fontSize': Expr.unwrap(font_size),
            'color': Expr.unwrap(color),
        }

    @staticmethod
    def if_(cond, t, f):
        return {'type': 'if', 'cond': Expr.unwrap(cond), 'then': Expr.unwrap(t), 'else': Expr.unwrap(f)}


class Expr:
    def __init__(self, val):
        if isinstance(val, Expr):
            self.val = val.val
        else:
            self.val = val

    @staticmethod
    def unwrap(value: Expr | int | float):
        if isinstance(value, (int, float)):
            return value
        else:
            return value.val

    @staticmethod
    def var(name):
        return Expr({'type': 'var', 'name': name})

    def __add__(self, other):
        other = Expr.unwrap(other)
        if isinstance(other, (int, float)) and isinstance(self.val, (int, float)):
            return Expr(self.val + other)
        elif isinstance(other, (int, float)) and other == 0:
            return self
        elif isinstance(other, (int, float)) and self.val['type'] == 'add':
            new_val = Expr(self.val['b']) + other
            if new_val.val == 0:
                return Expr(self.val['a'])
            else:
                return Expr({'type': 'add', 'a': self.val['a'], 'b': new_val.val})
        elif isinstance(other, (int, float)) and self.val['type'] == 'sub':
            new_val = Expr(self.val['b']) - other
            if new_val.val == 0:
                return Expr(self.val['a'])
            else:
                return Expr({'type': 'sub', 'a': self.val['a'], 'b': new_val.val})
        else:
            return Expr({'type': 'add', 'a': self.val, 'b': other})

    def __sub__(self, other):
        other = Expr.unwrap(other)
        if isinstance(other, (int, float)) and isinstance(self.val, (int, float)):
            return Expr(self.val - other)
        elif isinstance(other, (int, float)) and other == 0:
            return self
        elif isinstance(other, (int, float)) and self.val['type'] == 'add':
            new_val = Expr(self.val['b']) - other
            if new_val.val == 0:
                return Expr(self.val['a'])
            else:
                return Expr({'type': 'add', 'a': self.val['a'], 'b': new_val.val})
        elif isinstance(other, (int, float)) and self.val['type'] == 'sub':
            new_val = Expr(self.val['b']) + other
            if new_val.val == 0:
                return Expr(self.val['a'])
            else:
                return Expr({'type': 'sub', 'a': self.val['a'], 'b': new_val.val})
        else:
            return Expr({'type': 'sub', 'a': self.val, 'b': other})

    def __mul__(self, other):
        return Expr({'type': 'mul', 'a': self.val, 'b': Expr.unwrap(other)})

    def __mod__(self, other):
        return Expr({'type': 'mod', 'a': self.val, 'b': Expr.unwrap(other)})

    def __floordiv__(self, other):
        return Expr({'type': 'div', 'a': self.val, 'b': Expr.unwrap(other)})

    def __or__(self, other):
        return Expr({'type': 'b_or', 'a': self.val, 'b': Expr.unwrap(other)})

    def __and__(self, other):
        return Expr({'type': 'b_and', 'a': self.val, 'b': Expr.unwrap(other)})

    def sqrt(self):
        return Expr({'type': 'sqrt', 'a': self.val})

    def __gt__(self, other):
        return Expr({'type': 'gt', 'a': self.val, 'b': Expr.unwrap(other)})

    def __lt__(self, other):
        return Expr({'type': 'lt', 'a': self.val, 'b': Expr.unwrap(other)})

    def __ge__(self, other):
        return Expr({'type': 'ge', 'a': self.val, 'b': Expr.unwrap(other)})

    def __le__(self, other):
        return Expr({'type': 'le', 'a': self.val, 'b': Expr.unwrap(other)})

    def __eq__(self, other):
        return Expr({'type': 'eq', 'a': self.val, 'b': Expr.unwrap(other)})

    def __ne__(self, other):
        return Expr({'type': 'ne', 'a': self.val, 'b': Expr.unwrap(other)})

    def __neg__(self):
        return Expr({'type': 'neg', 'a': self.val})

    def __invert__(self):
        return Expr({'type': 'b_invert', 'a': self.val})

    def __abs__(self):
        return Expr({'type': 'abs', 'a': self.val})

    def __str__(self):
        if isinstance(self.val, (int, float)):
            return str(self.val)
        elif self.val['type'] == 'var':
            return self.val['name']
        elif self.val['type'] == 'add':
            return f'({Expr(self.val["a"])} + {Expr(self.val["b"])})'
        elif self.val['type'] == 'sub':
            return f'({Expr(self.val["a"])} - {Expr(self.val["b"])})'
        elif self.val['type'] == 'mul':
            return f'({Expr(self.val["a"])} * {Expr(self.val["b"])})'
        elif self.val['type'] == 'div':
            return f'({Expr(self.val["a"])} // {Expr(self.val["b"])})'
        elif self.val['type'] == 'b_or':
            return f'({Expr(self.val["a"])} | {Expr(self.val["b"])})'
        elif self.val['type'] == 'b_and':
            return f'({Expr(self.val["a"])} & {Expr(self.val["b"])})'
        elif self.val['type'] == 'mod':
            return f'({Expr(self.val["a"])} % {Expr(self.val["b"])})'
        elif self.val['type'] == 'abs':
            return f'abs({Expr(self.val["a"])})'
        elif self.val['type'] == 'sqrt':
            return f'sqrt({Expr(self.val["a"])})'
        elif self.val['type'] == 'gt':
            return f'({Expr(self.val["a"])} > {Expr(self.val["b"])})'
        elif self.val['type'] == 'lt':
            return f'({Expr(self.val["a"])} < {Expr(self.val["b"])})'
        elif self.val['type'] == 'ge':
            return f'({Expr(self.val["a"])} >= {Expr(self.val["b"])})'
        elif self.val['type'] == 'le':
            return f'({Expr(self.val["a"])} <= {Expr(self.val["b"])})'
        elif self.val['type'] == 'eq':
            return f'({Expr(self.val["a"])} == {Expr(self.val["b"])})'
        elif self.val['type'] == 'ne':
            return f'({Expr(self.val["a"])} != {Expr(self.val["b"])})'
        elif self.val['type'] == 'neg':
            return f'-{Expr(self.val["a"])}'
        elif self.val['type'] == 'b_and':
            return f'({Expr(self.val["a"])} & {Expr(self.val["b"])})'
        elif self.val['type'] == 'b_or':
            return f'({Expr(self.val["a"])} | {Expr(self.val["b"])})'
        elif self.val['type'] == 'b_invert':
            return f'~{Expr(self.val["a"])}'
        elif self.val['type'] == 'if':
            return f'if {Expr(self.val["cond"])} {{ {Expr(self.val["then"])} }} else {{ {Expr(self.val["else"])} }}'
        else:
            return json.dumps(self.val)

    def __repr__(self):
        return self.__str__()


class ProtocolServer:
    def __init__(self, address, initial_scene=None, reply_handler=None):
        self.address = address
        self._scene = initial_scene
        self.reply_handler = reply_handler
        if os.path.exists(address):
            os.remove(address)

        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(address)
        self.socket = None

    @property
    def scene(self):
        return self._scene

    @scene.setter
    def scene(self, value):
        self._scene = value
        self.send_scene()

    def serve(self):
        subprocess.Popen('sleep 0.2 && uiclient/main.py /tmp/boldui.hello_world.sock', shell=True)
        while True:
            print('Waiting for connection...')
            self.server.listen(1)
            self.socket, addr = self.server.accept()

            print('Client connected', addr)
            self.socket.send(b"BoldUI\x00\x01")

            # Read header
            header = self.socket.recv(8)
            if header != b"BoldUI\x00\x01":
                print("Invalid header, disconnecting")
                break

            print("Handshake complete, sending initial scene")
            if self.scene:
                self.send_scene()

            print(f'Server PID is {os.getpid()}')
            while True:
                packet = b''
                packet_length = self.socket.recv(4)
                if not packet_length:
                    break

                packet_length = int.from_bytes(packet_length, 'big')
                while len(packet) < packet_length:
                    packet += self.socket.recv(packet_length - len(packet))
                    if not packet:
                        break

                self._handle_packet(packet)

    def _send_packet(self, packet):
        # print('Sending packet:', packet)
        self.socket.send(len(packet).to_bytes(4, 'big'))
        self.socket.send(packet)

    def _handle_packet(self, packet):
        action = int.from_bytes(packet[:4], 'big')
        data = packet[4:]
        if action == Actions.HANDLER_REPLY:
            reply_count = int.from_bytes(data[:2], 'big')
            data = data[2:]
            for i in range(reply_count):
                reply_len = int.from_bytes(data[:2], 'big')
                reply_id = int.from_bytes(data[2:6], 'big')
                reply_data = data[6:6+reply_len]
                data_array = []
                while reply_data:
                    item_type = reply_data[0]
                    if item_type == 0:
                        data_array.append(int.from_bytes(reply_data[1:9], 'big'))
                        reply_data = reply_data[9:]
                    elif item_type == 1:
                        data_array.append(struct.unpack('>d', reply_data[1:9])[0])
                        reply_data = reply_data[9:]
                    else:
                        raise ValueError(f"Unknown item type {item_type}")
                if self.reply_handler:
                    # print(f'Reply: {hex(reply_id)} : {data_array}')
                    self.reply_handler(reply_id, data_array)

        else:
            print('Unknown packet type:', packet)

    def send_scene(self):
        self._send_packet(Actions.UPDATE_SCENE.to_bytes(4, 'big') + json.dumps(self._scene).encode())
