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
    WATCH_ACK = 3


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
        # print('Sending packet:', packet)
        self.socket.send(len(packet).to_bytes(4, 'big') + packet)

    def _handle_packet(self, packet):
        packet_type = int.from_bytes(packet[:4], 'big')
        packet = packet[4:]

        def set_vars_from_list(parts):
            while parts:
                var_name, var_type, var_value = parts[:3]
                parts = parts[3:]

                if type(var_name) == bytes:
                    var_name = var_name.decode()

                if type(var_type) == str:
                    var_type = bytes(var_type, 'utf-8')

                # FIXME: remove when variables get static types
                new_value = UIClient.resolve_oplist(json.loads(var_value), self.ui_client.context)[-1]
                if var_type == b'n':
                    new_value = float(new_value)
                elif var_type == b's':
                    new_value = str(new_value)
                else:
                    raise Exception('Unknown var type: {}'.format(var_type))

                print(f'{var_name}:{var_type} = {var_value}')
                self.ui_client.persistent_context[var_name] = new_value
            self.ui_client._should_update_watches = True
            self.ui_client.update_watches(send=True)

        if packet_type == Actions.UPDATE_SCENE:
            open('scene.json', 'wb').write(packet)

            self.ui_client.scene = json.loads(packet)
            if 'vars' in self.ui_client.scene and self.ui_client.scene['vars']:
                set_vars_from_list(self.ui_client.scene['vars'])

            self.ui_client._blocked_watches.clear()
            self.ui_client._should_update_watches = True
            self.ui_client.update_watches(send=True)
        elif packet_type == Actions.SET_VAR:
            if packet:
                parts = packet.split(b'\x00')
                set_vars_from_list(parts)
        elif packet_type == Actions.WATCH_ACK:
            ack_id = int.from_bytes(packet[:8], 'big')
            # print(f'Watch ack #{ack_id}')
            self.ui_client.ack_watch(ack_id)
        else:
            print('[client] Unknown packet type:', packet)


