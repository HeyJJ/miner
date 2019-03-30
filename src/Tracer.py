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
        self.method = frame.f_code.co_name
        self.file_name = frame.f_code.co_filename
        self.parent = Context(frame.f_back, False) if track_caller and frame.f_back else None

import sys
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
        if not self.tracing_context(cxt, event, arg): return self.trace_event
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
