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

def convert_pygmalion(instr):
    methods={} #helper dict method_name->id
    method_dict = {} #dict for method_id->(method_id, name, children)
    # irrelevant input comparisions
    irrelevant_operators = ["tokenstore", "tokencomp", "EOF", "strlen"]
    input_comparisons = []
    for line in sys.stdin.readlines():
            #ignore comments
            if not line.startswith("{"): continue
            data = json.loads(line)
            '''build tree of invocations'''
            if data['type'] == "STACK_EVENT":
                stack = data['stack']
                parent_id = 0
                for method in stack:
                    if method in methods.keys():
                        parent_id = methods[method]
                        continue
                    else:
                        method_id = len(methods) #starts with 0
                        methods[method] = method_id
                        method_dict[method_id] = (method_id, method, [])
                        if method_id > 0:
                            method_dict[parent_id][2].append(method_id)

            '''build list of comparisions'''
            if data['type'] == "INPUT_COMPARISON":
                operator = data['operator']
                if operator in irrelevant_operators:
                    continue
                index = data['index'][0] # !! for strcmp there is a list of indeces. Only taken first one.
                method = data['stack'][-1]
                method_id = methods[method] #get id from helper dict
                input_comparisons.append((index, method_id))

    print(json.dumps({'inputstr': instr, 'method_map': method_dict, 'comparisons': input_comparisons}, indent=2, sort_keys=False))

if __name__ == "__main__":
    convert_pygmalion(sys.argv[1])
