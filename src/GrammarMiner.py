#!/usr/bin/env python3
import sys
import re
import string

def parse_num(s,i):
    n = ''
    while s[i:] and s[i].in_(list(string.digits)):
        n += s[i]
        i = i +1
    return i,n

def parse_paren(s, i):
    assert s[i] == '('
    i, v = parse_expr(s, i+1)
    if s[i:] == '':
        raise Exception(s, i)
    assert s[i] == ')'
    return i+1, v


def parse_expr(s, i = 0):
    expr = []
    while s[i:]:
        c = s[i]
        if c.in_(list(string.digits)):
            i,num = parse_num(s,i)
            expr.append(num)
        elif c.in_(['+', '-', '*', '/']):
            expr.append(c)
            i = i + 1
        elif c == '(':
            i, cexpr = parse_paren(s, i)
            expr.append(cexpr)
        elif c == ')':
            return i, expr
        else:
            raise Exception(s,i)
    return i, expr

EXPRS = [
    '12+23',
    '(25+1)+100+(33+2)+1',
    '(25-1/(2+3))*100/3'
]



RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')
def tree_to_string(tree):
    def is_nonterminal(s): return re.match(RE_NONTERMINAL, s)
    symbol, children, *_ = tree
    if children: return ''.join(tree_to_string(c) for c in children)
    else: return '' if is_nonterminal(symbol) else symbol

from InformationFlow import tstr, ctstr, Instr

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
        self.comparisons.append((ct, Instr(op, c_a, c_b), get_current_method()))

    def create(self, res, taint):
        o = xtstr(res, taint, self)
        o.comparisons = self.comparisons
        return o

class Context:
    def __init__(self, frame, track_caller=True):
        self.method = self._method(frame)
        self.parameter_names = self._get_parameters(frame)
        self.file_name = self._file_name(frame)
        self.parent = Context(frame.f_back,
                              False) if track_caller and frame.f_back else None

    def _get_parameters(self, frame):
        return [
            frame.f_code.co_varnames[i]
            for i in range(frame.f_code.co_argcount)
        ]

    def _file_name(self, frame):
        return frame.f_code.co_filename
    
    def _method(self, frame):
        return frame.f_code.co_name

    def all_vars(self, frame):
        return frame.f_locals
    
    def __repr__(self):
        return "%s:%s(%s)" % (self.file_name, self.method, ','.join(self.parameter_names))

class Tracer:
    def __enter__(self):
        self.oldtrace = sys.gettrace()
        sys.settrace(self.trace_event)
        return self

    def __exit__(self, *args):
        sys.settrace(self.oldtrace)

    def on_event(self, event, arg, cxt, my_vars):
        self.trace.append((event, arg, cxt, my_vars))

    def trace_event(self, frame, event, arg):
        cxt = Context(frame)
        if not self.tracing_context(cxt, event, arg):
            return self.trace_event

        my_vars = [(k, v) for k, v in cxt.all_vars(frame).items()
                   if self.tracing_var(k, v)]
        self.on_event(event, arg, cxt, my_vars)
        return self.trace_event

    def __call__(self): return self.inputstr

# ### Tainted Tracer
class TaintedTracer(Tracer):
    def __init__(self, inputstr, restrict={}):
        self.inputstr = xtstr(inputstr, parent=None).with_comparisons([])
        self.trace = []
        self.restrict = restrict

        self.method_num = 0
        self.method_num_stack = [self.method_num]

    def tracing_var(self, k, v): return isinstance(repr(v), tstr)

    def tracing_context(self, cxt, event, arg):
        if self.restrict.get('files'):
            return any(
                cxt.file_name.endswith(f) for f in self.restrict['files'])
        if self.restrict.get('methods'):
            return cxt.method in self.restrict['methods']
        return True

    def on_event(self, event, arg, cxt, my_vars):
        super().on_event(event, arg, cxt, my_vars)
        if event == 'call':
            self.method_num += 1
            self.method_num_stack.append(self.method_num)
        elif event == 'return':
            self.method_num_stack.pop()
        set_current_method(cxt.method, self.method_num_stack)

if __name__ == "__main__":
    print(EXPRS[1])
    restrict = {'methods':['parse_expr', 'parse_paren', 'parse_num']}
    with TaintedTracer(EXPRS[1], restrict) as tracer:
        parse_expr(tracer())

# ## Tainted Miner (2)
if __name__ == "__main__":
    print('\n## Tainted Miner (2)')

