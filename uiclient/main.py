#!/usr/bin/env python3
import json
import math
import socket
import struct
import sys
import threading
import time
from typing import Tuple, Dict

import skia

from main_loop import main_loop


class Actions:
    UPDATE_SCENE = 0
    HANDLER_REPLY = 1
    SET_VAR = 2


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
        elif packet_type == Actions.SET_VAR:
            var_name, var_type, var_value = packet.split(b'\x00')
            if var_type == b'n':
                new_value = UIClient.resolve_int(json.loads(var_value), self.ui_client.persistent_context)
            elif var_type == b's':
                new_value = UIClient.resolve_str(json.loads(var_value), self.ui_client.persistent_context)
            else:
                raise Exception('Unknown var type')
            self.ui_client.persistent_context[var_name.decode()] = new_value
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
    def resolve_str(value, context):
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            if value['type'] == 'to_str':
                return str(UIClient.resolve_int(value['a'], context))
            else:
                raise ValueError('Unknown str operation: {}'.format(value['type']))
        else:
            raise ValueError('Unknown type: {}'.format(value))

    @staticmethod
    def resolve_int(value, context):
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, dict):
            if value['type'] == 'add':
                return UIClient.resolve_int(value['a'], context) + UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'sub':
                return UIClient.resolve_int(value['a'], context) - UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'mul':
                return UIClient.resolve_int(value['a'], context) * UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'div':
                return UIClient.resolve_int(value['a'], context) // UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'mod':
                return UIClient.resolve_int(value['a'], context) % UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'pow':
                return UIClient.resolve_int(value['a'], context) ** UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'sqrt':
                return UIClient.resolve_int(value['a'], context) ** 0.5
            elif value['type'] == 'sin':
                return math.sin(UIClient.resolve_int(value['a'], context))
            elif value['type'] == 'cos':
                return math.cos(UIClient.resolve_int(value['a'], context))
            elif value['type'] == 'tan':
                return math.tan(UIClient.resolve_int(value['a'], context))
            elif value['type'] == 'neg':
                return -UIClient.resolve_int(value['a'], context)
            elif value['type'] == 'abs':
                return abs(UIClient.resolve_int(value['a'], context))
            elif value['type'] == 'min':
                return min(UIClient.resolve_int(value['a'], context), UIClient.resolve_int(value['b'], context))
            elif value['type'] == 'max':
                return max(UIClient.resolve_int(value['a'], context), UIClient.resolve_int(value['b'], context))
            elif value['type'] == 'eq':
                return UIClient.resolve_int(value['a'], context) == UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'ne':
                return UIClient.resolve_int(value['a'], context) != UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'lt':
                return UIClient.resolve_int(value['a'], context) < UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'le':
                return UIClient.resolve_int(value['a'], context) <= UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'gt':
                return UIClient.resolve_int(value['a'], context) > UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'ge':
                return UIClient.resolve_int(value['a'], context) >= UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'b_and':
                return UIClient.resolve_int(value['a'], context) & UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'b_or':
                return UIClient.resolve_int(value['a'], context) | UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'b_xor':
                return UIClient.resolve_int(value['a'], context) ^ UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'b_invert':
                return ~UIClient.resolve_int(value['a'], context)
            elif value['type'] == 'shl':
                return UIClient.resolve_int(value['a'], context) << UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'shr':
                return UIClient.resolve_int(value['a'], context) >> UIClient.resolve_int(value['b'], context)
            elif value['type'] == 'if':
                if UIClient.resolve_int(value['cond'], context):
                    return UIClient.resolve_int(value['then'], context)
                else:
                    return UIClient.resolve_int(value['else'], context)
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
                    UIClient.resolve_int(item['rect'][0], context),
                    UIClient.resolve_int(item['rect'][1], context),
                    UIClient.resolve_int(item['rect'][2], context),
                    UIClient.resolve_int(item['rect'][3], context)
                ), self._paint_from_int_color(UIClient.resolve_int(item['color'], context)))
            elif item['type'] == 'text':
                paint = self._paint_from_int_color(UIClient.resolve_int(item['color'], context))
                font_size = UIClient.resolve_int(item['fontSize'], context)
                font = skia.Font(None, font_size)
                text = UIClient.resolve_str(item['text'], context)
                measurement = font.measureText(text, skia.TextEncoding.kUTF8, None, paint)

                canvas.drawString(
                    text,
                    UIClient.resolve_int(item['x'], context) - measurement // 2,
                    UIClient.resolve_int(item['y'], context) + font_size // 2,
                    font,
                    paint
                )
        canvas.flush()

    def handle_mouse_down(self, x: int, y: int, scene_size: Tuple[int, int]):
        MOUSE_DOWN_EVT = 1 << 0
        self._handle_event_generic(x, y, {}, MOUSE_DOWN_EVT, scene_size)

    def handle_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int, scene_size: Tuple[int, int]):
        MOUSE_SCROLL_EVT = 1 << 1
        self._handle_event_generic(x, y, {
            'scroll_x': scroll_x,
            'scroll_y': scroll_y
        }, MOUSE_SCROLL_EVT, scene_size)

    def _handle_event_generic(self, x: int, y: int, extra_context: Dict, event_mask: int, scene_size: Tuple[int, int]):
        context = {
            **self.persistent_context,
            'width': scene_size[0],
            'height': scene_size[1],
            'event_x': x,
            'event_y': y,
            'time': time.time(),
            **extra_context,
        }
        replies = []
        for item in self.scene:
            if item['type'] == 'evt_hnd' and item['events'] & event_mask:
                rect = (
                    UIClient.resolve_int(item['rect'][0], context),
                    UIClient.resolve_int(item['rect'][1], context),
                    UIClient.resolve_int(item['rect'][2], context),
                    UIClient.resolve_int(item['rect'][3], context)
                )
                if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                    for handler in item['handler']:
                        if handler['type'] == 'reply':
                            formatted_data = handler['id'].to_bytes(4, 'big')
                            for data in handler['data']:
                                val = UIClient.resolve_int(data, context)

                                if isinstance(val, int):
                                    formatted_data += b'\x00'
                                    formatted_data += val.to_bytes(8, 'big', signed=True)
                                elif isinstance(val, float):
                                    formatted_data += b'\x01'
                                    formatted_data += struct.pack('>d', val)
                                else:
                                    raise ValueError('Invalid reply data type: {}'.format(type(val)))
                            replies.append(formatted_data)
                        elif handler['type'] == 'set_var':
                            self.persistent_context[handler['name']] = UIClient.resolve_int(handler['value'], context)

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
