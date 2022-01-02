#!/usr/bin/env python3
import json
import math
import socket
import struct
import sys
import threading
import time
from typing import Tuple

import skia

from main_loop import main_loop


class Actions:
    UPDATE_SCENE = 0
    HANDLER_REPLY = 1


class Protocol:
    def __init__(self, address, ui_client):
        self.address = address
        self.ui_client = ui_client

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def connect(self):
        self.socket.connect(self.address)

        server_header = self.socket.recv(8)
        assert server_header == b'BoldUI\x00\x01'
        self.socket.send(b'BoldUI\x00\x01')

        self.thread.start()

    def _loop(self):
        while True:
            packet = b''
            packet_length = self.socket.recv(4)
            if not packet_length:
                break

            packet_length = int.from_bytes(packet_length, 'big')
            while len(packet) < packet_length:
                packet += self.socket.recv(packet_length - len(packet))

            self._handle_packet(packet)

    def send_packet(self, packet):
        print('Sending packet:', packet)
        self.socket.send(len(packet).to_bytes(4, 'big'))
        self.socket.send(packet)

    def _handle_packet(self, packet):
        packet_type = int.from_bytes(packet[:4], 'big')
        packet = packet[4:]

        if packet_type == Actions.UPDATE_SCENE:
            self.ui_client.scene = json.loads(packet)
            # print(self.ui_client.scene)
        else:
            print('Unknown packet type:', packet)