def parse_trees(trace, inputstr):
    # name,stack,children,idxs
    def new_node(s, stack, mid=None, indexes=None):
        n = {
            'sym': '<%s>' % s,
            'id': mid,
            'stack': stack,
            'indexes':  [],#[inputstr[i] for i in indexes] if indexes is not None else [],
            'children': []
        }
        for i in (indexes or []):
            n_addindex(n, i)
        return n

    root = new_node('start', stack=0, mid=0)
    method_stack = [root]

    def n_addchild(node, n): node['children'].append(n)
    def n_mid(node):      return node['id']
    def n_sym(node):      return node['sym']
    def n_addindex(node, i):
        c = inputstr[i]
        #node['indexes'].append(c)
        if node['children']:
            last_child = node['children'][-1]
            if last_child.get('id') is None: # last child an index. Hence, append
                last_child['indexes'].append(c)
                last_child['sym'] = ''.join(last_child['indexes'])
            else: # last child a method. Hence, start a new node
                n_addchild(node, {'sym': c, 'indexes': [c]})
        else: #no last_child. Start a new node
            n_addchild(node, {'sym': c, 'indexes': [c]})

    print(inputstr)
    prev_idx = None
    prev_node = None
    last_cmp_only = []
    for idx, instr, (method_name, stack_len, mid) in trace:
        if idx is None: continue
        if idx == prev_idx:
            prev_node = (idx, method_name, stack_len, mid)
        else:
            if prev_node is not None:
                last_cmp_only.append(prev_node)
            prev_node = (idx, method_name, stack_len, mid)
            prev_idx = idx
    if prev_node is not None:
        last_cmp_only.append(prev_node)
    print(len(last_cmp_only))
    for x in last_cmp_only:
        print(repr(x))
        idx, method_name, stack_len, mid = x
        print("%2d" % idx, " ", inputstr[idx], '  |' * stack_len, method_name,
              mid, "(%d)" % stack_len)
    print()
    for idx, method_name, stack_len, mid in last_cmp_only:#[:4]:
        last_idx = len(method_stack) -1
        print(inputstr)
        print("%2d" % idx, " chr:%s" % inputstr[idx], '  |' * stack_len, "\t",
              method_name, mid, "(%d)" % stack_len)
        if stack_len > last_idx:
            print('###### append parent')
            # first, generate a chain of the given stack length to the parent.
            for i in range(len(method_stack), stack_len):
                node = new_node('*',stack=i, mid=None)
                n_addchild(method_stack[-1],node)
                method_stack.append(node)

            assert len(method_stack) == stack_len
            # then for the given parent, add a child
            node = new_node(method_name, stack=stack_len, mid=mid, indexes=[idx])
            current = method_stack[-1]
            n_addchild(current,node)
            method_stack.append(node)
        elif stack_len == last_idx:
            current = method_stack[-1]
            if n_mid(current) == mid:
                print('###### insert char')
                assert n_sym(current) == "<%s>" % method_name
                current = method_stack[-1]
                n_addindex(current, idx)
            else:
                print('###### start new peer node')
                # a peer of this node. So get parent
                method_stack.pop()
                current = method_stack[-1]
                node = new_node(method_name, stack=stack_len, mid=mid, indexes=[idx])
                n_addchild(current,node)
        elif stack_len < last_idx:
            current = method_stack[-1]
            print("-", current)
            while stack_len < last_idx:
                print('<-')
                method_stack.pop()
                last_idx = len(method_stack)-1
            assert stack_len == last_idx
            current = method_stack[-1]
            
            if n_mid(current) is None:
                current['id'] = mid
                current['sym'] = "<%s>" % method_name
            else:
                assert n_mid(current) == mid, "%s != %s" %(n_mid(current), mid)
                assert n_sym(current) == "<%s>" % method_name
            current = method_stack[-1]
            n_addindex(current, idx)
    return root


if __name__ == "__main__":
    my_root = parse_trees(tracer.inputstr.comparisons, str(tracer.inputstr))

def to_tree(node, my_str):
    sym = node['sym']
    children = node.get('children')
    if children:
        return (sym, [to_tree(c, my_str) for c in children])
    else:
        return (sym, [])

if __name__ == "__main__":
    to_tree(my_root, str(tracer.inputstr))

if __name__ == "__main__":
    print(tracer.inputstr)
    tree = to_tree(my_root, str(tracer.inputstr))
    assert tree_to_string(tree) == str(tracer.inputstr)

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

