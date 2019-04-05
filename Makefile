.PHONY: trace mine

.SECONDARY: peg_call_trace.json calc_call_trace.json

ARG='a=1'

all: peg_mine

%_call_trace.json: src/%_parse.py
	python3 ./src/$*_parse.py $(ARG) > _$@
	mv _$@ $@
	#python3 ./src/calc_parse.py $(ARG)

%_mine: %_call_trace.json
	python3 ./src/mine.py $<

clean:
	rm *.json
