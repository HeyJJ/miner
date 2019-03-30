import sys
import string
import json
import re
RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')
from InformationFlow import ctstr

CURRENT_METHOD = None

def get_current_method():
    return CURRENT_METHOD

def set_current_method(method, stack_depth, mid):
    global CURRENT_METHOD
    CURRENT_METHOD = (method, stack_depth, mid)
    return CURRENT_METHOD

class xtstr(ctstr):
    def add_instr(self, op, c_a, c_b):
        ct = None
        if len(c_a) == 1 and isinstance(c_a, xtstr):
            ct = c_a.taint[0]
        elif len(c_b) == 1 and isinstance(c_b, xtstr):
            ct = c_b.taint[0]
        m = get_current_method()
        #print(repr(m))
        self.comparisons.append((ct, m))

    def create(self, res, taint):
        o = xtstr(res, taint, self)
        o.comparisons = self.comparisons
        return o

class Context:
    def __init__(self, frame, track_caller=True):
        self.method = self._method(frame)
        self.parameter_names = self._get_parameters(frame)
        self.file_name = self._file_name(frame)
        self.parent = Context(frame.f_back, False) if track_caller and frame.f_back else None

    def _get_parameters(self, frame):
        return [frame.f_code.co_varnames[i] for i in range(frame.f_code.co_argcount)]

    def _file_name(self, frame): return frame.f_code.co_filename
    
    def _method(self, frame): return frame.f_code.co_name

    def all_vars(self, frame): return frame.f_locals
    
    def __repr__(self): return "%s:%s(%s)" % (self.file_name, self.method, ','.join(self.parameter_names))

class Tracer:
    def __enter__(self):
        self.oldtrace = sys.gettrace()
        sys.settrace(self.trace_event)
        return self

    def __exit__(self, *args):
        sys.settrace(self.oldtrace)

    def __call__(self): return self.inputstr

    def __init__(self, inputstr, restrict={}):
        self.inputstr = xtstr(inputstr, parent=None).with_comparisons([])
        self.trace = []
        self.restrict = restrict

        self.method_num = 0
        # method_num, method_name, children
        start = (self.method_num, None, [])
        self.method_num_stack = [start]
        self.method_map = {self.method_num: start}

    def tracing_context(self, cxt, event, arg):
        if self.restrict.get('files'):
            return any(cxt.file_name.endswith(f) for f in self.restrict['files'])
        if self.restrict.get('methods'):
            return cxt.method in self.restrict['methods']
        return True

    def trace_event(self, frame, event, arg):
        cxt = Context(frame)
        if not self.tracing_context(cxt, event, arg):
            return self.trace_event

        self.on_event(event, arg, cxt)
        return self.trace_event

    def on_event(self, event, arg, cxt):
        # make it tree
        self.trace.append((event, cxt))
        if event == 'call':
            self.method_num += 1

            # create our method invocation
            # method_num, method_name, children
            n = (self.method_num, cxt.method, [])
            self.method_map[self.method_num] = n

            # add ourselves as one of the children to the previous method invocation
            self.method_num_stack[-1][2].append(n)

            # and set us as the current method.
            self.method_num_stack.append(n)
        elif event == 'return':
            self.method_num_stack.pop()
        current_minfo = self.method_num_stack[-1] # current
        current_mid = current_minfo[0]
        set_current_method(cxt.method, len(self.method_num_stack), current_mid)

def convert(method_map):
    light_map = {}
    for k in method_map:
        method_num, method_name, children = method_map[k]
        light_map[k] = (k, method_name, [c[0] for c in children])
    return light_map

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

if __name__ == "__main__":
    mystring = 'a=1'
    #mystring = 'avar=1.3;bvar=avar-3*(4+300)'
    C_VG = canonical(VAR_GRAMMAR)
    restrict = {'methods':['unify_key', 'unify_rule']}
    mystring = 'avar=1.3;bvar=avar-3*(4+300)'
    #mystring = 'av=1' #.3;bvar=avar-3*(4+300)'
    with Tracer(mystring, restrict) as tracer:
        unify_key(C_VG, '<start>', tracer())
    assert tracer.inputstr.comparisons
    with open('comparisons.json', 'w+') as f:
        f.write(json.dumps(tracer.inputstr.comparisons))
    with open('method_map.json', 'w+') as f:
        f.write(json.dumps(convert(tracer.method_map)))
    with open('inputstr.json', 'w+') as f:
        f.write(json.dumps(str(tracer.inputstr)))
