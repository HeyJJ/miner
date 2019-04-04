To get pygmalion.json file:
Run Björns tool (see in samples/calc_parse/build_calc.sh on Björns branch).

Converter.py takes the pygmalion.json and converts it to "my_comparisons.json" and "my_method_map.json".

The examples in this repo are from calling:
echo "(1+2)" | ./calc_parse.c.instrumented
