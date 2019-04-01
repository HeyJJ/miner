#!/usr/bin/env python
import json
import sys

def to_grammar(tree, grammar):
    node, children, _, _ = tree
    tokens = []
    if node not in grammar:
        grammar["<%s>" % node] = set()
    for c in children:
        if c[1] == []:
            tokens.append(c[0])
        else:
            tokens.append("<%s>" % c[0])
            to_grammar(c, grammar)
    grammar["<%s>" % node].add(''.join(tokens))


def merge_grammar(g1, g2):
    all_keys = set(list(g1.keys()) + list(g2.keys()))
    merged = {}
    for k in all_keys:
        alts = g1.get(k, set()) | g2.get(k, set())
        merged[k] = alts
    return merged

def process(files):
    final_grammar = {}
    for fn in files:
        with open(fn) as f:
            tree = json.load(f)[1][0]
        g = {}
        to_grammar(tree, g)
        final_grammar = merge_grammar(final_grammar, g)
    return {k:[a for a in v] for k,v in final_grammar.items()}

g = process(sys.argv[1:])
print(g)
