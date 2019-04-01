#!/usr/bin/env python3
import json
import sys
def reconstruct_method_tree(method_map):
    first = None
    tree_map = {}
    for key in method_map:
        m_id, m_name, m_children = method_map[key]

        children = []
        if m_id in tree_map:
            # just update the name and children
            assert not tree_map[m_id]
            tree_map[m_id]['id'] = m_id
            tree_map[m_id]['name'] = m_name
            tree_map[m_id]['children'] = children
            tree_map[m_id]['indexes'] = []
        else:
            assert first is None
            tree_map[m_id] =  {'id':m_id, 'name': m_name, 'children':children, 'indexes':[]}
            first = m_id

        for c in m_children:
            assert c not in tree_map
            val = {}
            tree_map[c] = val
            children.append(val)
    return (first, tree_map)

def last_comparisons(comparisons):
    last_cmp_only = {}
    for idx, mid in comparisons:
        last_cmp_only[idx] = mid
    return last_cmp_only

def attach_comparisons(method_tree, comparisons):
    for idx in comparisons:
        mid = comparisons[idx]
        method_tree[mid]['indexes'].append(idx)

from operator import itemgetter
import itertools as it

def to_node(idxes, my_str):
    return (my_str[idxes[0]:idxes[-1]+1], [], idxes[0], idxes[-1])

def indexes_to_children(indexes, my_str):
    # return a set of one level child nodes with contiguous chars from indexes
    lst = [list(map(itemgetter(1), g)) for k, g
            in it.groupby(enumerate(indexes), lambda x:x[0]-x[1])]
    return [to_node(n, my_str) for n in lst]

import re
RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')
def tree_to_string(tree):
    def is_nonterminal(s): return re.match(RE_NONTERMINAL, s)
    symbol, children, *_ = tree
    if children: return ''.join(tree_to_string(c) for c in children)
    else: return '' if is_nonterminal(symbol) else symbol

# assumption: If a node looks
def to_tree(node, my_str):
    method_name = node['name']
    indexes = node['indexes']
    node_children = [to_tree(c, my_str) for c in node.get('children', [])]
    idx_children = indexes_to_children(indexes, my_str)
    children = sorted([c for c in node_children if c is not None] + idx_children, key=lambda x: x[2]) # assert no overlap, and order by starting index
    if not children:
        return None
    start_idx = children[0][2]
    end_idx = children[-1][3]
    return (method_name, children, start_idx, end_idx)

if __name__ == "__main__":
    with open('method_map.json') as f:
        method_map = json.load(f)

    first, method_tree = reconstruct_method_tree(method_map)
    with open('comparisons.json') as f:
        comparisons = json.load(f)

    with open('inputstr.json') as f:
        my_str = json.load(f)

    print("INPUT:", my_str)
    attach_comparisons(method_tree, last_comparisons(comparisons))
    tree = to_tree(method_tree[first], my_str)
    print("RECONSTRUCTED INPUT:", tree_to_string(tree))
    assert tree_to_string(tree) == my_str
