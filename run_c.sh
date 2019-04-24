# ensure TOOLCHAIN exists
source .envrc
make -e mine_calc_parse
python3 -m pudb src/refine.py derivation_tree.json
