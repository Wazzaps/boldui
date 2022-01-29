#!/usr/bin/env python3
"""
Visualize each opcode in the scene graph as a graph using graphviz.
"""
import json
import sys
import textwrap

from anytree import Node
from anytree.exporter import UniqueDotExporter


COUNTER = 0
EXPECTED_NODES = 243350


def categorize_attrs(obj):
    plain_attrs = {}
    big_attrs = {}
    subtree_attrs = []

    if isinstance(obj, dict):
        keys = obj
    elif isinstance(obj, list):
        keys = range(len(obj))
    else:
        assert False, f'Unknown type: {type(obj)}'

    for attr in keys:
        if attr == 'type':
            continue
        if (isinstance(obj[attr], dict) and 'type' in obj[attr]) or isinstance(obj[attr], list):
            subtree_attrs.append(attr)
        else:
            attr_repr = repr(obj[attr])
            if len(attr_repr) > 50:
                big_attrs[attr] = attr_repr[:1000]
                if len(attr_repr) > 1000:
                    big_attrs[attr] += '...'
            else:
                plain_attrs[attr] = attr_repr

    return plain_attrs, big_attrs, subtree_attrs


def render_attrs(attrs):
    output = []

    for attr in attrs:
        output.append(f'{attr}: {attrs[attr]}')

    if output:
        return '<BR /><FONT POINT-SIZE="9">' + '<BR />'.join(output) + '</FONT>'
    else:
        return ''


def create_subnodes(node, big_attrs, parent_data, subtree_attrs):
    global COUNTER

    for attr in subtree_attrs:
        current_node = parent_data[attr]
        child_plain_attrs, child_big_attrs, child_subtree_attrs = categorize_attrs(current_node)

        if isinstance(current_node, dict):
            prefix = current_node["type"]
            COUNTER += 1
            if COUNTER % 1000 == 0:
                print(f'{COUNTER}/{EXPECTED_NODES} ({float(COUNTER) / EXPECTED_NODES * 100:.2f}%)')
        else:
            prefix = '(list)'

        subnode = Node(
            f'{prefix}{render_attrs(child_plain_attrs)}',
            attr_name=attr,
            parent=node
        )
        create_subnodes(subnode, child_big_attrs, current_node, child_subtree_attrs)

    for attr, attr_val in big_attrs.items():
        wrapped = '<BR />'.join(textwrap.wrap(attr_val, width=50))
        if not wrapped:
            wrapped = '(empty)'
        _subnode = Node(
            f'<FONT POINT-SIZE="9">{wrapped}</FONT>',
            attr_name=attr,
            parent=node
        )


def visualize(json_file):
    json_data = json.load(open(json_file, 'r'))
    for i, node in enumerate(json_data):
        # for i in range(1):
        plain_attrs, big_attrs, subtree_attrs = categorize_attrs(node)

        root = Node(f'Ops.{node["type"]}{render_attrs(plain_attrs)}', attr_name='')
        create_subnodes(root, big_attrs, node, subtree_attrs)

        UniqueDotExporter(root, nodeattrfunc=lambda n: 'label=<%s>, xlabel=<%s>' % (n.name, n.attr_name)).to_picture(f'scene_op_{i}.png')


def main():
    if len(sys.argv) != 2:
        print("Usage: python visualize_scene_graph.py <json_file>")
        sys.exit(1)

    visualize(sys.argv[1])


if __name__ == '__main__':
    main()
