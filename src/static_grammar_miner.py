#!/usr/bin/env python

import calc_parse_
import inspect
import ast

class Seq:
    def __init__(self, seq): self.seq = seq
    def __str__(self):
        return ' '.join([str(s) for s in self.seq if str(s)])

class Star:
    def __init__(self, elt): self.elt = elt
    def __str__(self):
        if str(self.elt):
            return '(%s)*' % self.elt
        else:
            return ''

class Alt:
    def __init__(self, alts): self.alts = alts
    def __str__(self):
        s = ' | '.join([str(s) for s in self.alts if str(s)])
        if s:
            return '(%s)*' % s
        else:
            return ''

class One:
    def __init__(self, one): self.one = one
    def __str__(self):
        if str(self.one):
            return '%s' % self.one
        else:
            return ''


def transform(myast):
    if isinstance(myast, ast.While):
        return transform_while(myast)
    elif isinstance(myast, ast.If):
        return transform_if(myast)
    elif isinstance(myast, ast.Assign):
        return transform(myast.value)
    elif isinstance(myast, ast.Expr):
        return transform(myast.value)
    elif isinstance(myast, ast.List):
        return None
        #return Seq([transform(i) for i in myast.elts])
    elif isinstance(myast, ast.Tuple):
        return None
        #return Seq([transform(i) for i in myast.elts])
    elif isinstance(myast, ast.NameConstant):
        return None
    elif isinstance(myast, ast.Name):
        return One(myast.id)
    elif isinstance(myast, ast.Call):
        return transform(myast.func)
    elif isinstance(myast, ast.Num):
        return None
        #return One(myast.n)
    elif isinstance(myast, ast.BinOp):
        return Seq(transform_lst([myast.left, myast.right]))
    elif isinstance(myast, ast.Return):
        return transform(myast.value)
    elif isinstance(myast, ast.Subscript):
        return None
        #return transform(myast.value)
    elif isinstance(myast, ast.Raise):
        return None
    elif isinstance(myast, ast.Break):
        return None
    elif isinstance(myast, ast.Attribute):
        return None
        #return transform(myast.value)
    else:
        return None
        print(myast)
        #raise(Exception(myast))

def transform_if(myast):
    if_ = Seq(transform_lst(myast.body))
    else_ = Seq(transform_lst(myast.orelse))
    return Alt([if_, else_])

def transform_while(myast):
    return Star(Seq(transform_lst(myast.body)))

def transform_fn(myast):
    return Seq(transform_lst(myast.body))

def transform_lst(lst):
    result = []
    for i in lst:
        j = transform(i)
        if j:
            result.append(j)
    return result

fns = [str(i) for i in calc_parse_.__dir__() if not str(i).startswith('__')]
print(fns)
import sys
s = fns[int(sys.argv[1])]
print(s)
my_ast = ast.parse(inspect.getsource(calc_parse_.__dict__[s]))
rule = transform_fn(my_ast.body[0])
print(rule)
