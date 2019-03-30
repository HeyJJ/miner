.PHONY: trace mine

ARG='a=1'

all: mine

trace: comparisons.json

comparisons.json: src/trace.py
	python3 ./src/trace.py $(ARG)

mine: comparisons.json
	python3 ./src/mine.py

clean:
	rm *.json
