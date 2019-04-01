.PHONY: trace mine

ARG='a=1'

all: mine

trace: comparisons.json

comparisons.json: src/peg_parse.py
	python3 ./src/peg_parse.py $(ARG)
	#python3 ./src/calc_parse.py $(ARG)

mine: comparisons.json
	python3 ./src/mine.py

clean:
	rm *.json
