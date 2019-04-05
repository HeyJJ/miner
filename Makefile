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

all: mine_calc_parse

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

LLVM=$(HOME)/toolchains/llvm+clang-401-x86_64-apple-darwin18.2.0/bin/opt
CLANG=$(HOME)/toolchains/llvm+clang-401-x86_64-apple-darwin18.2.0/bin/clang
LIBDIR=$(CHECKSUM_REPAIR)/install/lib
INCDIR=$(CHECKSUM_REPAIR)/install/include
TRACEPLUGIN=$(CHECKSUM_REPAIR)/build/debug/modules/trace-instr/libtraceplugin.dylib
EXCLUDED_FUNCTIONS=$(CHECKSUM_REPAIR)/samples/excluded_functions

## ---- GEN BITCODE -----
bitcode%: build/.%.bitcode; @echo done
build/.%.bitcode: subjects/%.c | build
	mkdir -p build/$*
	# build instrumented version
	$(CLANG) -g -D_FORTIFY_SOURCE=0 -o build/$*/uninstrumented -x c $< -ldl
	$(CLANG) -g -S -D_FORTIFY_SOURCE=0 -emit-llvm -include $(INCDIR)/traceinstr/wrapper_libc.h -o build/$*/uninstrumented.bc -x c $<
	# extract metadata for taint analysis
	$(CHECKSUM_REPAIR)/install/bin/extract_metadata -ef $(EXCLUDED_FUNCTIONS) -f build/$*/uninstrumented.bc
	touch $@

## ---- INSTRUMENT-----
instrument_%: build/.%.instrumented; @echo done
build/.%.instrumented: build/.%.bitcode | build
	$(LLVM) -S -instnamer -reg2mem -load $(TRACEPLUGIN) -traceplugin -exclude_functions $(EXCLUDED_FUNCTIONS) -disable-verify build/$*/uninstrumented.bc -o  build/$*/opt_debug.bc
	$(LLVM) -S -strip-debug build/$*/opt_debug.bc -o build/$*/debug.bc
	$(CLANG) -fno-inline -O3 -o build/$*.instrumented build/$*/debug.bc -L$(LIBDIR) -lwrappermain -lwrapperlibc -lsimpletracer -ljson-c -lm -lz -ldl
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


## ---------------------
build: ; mkdir -p build
