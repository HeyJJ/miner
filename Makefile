CHECKSUM_REPAIR=../checksum-repair
java=java
.PHONY: trace mine

PROJECTS=calc_parse
T_INSTRUMENTED=$(addsuffix .instrumented,$(PROJECTS))
T_RUN=$(addsuffix .run,$(PROJECTS))
T_TAINT=$(addsuffix .taint,$(PROJECTS))
T_TRACE=$(addsuffix .trace,$(PROJECTS))
T_MINE=$(addsuffix .mine,$(PROJECTS))

.PRECIOUS: $(addprefix build/.,$(T_INSTRUMENTED) $(T_RUN) $(T_TAINT) $(T_TRACE) $(T_MINE))

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

%_mine: %_call_trace.json
	python3 ./src/mine.py $<


INPUTSTR="(1+23)+(123-43)/3*1"
## ---- INSTRUMENT-----

instrument_%: build/.%.instrumented; @echo done
build/.%.instrumented: subjects/%.c
	./bin/trace-instr $< $(CHECKSUM_REPAIR)/samples/excluded_functions
	touch $@

## ---- RUN -----

run_%: build/.%.run; @echo done
build/.%.run: build/.%.instrumented
	echo $(INPUTSTR) | ./build/$*.instrumented
	mv output build/$*.output
	gzip -c build/$*.output > build/$*.output.gz
	touch $@

## ---- OFFLINE TAINT ANALYSIS ---

taint_%: build/.%.taint; @echo done
build/.%.taint: build/.%.run
	$(java) -cp "$(CHECKSUM_REPAIR)/install/lib/java/*" main.TaintTracker -me build/calc_parse/metadata -po build/$*.pygmalion.json -t build/$*.output.gz
	touch $@

## ---- OFFLINE CALL TRACE ---
trace_%: build/.%.trace; @echo done
build/.%.trace: build/.%.taint
	cat build/$*.pygmalion.json \
		| grep -v '"operator":"tokenstore"' \
		| grep -v '"operator":"tokencomp"'\
		| grep -v '"operator":"strlen"' \
		| python3 ./src/converter.py $(INPUTSTR) > build/$*.call_trace.json
	touch $@


## ---- MINE GRAMMAR ---

mine_%: build/.%.mine; @echo done
build/.%.mine: build/.%.trace
	python3 ./src/mine.py build/$*.call_trace.json
	touch $@
