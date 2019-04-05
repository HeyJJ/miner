CHECKSUM_REPAIR=../checksum-repair
java=java
.PHONY: trace mine

PROJECTS=calc_parse

T_INSTRUMENTED=$(add-prefix,.,$(add-suffix,$(PROJECTS),.instrumented))
T_RUN=$(add-prefix,.,$(add-suffix,$(PROJECTS),.run))
T_TAINT=$(add-prefix,.,$(add-suffix,$(PROJECTS),.taint))
T_TRACE=$(add-prefix,.,$(add-suffix,$(PROJECTS),.trace))

.PRECIOUS: $(T_INSTRUMENTED) $(T_RUN) $(T_TAINT) $(T_TRACE)

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


## ---- INSTRUMENT-----

instrument_%: .%.instrumented; @echo done
.%.instrumented: subjects/%.c
	./bin/trace-instr $< $(CHECKSUM_REPAIR)/samples/excluded_functions
	touch $@

## ---- RUN -----

run_%: .%.run; @echo done
.%.run: .%.instrumented
	echo $(INPUTSTR) | ./build/$*.instrumented
	mv output build/$*.output
	gzip -c build/$*.output > build/$*.output.gz
	touch $@

## ---- OFFLINE TAINT ANALYSIS ---

taint_%: .%.taint; @echo done
.%.taint: .%.run
	$(java) -cp "$(CHECKSUM_REPAIR)/install/lib/java/*" main.TaintTracker -me build/calc_parse/metadata -po build/$*.pygmalion.json -t build/$*.output.gz
	touch $@

## ---- OFFLINE CALL TRACE ---
trace_%: .%.trace; @echo done
.%.trace: .%.taint
	cat build/$*.pygmalion.json | python3 ./src/converter.py $(INPUTSTR) > build/$*.call_trace.json
	touch $@


## ---- MINE GRAMMAR ---

mine_%: .%.mine; @echo done
.%.mine: .%.trace
	python3 ./src/mine.py build/$*.call_trace.json
	touch $@
