#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import json
import os
import socket
import struct
import boldui.hotrefresh
from simplexp import Expr, var, Oplist
from typing import List


class Actions:
    UPDATE_SCENE = 0
    HANDLER_REPLY = 1
    SET_VAR = 2
    WATCH_ACK = 3


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
        if obj['type'] in ('clear', 'rect', 'rrect', 'reply', 'setVar', 'evtHnd', 'watch', 'ackWatch', 'if', 'text', 'save',
                           'restore', 'clipRect', 'image'):
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
        return {'type': 'clear', 'color': color}

    @staticmethod
    def rect(rect, color):
        return {'type': 'rect', 'rect': rect, 'color': color}

    @staticmethod
    def rrect(rect, color, radius):
        return {'type': 'rrect', 'rect': rect, 'color': color, 'radius': radius}

    @staticmethod
    def reply(ident: int, data: List[Expr | int | float | None]):
        return {'type': 'reply', 'id': ident, 'data': data}

    @staticmethod
    def set_var(name: str, value: Expr):
        return {'type': 'setVar', 'name': name, 'value': value}

    @staticmethod
    def event_handler(rect, events, handler, oplist):
        return {
            'type': 'evtHnd',
            'rect': rect,
            'events': events,
            'handler': handler,
            'oplist': oplist,
        }

    @staticmethod
    def watch_var(id, cond, wait_for_roundtrip, handler):
        return {
            'type': 'watch',
            'id': id,
            'cond': cond,
            'waitForRoundtrip': wait_for_roundtrip,
            'handler': handler
        }

    @staticmethod
    def ack_watch(id):
        return {
            'type': 'ackWatch',
            'id': id,
        }

    @staticmethod
    def text(text, x, y, font_size, color):
        return {
            'type': 'text',
            'text': text,
            'x': x,
            'y': y,
            'fontSize': font_size,
            'color': color,
        }

    @staticmethod
    def if_(cond, t, f):
        return {'type': 'if', 'cond': cond, 'then': t, 'else': f}

    @staticmethod
    def save():
        return {'type': 'save'}

    @staticmethod
    def restore():
        return {'type': 'restore'}

    @staticmethod
    def clip_rect(rect):
        return {'type': 'clipRect', 'rect': rect}

    @staticmethod
    def image(uri, rect):
        return {'type': 'image', 'uri': uri, 'rect': rect}


class ProtocolServer:
    def __init__(self, address, reply_handler=None):
        self.pending_vars = {}
        self.address = address
        self._scene = None
        self._cached_scene = None
        self.reply_handler = reply_handler
        if os.path.exists(address):
            os.remove(address)

        SYSTEMD_SOCK_FD = 3
        self.server = socket.fromfd(SYSTEMD_SOCK_FD, socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket = None

        self._is_batch = False
        self._batch_scene_updated = False
        self._batch_vars = None

        hotrefresh.init(self)

    @property
    def scene(self):
        if self._cached_scene is None:
            if callable(self._scene):
                self._cached_scene = self._scene()
            else:
                self._cached_scene = self._scene

        return self._cached_scene

    @scene.setter
    def scene(self, value):
        self._scene = value
        self._cached_scene = None
        if self._is_batch:
            self._batch_scene_updated = True
        else:
            self._send_scene()

    def refresh_scene(self):
        self._cached_scene = None
        if self._is_batch:
            self._batch_scene_updated = True
        else:
            self._send_scene()

    @contextlib.contextmanager
    def batch_update(self):
        assert not self._is_batch

        self._is_batch = True
        self._batch_scene_updated = False
        self._batch_vars = {}

        yield

        if self._batch_scene_updated:
            self._send_scene()
        elif self._batch_vars:
            self._send_remote_var([(name, val_type, val) for name, (val_type, val) in self._batch_vars.items()])

        self._is_batch = False
        self._batch_scene_updated = False
        self._batch_vars = None

    def serve(self):
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
                self._send_scene()
            for var in self.pending_vars:
                self.set_remote_var(var, self.pending_vars[var][0], self.pending_vars[var][1])

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

            print('Client disconnected')
            break

    def _send_packet(self, packet):
        # print('Sending packet:', packet)
        self.socket.send(len(packet).to_bytes(4, 'big') + packet)

    def _handle_packet(self, packet):
        action = int.from_bytes(packet[:4], 'big')
        data = packet[4:]
        if action == Actions.HANDLER_REPLY:
            reply_count = int.from_bytes(data[:2], 'big')
            data = data[2:]
            with self.batch_update():
                for i in range(reply_count):
                    reply_len = int.from_bytes(data[:2], 'big')
                    reply_id = int.from_bytes(data[2:6], 'big')
                    reply_data = data[6:6+reply_len]
                    data_array = []
                    while reply_data:
                        item_type = reply_data[0]
                        if item_type == 0:
                            data_array.append(int.from_bytes(reply_data[1:9], 'big', signed=True))
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
            print('[app] Unknown packet type:', packet)

    def _send_scene(self):
        if self.socket:
            combined_scene = self.scene
            if self._batch_vars:
                combined_scene['vars'] = sum(
                    (
                        [k, v[0], json.dumps(Oplist(Expr.to_dict(v[1])).to_list())]
                        for k, v in self._batch_vars.items()
                    ),
                    []
                )
            self._send_packet(Actions.UPDATE_SCENE.to_bytes(4, 'big') + json.dumps(self.scene).encode())

    def set_remote_var(self, name, val_type, value):
        self.pending_vars[name] = (val_type, value)
        if self._is_batch:
            self._batch_vars[name] = (val_type, value)
        else:
            self._send_remote_var([(name, val_type, value)])

    def _send_remote_var(self, set_vars):
        if self.socket:
            parts = []
            for name, val_type, value in set_vars:
                value = Oplist(Expr.to_dict(value)).to_list()
                parts.append(name.encode() + b'\x00' + val_type.encode() + b'\x00' + json.dumps(value).encode())
            self._send_packet(Actions.SET_VAR.to_bytes(4, 'big') + b'\x00'.join(parts))

    def send_watch_ack(self, ack_id: int):
        if self.socket:
            self._send_packet(Actions.WATCH_ACK.to_bytes(4, 'big') + ack_id.to_bytes(8, 'big'))
