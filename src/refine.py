#!/usr/bin/env python
import json
import random
import sys
import itertools

import mingen
def to_map(tree, map_str, grammar):
    node, children, *_ = tree
    if node in grammar:
        if node not in map_str:
            map_str[node] = {mingen.all_terminals(tree)}
        else:
            map_str[node].add(mingen.all_terminals(tree))

    for c in children:
        to_map(c, map_str, grammar)
    return map_str

def get_grammar(tree):
    g = to_grammar.to_grammar(tree, {})
    return {k:sorted(g[k]) for k in g}


def t(a): return ''.join([str(s) for s in a])
def flatten(arr): return [i for x in arr for i in (flatten(x) if isinstance(x, (list, tuple)) else [x])]

def tree_to_str(node, nt, expansion):
    """Reconstruct the tree replacing nt with expansion"""
    node, children, *_ = node
    if node == nt: return expansion
    else:
        if not children: return node
        else: return ''.join(tree_to_str(c, nt, expansion) for c in children)

import pudb
brk = pudb.set_trace

def to_strings(nt, regex, tree):
    """
    Given a token, and its corresponding rule, first obtain the expansion
    string by replacing all tokens with candidates, then reconstruct the string
    from the derivation tree by recursively traversing and replacing any node
    that corresponds to nt with the expanded string.
    """
    for rule in regex_to_rules(regex):
        arr = [list(str_db.get(token, [token])) for token in rule]
        for lst in itertools.product(*arr):
            expansion = ''.join(lst)
            yield tree_to_str(tree, nt, expansion)

import calc_parse_

exec_map = {}
def check(s):
    if s in exec_map:
        return exec_map[s]
    try:
        calc_parse_.parse_expr(s)
        exec_map[s] = True
        return True
    except:
        exec_map[s] = False
        return False

def gen_alt(arr):
    length = len(arr)
    # alpha_1 != e and alpha_2 != e
    for i in range(1,length): # shorter alpha_1 prioritized
        alpha_1, alpha_2 = arr[:i], arr[i:]
        assert alpha_1
        assert alpha_2
        for a1 in gen_rep(alpha_1):
            for a2 in gen_alt(alpha_2):
                yield alt(a1, a2)
    if length: # this is the final choice.
        yield arr
    return

def alt(a1, a2): return (0, a1, a2)
def rep(a): return (1, a)
def seq(*arr): return tuple([2, *arr])


def regex_to_rules(regex):
    if regex[0] == 0: # alt
        _, a, b = regex
        for a1 in regex_to_rules(a):
            yield a1
        for b1 in regex_to_rules(b):
            yield b1
    elif regex[0] == 1: # rep
        _, a = regex
        for a3 in regex_to_rules(a):
            for n in [0, 1, 2]:
                yield a3 * n
    elif regex[0] == 2: # seq
        _, *arr = regex
        if arr[0]:
            for a4 in regex_to_rules(arr[0]):
                if arr[1:]:
                    for a5 in regex_to_rules((2, *arr[1:])):
                        yield a4 + a5
                else:
                    yield a4
        else:
            for a5 in regex_to_rules((2, *arr[1:])):
                yield a5

    else:
        yield regex


def regex_to_string(regex):
    if not regex: return ''
    if len(regex) == 1: return regex[0]
    elif regex[0] == 0: # alt
        _, a, b = regex
        return "\(%s\)" % (regex_to_string(a) + '\|' + regex_to_string(b))
    elif regex[0] == 1: # rep
        _, a = regex
        return "\(%s\)" % (regex_to_string(a) + '\*')
    elif regex[0] == 2: # seq
        _, *arr = regex
        if len(arr) == 1:
            return "%s" % regex_to_string(arr[1])
        else:
            return "\(%s\)" % ''.join([regex_to_string(a) for a in arr])
    else:
        return "\(%s\)" % ''.join(regex)

def gen_rep(arr):
    length = len(arr)
    for i in range(length): # shorter alpha1 prioritized
        alpha_1 = arr[:i]
        # alpha_2 != e
        for j in range(i+1, length+1): # longer alpha2 prioritized
            alpha_2, alpha_3 = arr[i:j], arr[j:]
            assert alpha_2
            for a2 in gen_alt(alpha_2):
                for a3 in gen_rep(alpha_3):
                    yield seq(alpha_1, rep(a2), a3)
                if not alpha_3:
                    yield seq(alpha_1, rep(a2))
    if length: # the final choice
        yield arr
    return

str_db = {}
regex_map = {}
final_regex_map = {}


def process_alt(nt, my_alt, tree):
    # the idea is as follows: We choose a single nt to refine, and a single
    # alternative at a time.
    # Then, consider that single alternative as a sting, with each token a
    # character. Then apply regular expression synthesis to determine the
    # abstraction candiates. Place each abstraction candidate as the replacement
    # for that nt, and generate the minimum string. Evaluate and verify that
    # the string is accepted (adv: verify that the derivation tree is
    # as expected). Do this for each alternative, and we have the list of actual
    # alternatives.
    for regex in gen_rep(my_alt):
        all_true = False
        for expr in to_strings(nt, regex, tree):
            if regex_map.get(regex, False):
                v = check(expr)
                regex_map[regex] = v
                if not v:
                    break # one sample of regex failed. Exit
            elif regex not in regex_map:
                v = check(expr)
                regex_map[regex] = v
                if not v: break # one sample of regex failed. Exit
            all_true = True
        if all_true: # get the first
            print("nt:", nt, 'rule:', regex_to_string(regex))
            break

    for k in regex_map:
        if regex_map[k]:
            print('->        ', regex_to_string(k))
    print('')
    regex_map.clear()
    sys.stdout.flush()

def process_rule(nt, my_rule, tree):
    for alt in my_rule:
        print("->    ", alt)
        process_alt(nt, alt, tree)
    print('-'*10)
    sys.stdout.flush()

def process_grammar(grammar, tree):
    for nt in grammar:
        print("->", nt)
        my_rule = grammar[nt]
        process_rule(nt, my_rule, tree)
    sys.stdout.flush()

def main(tree_file, nt, alt):
    tree = json.load(open(tree_file))
    grammar = get_grammar(tree)
    if nt is '':
        for i, k in enumerate(grammar):
            for j,a in enumerate(grammar[k]):
                print(i,j,k, ' '.join(["%d:%s" % (i,t) for i,t in enumerate(a)]))
            print()
        return
    to_map(tree, str_db, grammar)
    sys.stdout.flush()
    #for i in str_db: print(i, str_db[i])
    process_grammar(grammar, tree)

import to_grammar
if __name__ == '__main__':
    main(sys.argv[1], nt=(sys.argv[2] if len(sys.argv) > 2 else None), alt=(int(sys.argv[3]) if len(sys.argv) > 3 else -1))
