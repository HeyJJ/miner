To get pygmalion.json file:
Run Björns tool (see in samples/calc_parse/build_calc.sh on Björns branch).

Converter.py takes the pygmalion.json and converts it to "my_comparisons.json" and "my_method_map.json".

The examples in this repo are from calling:
echo "(1+2)" | ./calc_parse.c.instrumented

If you want to create a .json file with the input, simply call:
echo "(1+2)" | tee inputstr.json | ./calc_parse.c.instrumented
instead. 

Right now, nothing is done with an inputstr.json in Converter.py.
