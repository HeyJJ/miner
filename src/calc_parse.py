#!/usr/bin/env python3
import string
from helpers import scope
def parse_num(s,i):
    n = ''
    while s[i:] and s[i].in_(list(string.digits)):
        with scope('while_1', 0):
            n += s[i]
            i = i +1
    return i,n

def parse_paren(s, i):
    assert s[i] == '('
    i, v = parse_expr(s, i+1)
    if s[i:] == '':
        with scope('if_0', 0):
            raise Exception(s, i)
    assert s[i] == ')'
    return i+1, v


def parse_expr(s, i = 0):
    expr = []
    while s[i:]:
        with scope('while_2', 0):
            c = s[i]
            if c.in_(list(string.digits)):
                with scope('if_1', 0):
                    i,num = parse_num(s,i)
                    expr.append(num)
            elif c.in_(['+', '-', '*', '/']):
                with scope('if_1', 1):
                    expr.append(c)
                    i = i + 1
            elif c == '(':
                with scope('if_1', 2):
                    i, cexpr = parse_paren(s, i)
                    expr.append(cexpr)
            elif c == ')':
                with scope('if_1', 3):
                    return i, expr
            else:
                with scope('if_1', 4):
                    raise Exception(s,i)
    return i, expr

import json
import sys
import Tracer
if __name__ == "__main__":
    mystring = sys.argv[1] if len(sys.argv) > 1 else "(25-1/(2+3))*100/3"
    restrict = {'methods':['parse_num', 'parse_paren', 'parse_expr']}
    with Tracer.Tracer(mystring, restrict) as tracer:
        parse_expr(tracer())
    assert tracer.inputstr.comparisons
    print(json.dumps({
        'comparisons':Tracer.convert_comparisons(tracer.inputstr.comparisons),
        'method_map': Tracer.convert_method_map(tracer.method_map),
        'inputstr': str(tracer.inputstr)}))