class UIClient:
    WATCH_RECURSION = 3
    _text_measurement_cache = {}
    _font_cache = {}

    def __init__(self, address):
        self.scene = {
            'oplist': [0xff202020],
            'scene': [
                {'type': 'clear', 'color': 0},
            ]
        }
        self.event_handlers = []
        self.protocol = Protocol(address, self)
        self.persistent_context = {}
        self._should_update_watches = False
        self._blocked_watches = set()
        self.width = 0
        self.height = 0
        self.image_cache = {}
        self._start_time = time.time()

        self.protocol.connect()

    @staticmethod
    def _paint_from_int_color(color):
        return skia.Paint(
            Color=skia.Color(
                (color >> 16) & 0xff,
                (color >> 8) & 0xff,
                color & 0xff,
                (color >> 24) & 0xff
            ),
            AntiAlias=True,
        )

    @staticmethod
    def measure_text(text, font_size) -> (float, float):
        font_name = 'Cantarell'
        key = f'{font_name}:{font_size}:{text}'

        if key in UIClient._text_measurement_cache:
            return UIClient._text_measurement_cache[key]

        paint = UIClient._paint_from_int_color(0xffffffff)
        font = UIClient.get_font(font_name, font_size)
        bounds = skia.Rect()
        font.measureText(text, skia.TextEncoding.kUTF8, bounds, paint)
        UIClient._text_measurement_cache[key] = (bounds.width(), font_size)

        return UIClient._text_measurement_cache[key]

    @staticmethod
    def get_font(font_name, font_size):
        key = f'{font_name}:{font_size}'

        if key in UIClient._font_cache:
            return UIClient._font_cache[key]

        UIClient._font_cache[key] = skia.Font(skia.Typeface(font_name), font_size)
        return UIClient._font_cache[key]

    @staticmethod
    def resolve_op(value, op_results, context):
        if value is None:
            return 0
        elif isinstance(value, (int, float, str)):
            return value
        elif isinstance(value, dict):
            if value['type'] == 'add':
                return op_results[value['a']] + op_results[value['b']]
            elif value['type'] == 'sub':
                return op_results[value['a']] - op_results[value['b']]
            elif value['type'] == 'mul':
                return op_results[value['a']] * op_results[value['b']]
            elif value['type'] == 'div':
                return op_results[value['a']] / op_results[value['b']]
            elif value['type'] == 'fdiv':
                return op_results[value['a']] // op_results[value['b']]
            elif value['type'] == 'mod':
                return op_results[value['a']] % op_results[value['b']]
            elif value['type'] == 'pow':
                return op_results[value['a']] ** op_results[value['b']]
            elif value['type'] == 'sqrt':
                return op_results[value['a']] ** 0.5
            elif value['type'] == 'sin':
                return math.sin(op_results[value['a']])
            elif value['type'] == 'cos':
                return math.cos(op_results[value['a']])
            elif value['type'] == 'tan':
                return math.tan(op_results[value['a']])
            elif value['type'] == 'neg':
                return -op_results[value['a']]
            elif value['type'] == 'abs':
                return abs(op_results[value['a']])
            elif value['type'] == 'min':
                return min(op_results[value['a']], op_results[value['b']])
            elif value['type'] == 'max':
                return max(op_results[value['a']], op_results[value['b']])
            elif value['type'] == 'eq':
                return op_results[value['a']] == op_results[value['b']]
            elif value['type'] == 'ne':
                return op_results[value['a']] != op_results[value['b']]
            elif value['type'] == 'lt':
                return op_results[value['a']] < op_results[value['b']]
            elif value['type'] == 'le':
                return op_results[value['a']] <= op_results[value['b']]
            elif value['type'] == 'gt':
                return op_results[value['a']] > op_results[value['b']]
            elif value['type'] == 'ge':
                return op_results[value['a']] >= op_results[value['b']]
            elif value['type'] == 'bAnd':
                return op_results[value['a']] & op_results[value['b']]
            elif value['type'] == 'bOr':
                return op_results[value['a']] | op_results[value['b']]
            elif value['type'] == 'bXor':
                return op_results[value['a']] ^ op_results[value['b']]
            elif value['type'] == 'bInvert':
                return ~op_results[value['a']]
            elif value['type'] == 'shl':
                return op_results[value['a']] << op_results[value['b']]
            elif value['type'] == 'shr':
                return op_results[value['a']] >> op_results[value['b']]
            elif value['type'] == 'min':
                return min(op_results[value['a']], op_results[value['b']])
            elif value['type'] == 'max':
                return max(op_results[value['a']], op_results[value['b']])
            elif value['type'] == 'inf':
                return float('inf')
            elif value['type'] == 'measureTextX':
                font_size = op_results[value['fontSize']]
                text = op_results[value['text']]
                return UIClient.measure_text(text, font_size)[0]
            elif value['type'] == 'measureTextY':
                font_size = op_results[value['fontSize']]
                text = op_results[value['text']]
                return UIClient.measure_text(text, font_size)[1]
            elif value['type'] == 'if':
                if op_results[value['cond']]:
                    return op_results[value['t']]
                else:
                    return op_results[value['f']]
            elif value['type'] == 'toStr':
                return str(op_results[value['a']])
            elif value['type'] == 'var':
                return context.get(value['name'], 0)
            else:
                raise ValueError('Unknown operation: {}'.format(value['type']))
        else:
            raise ValueError('Unknown type: {}'.format(value))

    @staticmethod
    def resolve_oplist(oplist, context):
        op_results = []
        for op in oplist:
            op_results.append(UIClient.resolve_op(op, op_results, context))
        return op_results

    @property
    def context(self):
        return {
            **self.persistent_context,
            'width': self.width,
            'height': self.height,
            'time': time.time() - self._start_time,
        }

    def resize(self, width, height):
        self.width = width
        self.height = height
        self._should_update_watches = True
        self.update_watches(send=True)

    def draw(self, canvas: skia.Canvas) -> None:
        context = self.context
        canvas.save()
        canvas.clear(0xff000000)

        new_event_handlers = []

        op_results = UIClient.resolve_oplist(self.scene['oplist'], context)

        for item in self.scene['scene']:
            if item['type'] == 'clear':
                canvas.clear(item['color'])
            elif item['type'] == 'rect':
                canvas.drawRect(skia.Rect(
                    op_results[item['rect'][0]],
                    op_results[item['rect'][1]],
                    op_results[item['rect'][2]],
                    op_results[item['rect'][3]]
                ), self._paint_from_int_color(op_results[item['color']]))
            elif item['type'] == 'rrect':
                canvas.drawRRect(skia.RRect(
                    skia.Rect(
                        op_results[item['rect'][0]],
                        op_results[item['rect'][1]],
                        op_results[item['rect'][2]],
                        op_results[item['rect'][3]],
                    ),
                    op_results[item['radius']],
                    op_results[item['radius']],
                ), self._paint_from_int_color(op_results[item['color']]))
            elif item['type'] == 'save':
                canvas.save()
            elif item['type'] == 'restore':
                canvas.restore()
            elif item['type'] == 'clipRect':
                canvas.clipRect(skia.Rect(
                    op_results[item['rect'][0]],
                    op_results[item['rect'][1]],
                    op_results[item['rect'][2]],
                    op_results[item['rect'][3]]
                ))
            elif item['type'] == 'text':
                paint = self._paint_from_int_color(op_results[item['color']])
                font_size = op_results[item['fontSize']]
                font = UIClient.get_font('Cantarell', font_size)
                text = op_results[item['text']]
                measurement = font.measureText(text, skia.TextEncoding.kUTF8, None, paint)

                canvas.drawString(
                    text,
                    # TODO: Add alignment parameter
                    op_results[item['x']] - measurement // 2,
                    op_results[item['y']] + font_size // 2,
                    font,
                    paint
                )
            elif item['type'] == 'image':
                rect = (
                    op_results[item['rect'][0]],
                    op_results[item['rect'][1]],
                    op_results[item['rect'][2]],
                    op_results[item['rect'][3]],
                )
                # width, height = rect[2] - rect[0], rect[3] - rect[1]
                if item['uri'] not in self.image_cache:
                    image = skia.Image.open(item['uri'])
                    # image = image.resize(width, height)
                    image = image.convert(alphaType=skia.kUnpremul_AlphaType)
                    self.image_cache[item['uri']] = image

                canvas.drawImageRect(
                    image=self.image_cache[item['uri']],
                    dst=skia.Rect(rect[0], rect[1], rect[2], rect[3]),
                )
                # canvas.drawRect(
                #     rect=skia.Rect(rect[0] + 100, rect[1] + 100, rect[2] - 100, rect[3] - 100),
                #     paint=skia.Paint(
                #         Color=0xa0000000,
                #         ImageFilter=skia.ImageFilters.Blur(32.0, 32.0, tileMode=skia.TileMode.kClamp),
                #     ),
                # )
            elif item['type'] == 'evtHnd':
                rect = (
                    op_results[item['rect'][0]],
                    op_results[item['rect'][1]],
                    op_results[item['rect'][2]],
                    op_results[item['rect'][3]],
                )
                new_event_handlers.append({
                    'rect': rect,
                    'events': item['events'],
                    'handler': item['handler'],
                    'oplist': item['oplist'],
                })

        self.event_handlers = new_event_handlers
        canvas.restore()

    def handle_mouse_down(self, x: int, y: int):
        MOUSE_DOWN_EVT = 1 << 0
        self._handle_event_generic(x, y, {}, MOUSE_DOWN_EVT)

    def handle_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        MOUSE_SCROLL_EVT = 1 << 1
        self._handle_event_generic(x, y, {
            'scroll_x': scroll_x,
            'scroll_y': scroll_y
        }, MOUSE_SCROLL_EVT)

    def _eval_handlers(self, handlers, op_results):
        replies = []
        for handler in handlers:
            if handler['type'] == 'reply':
                formatted_data = handler['id'].to_bytes(4, 'big')
                for data in handler['data']:
                    val = op_results[data]

                    if isinstance(val, int):
                        formatted_data += b'\x00'
                        formatted_data += val.to_bytes(8, 'big', signed=True)
                    elif isinstance(val, float):
                        formatted_data += b'\x01'
                        formatted_data += struct.pack('>d', val)
                    else:
                        raise ValueError('Invalid reply data type: {}'.format(type(val)))
                replies.append(formatted_data)
            elif handler['type'] == 'setVar':
                self.persistent_context[handler['name']] = op_results[handler['value']]
                self._should_update_watches = True
                replies += self.update_watches()
        return replies

    def _send_replies(self, replies):
        self.protocol.send_packet(
            Actions.HANDLER_REPLY.to_bytes(4, 'big')
            + len(replies).to_bytes(2, 'big')
            + b''.join(((len(reply) - 4).to_bytes(2, 'big') + reply) for reply in replies)
        )

    def _handle_event_generic(self, x: int, y: int, extra_context: Dict, event_mask: int):
        context = {
            **self.context,
            'event_x': x,
            'event_y': y,
            **extra_context,
        }
        replies = []
        for handler in self.event_handlers:
            if handler['events'] & event_mask and \
                    handler['rect'][0] <= x <= handler['rect'][2] and handler['rect'][1] <= y <= handler['rect'][3]:
                op_results = UIClient.resolve_oplist(handler['oplist'], context)
                replies += self._eval_handlers(handler['handler'], op_results)

        replies += self.update_watches()

        if replies:
            self._send_replies(replies)

    def update_watches(self, send=False):
        replies = []
        context = self.context
        for _ in range(UIClient.WATCH_RECURSION):
            if self._should_update_watches:
                self._should_update_watches = False
                op_results = UIClient.resolve_oplist(self.scene['oplist'], context)
                for op in self.scene['scene']:
                    if op['type'] == 'watch':
                        if op['id'] not in self._blocked_watches:
                            if op_results[op['cond']]:
                                replies += self._eval_handlers(op['handler'], op_results)
                                if op['waitForRoundtrip']:
                                    self._blocked_watches.add(op['id'])
            else:
                break

        if send:
            self._send_replies(replies)
        else:
            return replies

    def ack_watch(self, ack_id: int):
        if ack_id in self._blocked_watches:
            self._blocked_watches.remove(ack_id)
        self.update_watches(send=True)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <socket-path>")
        sys.exit(1)

    state = UIClient(sys.argv[1])
    sys.exit(main_loop(state))
