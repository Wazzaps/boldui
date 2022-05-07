#!/usr/bin/env python3
"""
Visualize each opcode in the scene graph as a graph using graphviz.
"""
import json
import sys

from graphviz import Digraph


def visualize(json_file):
    json_data = json.load(open(json_file, 'r'))
    dot = Digraph(graph_attr={'splines': 'ortho'})

    dot.node('root', 'Scene', color='purple', fontcolor='purple')

    for i, op in enumerate(json_data["oplist"]):
        if type(op) == dict:
            attrs = {}
            for attr in op:
                if attr == 'type':
                    continue
                if type(op[attr]) == str:
                    attrs[attr] = repr(op[attr])

            nodetext = f'OP{i}: {op["type"]}'
            if attrs:
                nodetext += f'<BR /><FONT POINT-SIZE="10">' \
                            f'{"<BR />".join(f"{attr}: {attrs[attr]}" for attr in attrs)}' \
                            f'</FONT>'
            dot.node(f'op-{i}', f'<{nodetext}>')

            for attr in op:
                if attr == 'type':
                    continue
                if type(op[attr]) == int:
                    dot.edge(f'op-{op[attr]}', f'op-{i}', headlabel=f' {attr} ', minlen='2')
        else:
            op_repr = repr(op)
            if type(op) == int and op >= 0x1000:
                op_repr = hex(op)

            dot.node(f'op-{i}', f'OP{i}: {op_repr}', color='blue', fontcolor='blue')

    for i, op in enumerate(json_data["scene"]):
        attrs = {}

        def handle_attrs1(obj):
            for attr in obj:
                if attr == 'type':
                    continue
                elif op['type'] == 'clear' and attr == 'color':
                    attrs[attr] = hex(op[attr])
                elif op['type'] == 'evtHnd' and attr == 'events':
                    attrs[attr] = hex(op[attr])
                elif type(op[attr]) == str:
                    attrs[attr] = repr(op[attr])

        handle_attrs1(op)

        nodetext = f'SCN{i}: {op["type"]}'
        if attrs:
            nodetext += f'<BR /><FONT POINT-SIZE="10">' \
                        f'{"<BR />".join(f"{attr}: {attrs[attr]}" for attr in attrs)}' \
                        f'</FONT>'

        dot.node(f'scn-{i}', f'<{nodetext}>', color='red', fontcolor='red')
        dot.edge(f'scn-{i}', 'root', minlen='2')

        def handle_attrs2(obj):
            for attr in obj:
                if attr == 'type':
                    continue
                if obj['type'] == 'clear' and attr == 'color':
                    continue
                if obj['type'] == 'evtHnd' and attr == 'events':
                    continue
                if type(obj[attr]) == int:
                    dot.edge(f'op-{obj[attr]}', f'scn-{i}', headlabel=f' {attr} ', minlen='2')
                if type(obj[attr]) == list:
                    for j, entry in enumerate(obj[attr]):
                        handle_attrs2({f'{attr}.{j}': entry, 'type': ''})

        handle_attrs2(op)

    dot.render(view=True, engine='dot')


def main():
    if len(sys.argv) != 2:
        print("Usage: python visualize_scene_graph.py <json_file>")
        sys.exit(1)

    visualize(sys.argv[1])


if __name__ == '__main__':
    main()
