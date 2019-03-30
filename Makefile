.PHONY: trace mine

all: mine

trace: comparisons.json

comparisons.json: src/trace.py
	python3 ./src/trace.py

mine: comparisons.json
	python3 ./src/mine.py

clean:
	rm *.json
