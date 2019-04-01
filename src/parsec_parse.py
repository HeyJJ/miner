#!/usr/bin/env python3
import string
import json
import sys
import Tracer
import pyparsec
aparser = pyparsec.char("a")
bparser = pyparsec.char("b")
cparser = pyparsec.char("c")

abcparser = aparser >> bparser >> cparser
sentp = pyparsec.letters >> pyparsec.char(",") >> pyparsec.many(pyparsec.whitespace) >> pyparsec.letters >> pyparsec.optionally(pyparsec.char("!"))
if __name__ == "__main__":
    mystring = sys.argv[1] if len(sys.argv) > 1 else "abc"
    #mystring = sys.argv[1] if len(sys.argv) > 1 else "Hello, World!"
    #restrict = {'methods':['parse_num', 'parse_paren', 'parse_expr']}
    with Tracer.Tracer(mystring) as tracer:
        abcparser.parse(tracer())
        #sentp.parse(tracer())
    assert tracer.inputstr.comparisons
    with open('comparisons.json', 'w+') as f:
        f.write(json.dumps(Tracer.convert_comparisons(tracer.inputstr.comparisons)))
    #    #f.write(json.dumps(tracer.inputstr.comparisons))
    with open('method_map.json', 'w+') as f:
        f.write(json.dumps(Tracer.convert_method_map(tracer.method_map)))
    #    #f.write(json.dumps(tracer.method_map))
    with open('inputstr.json', 'w+') as f:
        f.write(json.dumps(str(tracer.inputstr)))
