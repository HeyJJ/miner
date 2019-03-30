#!/usr/bin/env python3
import sys
import re
import string

RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')
def tree_to_string(tree):
    def is_nonterminal(s): return re.match(RE_NONTERMINAL, s)
    symbol, children, *_ = tree
    if children: return ''.join(tree_to_string(c) for c in children)
    else: return '' if is_nonterminal(symbol) else symbol

from InformationFlow import ctstr

CURRENT_METHOD = None

def get_current_method():
    return CURRENT_METHOD

def set_current_method(method, method_stack):
    global CURRENT_METHOD
    CURRENT_METHOD = (method, len(method_stack), method_stack[-1])
    return CURRENT_METHOD

class xtstr(ctstr):
    def add_instr(self, op, c_a, c_b):
        ct = None
        if len(c_a) == 1 and isinstance(c_a, xtstr):
            ct = c_a.taint[0]
        elif len(c_b) == 1 and isinstance(c_b, xtstr):
            ct = c_b.taint[0]
        self.comparisons.append((ct, get_current_method()))

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
        set_current_method(cxt.method, self.method_num_stack)

# Given a child id, we can retrieve the parent id
# parent_map[childid] == parent_id
def to_parent_map(method_map):
    parent_map = {}
    for i in method_map:
        mid, _method, children = method_map[i]
        for cmid,*_ in children:
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
    for idx, (method_name, stack_len, minfo) in trace:
        if idx is None: continue  # TODO. investigate None idx in IF
        last_cmp_only[idx] = (idx, method_name, stack_len, minfo[0])

    res = []
    for x in last_cmp_only.values():
        idx, method_name, stack_len, mid = x
        c = inputstr[idx]
        print("%2d" % idx, " ", c, '  |' * stack_len, method_name, mid, "(%d)" % stack_len)
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
            e_mid, e_method, _ = method_map[elt]
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
    mystring = 'av=1' #.3;bvar=avar-3*(4+300)'
    with Tracer(mystring, restrict) as tracer:
        unify_key(C_VG, '<start>', tracer())
    assert tracer.inputstr.comparisons

    my_root = parse_trees(tracer.inputstr.comparisons, str(tracer.inputstr), tracer.method_map)
    #print(my_root)
    tree = to_tree(my_root, str(tracer.inputstr))
    print(tree)
    assert tree_to_string(tree) == str(tracer.inputstr)
