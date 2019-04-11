#!/usr/bin/env python
import json
import sys

def t(a): return ''.join([str(s) for s in a])
def flatten(arr): return [i for x in arr for i in (flatten(x) if isinstance(x, (list, tuple)) else [x])]

def to_string(arr): return ''.join([str_db.get(a, a) for a in arr])

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
    sys.stdout.flush()
    my_lst = []
    length = len(arr)
    # alpha_1 != e and alpha_2 != e
    if length:
        if length == 1:
            my_lst.append((arr, '%s' % ''.join(arr)))
            return my_lst
        elif length > 1:
            my_lst.append((arr, '\(%s\)' % ''.join(arr)))
        else:
            assert False
    for i in range(1,length): # shorter alpha_1 prioritized
        alpha_1 = arr[:i]
        alpha_2 = arr[i:]
        assert alpha_1
        assert alpha_2
        a1_rep = gen_rep(alpha_1)
        a2_alt = gen_alt(alpha_2)
        for a1, a1_s in a1_rep:
            for a2, a2_s in a2_alt:
                key = '\(%s\|%s\)' % (a1_s, a2_s)
                my_lst.append((a1, key))
                my_lst.append((a2, key))
    return my_lst

# returns a list.
def gen_rep(arr):
    sys.stdout.flush()
    my_lst = []
    length = len(arr)
    if length:
        if length == 1:
            my_lst.append((arr, '\(%s\)' % ''.join(arr)))
        else:
            my_lst.append((arr, '%s' % ''.join(arr)))
    for i in range(length): # shorter alpha1 prioritized
        alpha_1 = arr[:i]
        alpha_1_s = ''.join(alpha_1)
        # alpha_2 != e
        for j in (range(i+1, length+1)): # longer alpha2 prioritized
            alpha_2 = arr[i:j]
            assert alpha_2
            alpha_3 = arr[j:]
            a2_alt = gen_alt(alpha_2) # we need to check multiples 0, 1, 2.
            a3_rep = gen_rep(alpha_3)
            for n in [0, 1, 2]:
                for a2, a2_s in a2_alt:
                    if a3_rep:
                        for a3, a3_s in a3_rep:
                            my_lst.append(((alpha_1, a2 * n, a3), '\(%s%s\*%s\)' % (alpha_1_s, a2_s, a3_s)))
                            if n != 0:
                                my_lst.append(((alpha_1, a2 * n, a3), '\(%s%s\+%s\)' % (alpha_1_s, a2_s, a3_s)))
                    else:
                        my_lst.append(((alpha_1, a2 * n), '\(%s%s\*\)' % (alpha_1_s, a2_s)))
                        if n != 0:
                            my_lst.append(((alpha_1, a2 * n), '\(%s%s\+\)' % (alpha_1_s, a2_s)))
    return my_lst

str_db = {}

regex_map = {}
def main(tree_file, rule, alt):
    tree = json.load(open(tree_file))
    grammar = get_grammar(tree)
    if rule is None:
        for i, k in enumerate(grammar):
            for j,a in enumerate(grammar[k]):
                print(i,j,k, ' '.join(["%d:%s" % (i,t) for i,t in enumerate(a)]))
            print()
        return
    to_map(tree, str_db, grammar)
    #for i in str_db: print(i, str_db[i])
    sys.stdout.flush()
    # the idea is as follows: We choose a single rule to refine, and a single
    # alternative at a time.
    # Then, consider that single alternative as a sting, with each token a
    # character. Then apply regular expression synthesis to determine the
    # abstraction candiates. Place each abstraction candidate as the replacement
    # for that rule, and generate the minimum string. Evaluate and verify that
    # the string is accepted (adv: verify that the derivation tree is
    # as expected). Do this for each alternative, and we have the list of actual
    # alternatives.
    my_rule = grammar[rule]
    my_alt = sorted(my_rule)[alt]
    print(my_alt, file=sys.stderr)
    lres = gen_rep(my_alt)
    #
    sys.stdout.flush()
    for l,s in lres:
        expr = to_string(flatten(l))
        if regex_map.get(s, False):
            v = check(expr)
            regex_map[s] = v
        elif s not in regex_map:
            v = check(expr)
            regex_map[s] = v

    for k in regex_map:
        if regex_map[k]:
            print(k)
    #put it back into tree

import mingen
def to_map(tree, map_str, grammar):
    node, children, *_ = tree
    if node not in map_str and node in grammar:
        map_str[node] = mingen.all_terminals(tree)
    for c in children:
        to_map(c, map_str, grammar)
    return map_str

def get_grammar(tree): return to_grammar.to_grammar(tree, {})

import to_grammar
if __name__ == '__main__':
    main(sys.argv[1], rule=(sys.argv[2] if len(sys.argv) > 2 else None), alt=(int(sys.argv[3]) if len(sys.argv) > 3 else 0))
