#!/usr/bin/env python3
import json
import sys
"""   Convert pygmalion file to specified format   
Format of pygmalion.json:
The important parts for constructing the invocation tree and the comparisons are:
- "type": type of event (STACK_EVENT or INPUT_COMPARISON)
- "stack": represents stack as list of method names at that point
- "index": represents index/indices in input string at which comparison occured
- "operator": represents type of comparison operation (!=, ==, strcmp ,...)
Author: Julia Hess
"""
IGNORE = ["tokenstore", "tokencomp", "EOF", "strlen"]

def convert_pygmalion(instr):
    methods={} #helper dict method_name->id
    method_dict = {} #dict for method_id->(method_id, name, children)
    # irrelevant input comparisions
    input_comparisons = []
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()
    method_count = -1
    method_id = -1
    parent_id = -1
    old_stack_size = 0
    method_stack = [(None, -1, [])]
    current_method = None
    method_map = {}
    old_stack = None
    children = []
    for i,line in enumerate(lines):
            #ignore comments
            if not line.startswith("{"): continue
            data = json.loads(line)
            '''build tree of invocations'''
            if data['type'] == "STACK_EVENT":
                stack = data['stack']
                if len(stack) > old_stack_size:
                    method_count += 1
                    method_id = method_count
                    current_method = (method_id, stack[-1], [])
                    method_map[method_id] = current_method
                    method_stack[-1][2].append(method_id)
                    method_stack.append(current_method)
                    old_stack_size = len(stack)
                elif len(stack) < old_stack_size:
                    method_stack.pop()
                    method_id, _, _ = method_stack[-1]
                    old_stack_size = len(stack)
                else:
                    assert False
                old_stack = stack

            '''build list of comparisions'''
            if data['type'] == "INPUT_COMPARISON" and data['operator'] not in IGNORE:
                index = data['index'][0] # !! for strcmp there is a list of indeces. Only taken first one.
                input_comparisons.append((index, method_id))

    print(json.dumps({'inputstr': instr, 'method_map': method_map, 'comparisons': input_comparisons}, indent=2, sort_keys=False))

if __name__ == "__main__":
    convert_pygmalion(sys.argv[1])
