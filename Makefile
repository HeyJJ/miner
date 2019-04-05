CHECKSUM_REPAIR=../checksum-repair
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
	rm -rf *.json build

INPUTSTR="(1+23)+(123-43)/3*1"

convert: pygmalion.json
	cat pygmalion.json | python3 ./src/converter.py $(INPUTSTR) > calc_call_trace.json

%_mine: %_call_trace.json
	python3 ./src/mine.py $<

%_instrument: subjects/%_parse.c
	./bin/trace-instr $< $(CHECKSUM_REPAIR)/samples/excluded_functions


#run your C-program (example)
run: calc_instrument
	echo $(INPUTSTR) | ./build/calc_parse/calc_parse.instrumented

#zip output file

#generate taint from the trace
taint:
	gzip -c output > output.gz
	java -cp "$(CHECKSUM_REPAIR)/install/lib/java/*" main.TaintTracker -me build/calc_parse/metadata -po pygmalion.json -t output.gz
