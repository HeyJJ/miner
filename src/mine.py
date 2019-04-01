#!/usr/bin/env python3
import json
# Given a child id, we can retrieve the parent id
# parent_map[childid] == parent_id
def to_parent_map(method_map):
    parent_map = {}
    for i in method_map:
        mid, _method, children = method_map[i]
        for cmid in children:
            parent_map[cmid] = mid
    return parent_map

# name,stack,children,idxs
def new_node(s, mid=None):
    return {'sym': s,'id': mid,'children': []}

def add_indexes(node, indexes):
    for i in indexes:
        n = new_node(i)
        node['children'].append(n)

def get_last_comparison_on_index(trace, inputstr):
    last_cmp_only = {}
    for idx, mid in trace:
        last_cmp_only[idx] = (idx, mid)

    res = []
    for x in last_cmp_only.values():
        idx, mid = x
        c = inputstr[idx]
        res.append((c, mid))
    print()
    return res

def parse_trees(trace_comparisons, inputstr, method_map):
    last_cmp_only = get_last_comparison_on_index(trace_comparisons, inputstr)
    parent_map = to_parent_map(method_map)

    root = new_node("<%s>" % 'start', mid=0)
    method_stack = [root]
    method_stack_map = {s['id'] for s in method_stack}
    
    # idx, m_name, stack_len, mid
    for cur_char, mid in last_cmp_only:
        #print("%2d" % idx, repr(inputstr[idx]), '  |' * stack_len, m_name, mid, "(%d)" % stack_len)
        current = method_stack[-1]
        # look back until we have a parent that is in method_stack_map
        parent_mid = mid
        parents = [parent_mid]

        # look for any parent that is in the stack so we can budd off
        # from that point
        while parent_mid not in method_stack_map:
            parent_mid = parent_map[parent_mid]
            parents.insert(0, parent_mid)
        # at this point, we have found a common parent. Now, pop off the
        # stack so that we reach the common parent.

        common_parent = parents[0]

        # pop off the method_stack until we come to the parents[0]
        while common_parent != method_stack[-1]['id']:
            v = method_stack.pop()
            method_stack_map.remove(v['id'])

        # now start appending until we reach mid
        # note that we also append a node with mid
        for elt in parents[1:]:
            # e_mid, e_method, _e_children
            e_mid, e_method, _ = method_map[str(elt)]
            idxs = [] if e_mid != mid else [cur_char]
            node = new_node("<%s>" % e_method, mid=elt)
            add_indexes(node, idxs)
            method_stack[-1]['children'].append(node)
            method_stack.append(node)
            method_stack_map.add(node['id'])

    return root

def to_tree(node, my_str):
    sym = node['sym']
    children = node.get('children')
    if children: return (sym, [to_tree(c, my_str) for c in children])
    else: return (sym, [])

import re
RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')
def tree_to_string(tree):
    def is_nonterminal(s): return re.match(RE_NONTERMINAL, s)
    symbol, children, *_ = tree
    if children: return ''.join(tree_to_string(c) for c in children)
    else: return '' if is_nonterminal(symbol) else symbol

if __name__ == "__main__":
    with open('comparisons.json') as f:
        comparisons = json.load(f)
    with open('inputstr.json') as f:
        inputstr = json.load(f)
    with open('method_map.json') as f:
        method_map = json.load(f)
    my_root = parse_trees(comparisons, str(inputstr), method_map)
    #print(my_root)
    tree = to_tree(my_root, inputstr)
    print(tree)
    print(tree_to_string(tree))
    assert tree_to_string(tree) == inputstr
    print()
    print(tree_to_string(tree))
