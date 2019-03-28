#!/usr/bin/env python3

import string
import re
RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')

CSV_GRAMMAR = {
    '<start>' : ['<csvline>'],
    '<csvline>': ['<items>'],
    '<items>' :  ['<item>,<items>', '<item>'],
    '<item>' : ['<letters>'],
    '<letters>': ['<letter><letters>', '<letter>'],
    '<letter>' : list(string.ascii_letters + string.digits + string.punctuation + ' \t\n')
}


import copy

import random

def parse_csv(mystring):
    children = []
    tree = (START_SYMBOL, children)
    for i,line in enumerate(mystring.split('\n')):
        children.append(("record %d" %i, [(cell,[]) for cell in line.split(',')]))
    return tree

def lr_graph(dot):
    dot.attr('node', shape='plain')
    dot.graph_attr['rankdir'] = 'LR'

def parse_quote(string, i):
    v = string[i+1:].find('"')
    return v+i+1 if v >= 0 else -1
    
def find_comma(string, i):
    slen = len(string)
    while i < slen:
        if string[i] == '"':
            i = parse_quote(string, i)
            if i == -1:
                return -1
        if string[i] == ',':
            return i
        i+=1
    return -1
        
def comma_split(string):
    slen = len(string)
    i = 0
    while i < slen:
        c = find_comma(string, i)
        if c == -1:
            yield string[i:]
            return
        else:
            yield string[i:c]
        i = c+1

def parse_csv(mystring):
    children = []
    tree = (START_SYMBOL, children)
    for i,line in enumerate(mystring.split('\n')):
        children.append(("record %d" %i, [(cell,[]) for cell in comma_split(line)]))
    return tree


A1_GRAMMAR = {
    "<start>": ["<expr>"],
    "<expr>": ["<expr>+<expr>", "<expr>-<expr>", "<integer>"],
    "<integer>": ["<digit><integer>", "<digit>"],
    "<digit>": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
}


A2_GRAMMAR = {
    "<start>": ["<expr>"],
    "<expr>": ["<integer><expr_>"],
    "<expr_>": ["+<expr>", "-<expr>", ""],
    "<integer>": ["<digit><integer_>"],
    "<integer_>": ["<integer>", ""],
    "<digit>": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
}


LR_GRAMMAR = {
    '<start>': ['<A>'],
    '<A>': ['<A>a', ''],
}

RR_GRAMMAR = {
    '<start>': ['<A>'],
    '<A>': ['a<A>', ''],
}


class Parser(object):
    def __init__(self, grammar, **kwargs):
        self._grammar = grammar
        self._start_symbol = kwargs.get('start_symbol', default=START_SYMBOL)
        self.log = kwargs.get('log', default=False)
        self.coalesce = kwargs.get('coalesce', default=True)
        self.tokens = kwargs.get('tokens', default=set())

    def grammar(self):
        return self._grammar

    def start_symbol(self):
        return self._start_symbol

    def parse_prefix(self, text):
        """Return pair (cursor, forest) for longest prefix of text"""
        raise NotImplemented()

    def parse(self, text):
        cursor, forest = self.parse_prefix(text)
        if cursor < len(text):
            raise SyntaxError("at " + repr(text[cursor:]))
        return [self.prune_tree(tree) for tree in forest]
    
    def coalesce(self, children):
        last = ''
        new_lst = []
        for cn, cc in children:
            if cn not in self._grammar:
                last += cn
            else:
                if last:
                    new_lst.append((last, []))
                    last = ''
                new_lst.append((cn, cc))
        if last:
            new_lst.append((last, []))
        return new_lst
                
    def prune_tree(self, tree):
        name, children = tree
        if self.coalesce:
            children = self.coalesce(children)
        if name in self.tokens:
            return (name, [(tree_to_string(tree), [])])
        else:
            return (name, [self.prune_tree(c) for c in children])

PEG1 = {
    '<start>': ['a', 'b']
}

PEG2 = {
    '<start>': ['ab', 'abc']
}

import re

def canonical(grammar, letters=False):
    def split(expansion):
        if isinstance(expansion, tuple):
            expansion = expansion[0]

        return [token for token in re.split(RE_NONTERMINAL, expansion) if token]

    def tokenize(word):
        return list(word) if letters else [word]

    def canonical_expr(expression):
        return [
            token for word in split(expression)
            for token in ([word] if word in grammar else tokenize(word))
        ]

    return {
        k: [canonical_expr(expression) for expression in alternatives]
        for k, alternatives in grammar.items()
    }

class Parser(Parser):
    def __init__(self, grammar, **kwargs):
        self._grammar = grammar
        self._start_symbol = kwargs.get('start_symbol', START_SYMBOL)
        self.log = kwargs.get('log') or False
        self.tokens = kwargs.get('tokens') or set()
        self.cgrammar = canonical(grammar)


class PEGParser(Parser):
    def parse_prefix(self, text):
        cursor, tree = self.unify_key(self.start_symbol(), text, 0)
        return cursor, [tree]

    def unify_key(self, key, text, at=0):
        if self.log:
            print("unify_key: %s with %s" % (repr(key), repr(text[at:])))
        if key not in self.cgrammar:
            if text[at:].startswith(key):
                return at + len(key), (key, [])
            else:
                return at, None
        for rule in self.cgrammar[key]:
            to, res = self.unify_rule(rule, text, at)
            if res:
                return (to, (key, res))
        return 0, None

    def unify_rule(self, rule, text, at):
        if self.log:
            print('unify_rule: %s with %s' % (repr(rule), repr(text[at:])))
        results = []
        for token in rule:
            at, res = self.unify_key(token, text, at)
            if res is None:
                return at, None
            results.append(res)
        return at, results

from functools import lru_cache

class PEGParser(PEGParser):
    @lru_cache(maxsize=None)
    def unify_key(self, key, text, at=0):
        if key not in self.cgrammar:
            if text[at:].startswith(key):
                return at + len(key), (key, [])
            else:
                return at, None
        for rule in self.cgrammar[key]:
            to, res = self.unify_rule(rule, text, at)
            if res:
                return (to, (key, res))
        return 0, None


def crange(character_start, character_end):
    return [chr(i)
            for i in range(ord(character_start), ord(character_end) + 1)]
VAR_GRAMMAR = {
    '<start>': ['<statements>'],
    '<statements>': ['<statement>;<statements>', '<statement>'],
    '<statement>': ['<assignment>'],
    '<assignment>': ['<identifier>=<expr>'],
    '<identifier>': ['<word>'],
    '<word>': ['<alpha><word>', '<alpha>'],
    '<alpha>': list(string.ascii_letters),
    '<expr>': ['<term>+<expr>', '<term>-<expr>', '<term>'],
    '<term>': ['<factor>*<term>', '<factor>/<term>', '<factor>'],
    '<factor>':
    ['+<factor>', '-<factor>', '(<expr>)', '<identifier>', '<number>'],
    '<number>': ['<integer>.<integer>', '<integer>'],
    '<integer>': ['<digit><integer>', '<digit>'],
    '<digit>': crange('0', '9')
}

VAR_TOKENS = {'<number>', '<identifier>'}
