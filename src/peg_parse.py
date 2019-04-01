import Tracer

import re
RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')

def canonical(grammar, letters=False):
    def split(expansion):
        if isinstance(expansion, tuple): expansion = expansion[0]
        return [token for token in re.split(RE_NONTERMINAL, expansion) if token]
    def tokenize(word): return list(word) if letters else [word]
    def canonical_expr(expression):
        return [token for word in split(expression)
            for token in ([word] if word in grammar else tokenize(word))]
    return {k: [canonical_expr(expression) for expression in alternatives]
        for k, alternatives in grammar.items()}

def crange(character_start, character_end):
    return [chr(i) for i in range(ord(character_start), ord(character_end) + 1)]

def unify_key(grammar, key, text, at=0):
    if key not in grammar:
        if text[at:].startswith(key):
            return at + len(key), (key, [])
        else:
            return at, None
    for rule in grammar[key]:
        to, res = unify_rule(grammar, rule, text, at)
        if res:
            return (to, (key, res))
    return 0, None

def unify_rule(grammar, rule, text, at):
    results = []
    for token in rule:
        at, res = unify_key(grammar, token, text, at)
        if res is None:
            return at, None
        results.append(res)
    return at, results

import string
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

import json
import sys
if __name__ == "__main__":
    mystring = sys.argv[1] #'a=1'
    #mystring = 'avar=1.3;bvar=avar-3*(4+300)'
    C_VG = canonical(VAR_GRAMMAR)
    restrict = {'methods':['unify_key', 'unify_rule']}
    #mystring = 'avar=1.3;bvar=avar-3*(4+300)'
    #mystring = 'av=1' #.3;bvar=avar-3*(4+300)'
    with Tracer.Tracer(mystring, restrict) as tracer:
        unify_key(C_VG, '<start>', tracer())
    assert tracer.inputstr.comparisons
    with open('comparisons.json', 'w+') as f:
        f.write(json.dumps(Tracer.convert_comparisons(tracer.inputstr.comparisons)))
    with open('method_map.json', 'w+') as f:
        f.write(json.dumps(Tracer.convert_method_map(tracer.method_map)))
    with open('inputstr.json', 'w+') as f:
        f.write(json.dumps(str(tracer.inputstr)))