if __name__ == "__main__":
    mystring = 'a=1'
    #mystring = 'avar=1.3;bvar=avar-3*(4+300)'
    C_VG = canonical(VAR_GRAMMAR)


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

class TaintedTracer(Tracer):
    def __init__(self, inputstr, restrict={}):
        self.inputstr = xtstr(inputstr, parent=None).with_comparisons([])
        self.trace = []
        self.restrict = restrict

        self.method_num = 0
        start = (self.method_num, None, [], {})
        self.method_num_stack = [start]
        self.method_map = {self.method_num: start}

    def tracing_var(self, k, v): return isinstance(repr(v), tstr)

    def tracing_context(self, cxt, event, arg):
        if self.restrict.get('files'):
            return any(
                cxt.file_name.endswith(f) for f in self.restrict['files'])
        if self.restrict.get('methods'):
            return cxt.method in self.restrict['methods']
        return True

    def on_event(self, event, arg, cxt, my_vars):
        # make it tree
        super().on_event(event, arg, cxt, my_vars)
        if event == 'call':
            self.method_num += 1
            n = (self.method_num, cxt.method, [], {})
            self.method_map[self.method_num] = n
            self.method_num_stack[-1][2].append(n)
            self.method_num_stack.append(n)
        elif event == 'return':
            self.method_num_stack.pop()
        set_current_method(cxt.method, self.method_num_stack)

def to_parent_map(method_map):
    parent_map = {}
    for i in method_map:
        mid, method, children, ann = method_map[i]
        for cmid,*_ in children:
            parent_map[cmid] = mid
    return parent_map

def parse_trees(trace, inputstr, method_map):
    def add_indexes(node, indexes):
        for i in indexes:
            n = new_node(i)
            node['children'].append(n)
    parent_map = to_parent_map(method_map)

    # name,stack,children,idxs

    def new_node(s, mid=None):
        return {
            'sym': s,
            'id': mid,
            'children': []
        }

    root = new_node("<%s>" % 'start', mid=0)
    method_stack = [root]
    method_stack_map = {s['id'] for s in method_stack}
    last_cmp_only = {}
    for idx, instr, (method_name, stack_len, minfo) in trace:
        if idx is None: continue  # TODO. investigate None idx in IF
        last_cmp_only[idx] = (idx, method_name, stack_len, minfo[0])
        
    for x in last_cmp_only.values():
        idx, method_name, stack_len, mid = x
        print("%2d" % idx, " ", inputstr[idx], '  |' * stack_len, method_name, mid, "(%d)" % stack_len)
    print()
    
    last_cmp_values = list(last_cmp_only.values())
    for idx, m_name, stack_len, mid in last_cmp_values:
        print("%2d" % idx, repr(inputstr[idx]), '  |' * stack_len, m_name, mid, "(%d)" % stack_len)
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

        # pop off the method_stack until we come to the parents[0]
        while parents[0] != method_stack[-1]['id']:
            v = method_stack.pop()
            method_stack_map.remove(v['id'])

        # now start appending until we reach mid
        # note that we also append a node with mid
        for elt in parents[1:]:
            e_mid, e_method, e_children, e_ann = method_map[elt]
            idxs = [] if e_mid != mid else [inputstr[idx]]
            node = new_node("<%s>" % e_method, mid=elt)
            add_indexes(node, idxs)
            method_stack[-1]['children'].append(node)
            method_stack.append(node)
            method_stack_map.add(node['id'])

    return root

def to_tree(node, my_str):
    sym = node['sym']
    children = node.get('children')
    if children:
        return (sym, [to_tree(c, my_str) for c in children])
    else:
        return (sym, [])

if __name__ == "__main__":
    restrict = {'methods':['unify_key', 'unify_rule']}
    mystring = 'avar=1.3;bvar=avar-3*(4+300)'
    with TaintedTracer(mystring, restrict) as tracer:
        unify_key(C_VG, '<start>', tracer())
    assert tracer.inputstr.comparisons

if __name__ == "__main__":
    tracer.method_map[225]


if __name__ == "__main__":
    my_root = parse_trees(tracer.inputstr.comparisons, str(tracer.inputstr), tracer.method_map)
    #print(my_root)
    tree = to_tree(my_root, str(tracer.inputstr))
    #print(tree)
    assert tree_to_string(tree) == str(tracer.inputstr)