class UIClient:
    def __init__(self, address):
        self.scene = [
            {'type': 'clear', 'color': 0xff202020},
        ]
        self.protocol = Protocol(address, self)
        self.persistent_context = {}

        self.protocol.connect()

    @staticmethod
    def _paint_from_int_color(color):
        return skia.Paint(skia.Color(
            (color >> 16) & 0xff,
            (color >> 8) & 0xff,
            color & 0xff,
            (color >> 24) & 0xff))

    @staticmethod
    def _resolve_str(value, context):
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            if value['type'] == 'to_str':
                return str(UIClient._resolve_int(value['a'], context))
            else:
                raise ValueError('Unknown str operation: {}'.format(value['type']))
        else:
            raise ValueError('Unknown type: {}'.format(value))

    @staticmethod
    def _resolve_int(value, context):
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, dict):
            if value['type'] == 'add':
                return UIClient._resolve_int(value['a'], context) + UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'sub':
                return UIClient._resolve_int(value['a'], context) - UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'mul':
                return UIClient._resolve_int(value['a'], context) * UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'div':
                return UIClient._resolve_int(value['a'], context) // UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'mod':
                return UIClient._resolve_int(value['a'], context) % UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'pow':
                return UIClient._resolve_int(value['a'], context) ** UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'sqrt':
                return UIClient._resolve_int(value['a'], context) ** 0.5
            elif value['type'] == 'sin':
                return math.sin(UIClient._resolve_int(value['a'], context))
            elif value['type'] == 'cos':
                return math.cos(UIClient._resolve_int(value['a'], context))
            elif value['type'] == 'tan':
                return math.tan(UIClient._resolve_int(value['a'], context))
            elif value['type'] == 'neg':
                return -UIClient._resolve_int(value['a'], context)
            elif value['type'] == 'abs':
                return abs(UIClient._resolve_int(value['a'], context))
            elif value['type'] == 'min':
                return min(UIClient._resolve_int(value['a'], context), UIClient._resolve_int(value['b'], context))
            elif value['type'] == 'max':
                return max(UIClient._resolve_int(value['a'], context), UIClient._resolve_int(value['b'], context))
            elif value['type'] == 'eq':
                return UIClient._resolve_int(value['a'], context) == UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'ne':
                return UIClient._resolve_int(value['a'], context) != UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'lt':
                return UIClient._resolve_int(value['a'], context) < UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'le':
                return UIClient._resolve_int(value['a'], context) <= UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'gt':
                return UIClient._resolve_int(value['a'], context) > UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'ge':
                return UIClient._resolve_int(value['a'], context) >= UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'b_and':
                return UIClient._resolve_int(value['a'], context) & UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'b_or':
                return UIClient._resolve_int(value['a'], context) | UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'b_xor':
                return UIClient._resolve_int(value['a'], context) ^ UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'b_invert':
                return ~UIClient._resolve_int(value['a'], context)
            elif value['type'] == 'shl':
                return UIClient._resolve_int(value['a'], context) << UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'shr':
                return UIClient._resolve_int(value['a'], context) >> UIClient._resolve_int(value['b'], context)
            elif value['type'] == 'if':
                if UIClient._resolve_int(value['cond'], context):
                    return UIClient._resolve_int(value['then'], context)
                else:
                    return UIClient._resolve_int(value['else'], context)
            elif value['type'] == 'var':
                return context.get(value['name'], 0)
            else:
                raise ValueError('Unknown int operation: {}'.format(value['type']))
        else:
            raise ValueError('Unknown type: {}'.format(value))

    def draw(self, canvas: skia.Canvas, scene_size: Tuple[int, int]) -> None:
        context = {
            **self.persistent_context,
            'width': scene_size[0],
            'height': scene_size[1],
            'time': time.time()
        }
        for item in self.scene:
            if item['type'] == 'clear':
                canvas.clear(item['color'])
            elif item['type'] == 'rect':
                canvas.drawRect(skia.Rect(
                    UIClient._resolve_int(item['rect'][0], context),
                    UIClient._resolve_int(item['rect'][1], context),
                    UIClient._resolve_int(item['rect'][2], context),
                    UIClient._resolve_int(item['rect'][3], context)
                ), self._paint_from_int_color(UIClient._resolve_int(item['color'], context)))
            elif item['type'] == 'text':
                paint = self._paint_from_int_color(UIClient._resolve_int(item['color'], context))
                font_size = UIClient._resolve_int(item['fontSize'], context)
                font = skia.Font(None, font_size)
                text = UIClient._resolve_str(item['text'], context)
                measurement = font.measureText(text, skia.TextEncoding.kUTF8, None, paint)

                canvas.drawString(
                    text,
                    UIClient._resolve_int(item['x'], context) - measurement // 2,
                    UIClient._resolve_int(item['y'], context) + font_size // 2,
                    font,
                    paint
                )
        canvas.flush()

    def handle_mouse_down(self, x: int, y: int, scene_size: Tuple[int, int]):
        context = {
            **self.persistent_context,
            'width': scene_size[0],
            'height': scene_size[1],
            'event_x': x,
            'event_y': y,
            'time': time.time()
        }
        replies = []
        for item in self.scene:
            MOUSE_DOWN_EVT = 1 << 0
            if item['type'] == 'evt_hnd' and item['events'] & MOUSE_DOWN_EVT:
                rect = (
                    UIClient._resolve_int(item['rect'][0], context),
                    UIClient._resolve_int(item['rect'][1], context),
                    UIClient._resolve_int(item['rect'][2], context),
                    UIClient._resolve_int(item['rect'][3], context)
                )
                if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                    for handler in item['handler']:
                        if handler['type'] == 'reply':
                            formatted_data = handler['id'].to_bytes(4, 'big')
                            for data in handler['data']:
                                val = UIClient._resolve_int(data, context)

                                if isinstance(val, int):
                                    formatted_data += b'\x00'
                                    formatted_data += val.to_bytes(8, 'big')
                                elif isinstance(val, float):
                                    formatted_data += b'\x01'
                                    formatted_data += struct.pack('>d', val)
                                else:
                                    raise ValueError('Invalid reply data type: {}'.format(type(val)))
                            replies.append(formatted_data)
                        elif handler['type'] == 'set_var':
                            self.persistent_context[handler['name']] = UIClient._resolve_int(handler['value'], context)

        if replies:
            self.protocol.send_packet(
                Actions.HANDLER_REPLY.to_bytes(4, 'big')
                + len(replies).to_bytes(2, 'big')
                + b''.join(((len(reply) - 4).to_bytes(2, 'big') + reply) for reply in replies)
            )


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <socket-path>")
        sys.exit(1)

    state = UIClient(sys.argv[1])
    sys.exit(main_loop(state))
