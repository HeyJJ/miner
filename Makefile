CHECKSUM_REPAIR=../checksum-repair
java=java
.PHONY: trace mine

PROJECTS=calc_parse
T_UNINSTRUMENTED=$(addsuffix .uninstrumentedll,$(PROJECTS))
T_ORIGINAL=$(addsuffix .original,$(PROJECTS))
T_INSTRUMENTED=$(addsuffix .instrumented,$(PROJECTS))
T_BITCODE=$(addsuffix .metadata,$(PROJECTS))
T_RUN=$(addsuffix .run,$(PROJECTS))
T_TAINT=$(addsuffix .taint,$(PROJECTS))
T_TRACE=$(addsuffix .trace,$(PROJECTS))
T_MINE=$(addsuffix .mine,$(PROJECTS))

.PRECIOUS: $(addprefix build/.,$(T_ORIGINAL) $(T_UNINSTRUMENTED) $(T_INSTRUMENTED) $(T_BITCODE) $(T_RUN) $(T_TAINT) $(T_TRACE) $(T_MINE)) $(addsuffix /uninstrumented,$(addprefix build/,$(PROJECTS)))

.SECONDARY: peg_call_trace.json calc_call_trace.json

ARG='a=1'

#all: mine_calc_parse; @echo all
all: calc_parse_mine; @echo all

EARG='(25-1/(2+3))*100/3'
%_call_trace.json: src/%_parse.py
	python3 ./src/$*_parse.py $(EARG) > _$@
	mv _$@ $@

%_mine: %_call_trace.json
	python3 ./src/mine.py $<

clean:
	rm -rf *.json build

## ----  DECOMPILE ---
DECOMPILER=$(HOME)/Research/dagger/build/bin/llvm-dec

decompile_%: build/.%.decompiled; @echo decompile
build/.%.decompiled: build/.%.original
	$(DECOMPILER) build/$*/original > build/$*/decompiled.ll
	touch $@

INPUTSTR="(1+23)+(123-43)/3*1"

TOOLCHAIN=$(HOME)/toolchains/llvm+clang-401-x86_64-apple-darwin17.7.0
LLVM=$(TOOLCHAIN)/bin/opt
CLANG=$(TOOLCHAIN)/bin/clang
LIBDIR=$(CHECKSUM_REPAIR)/install/lib
INCDIR=$(CHECKSUM_REPAIR)/install/include
TRACEPLUGIN=$(CHECKSUM_REPAIR)/build/debug/modules/trace-instr/libtraceplugin.dylib
EXCLUDED_FUNCTIONS=$(CHECKSUM_REPAIR)/samples/excluded_functions

## ----  COMPILE ---
original_%: build/.%.original; @echo original
build/.%.original: subjects/%.c | build
	mkdir -p build/$*
	$(CLANG) -g -D_FORTIFY_SOURCE=0 -o build/$*/original -x c $< -ldl
	touch $@

## ---- GEN UNINSTRUMETED BITCODE -----
ull_%: build/.%.uninstrumentedll; @echo ull
build/.%.uninstrumentedll: subjects/%.c | build
	mkdir -p build/$*
	$(CLANG) -g -S -D_FORTIFY_SOURCE=0 -emit-llvm -include $(INCDIR)/traceinstr/wrapper_libc.h -o build/$*/uninstrumented.ll -x c $<
	touch $@

metadata%: build/.%.metadata; @echo metadata
build/.%.metadata: build/.%.uninstrumentedll
	# extract metadata for taint analysis
	$(CHECKSUM_REPAIR)/install/bin/extract_metadata -ef $(EXCLUDED_FUNCTIONS) -f build/$*/uninstrumented.ll
	touch $@

## ---- INSTRUMENT BITCODE-----
instrument_%: build/.%.instrumented; @echo instrument
build/.%.instrumented: build/.%.metadata build/.%.uninstrumentedll | build
	$(LLVM) -S -instnamer -reg2mem -load $(TRACEPLUGIN) -traceplugin -exclude_functions $(EXCLUDED_FUNCTIONS) -disable-verify build/$*/uninstrumented.ll -o  build/$*/opt_debug.ll
	$(LLVM) -S -strip-debug build/$*/opt_debug.ll -o build/$*/debug.ll
	$(CLANG) -fno-inline -O3 -o build/$*.instrumented build/$*/debug.ll -L$(LIBDIR) -lwrappermain -lwrapperlibc -lsimpletracer -ljson-c -lm -lz -ldl
	touch $@

## ---- RUN -----

run_%: build/.%.run; @echo run
build/.%.run: build/.%.instrumented
	echo $(INPUTSTR) | ./build/$*.instrumented
	mv output build/$*/output
	gzip -c build/$*/output > build/$*/output.gz
	touch $@

## ---- OFFLINE TAINT ANALYSIS ---

taint_%: build/.%.taint; @echo taint
build/.%.taint: build/.%.run
	$(java) -cp "$(CHECKSUM_REPAIR)/install/lib/java/*" main.TaintTracker -me build/calc_parse/metadata -po build/$*.pygmalion.json -t build/$*/output.gz
	touch $@

## ---- OFFLINE CALL TRACE ---
trace_%: build/.%.trace; @echo trace
build/.%.trace: build/.%.taint
	cat build/$*.pygmalion.json \
		| grep -v '"operator":"tokenstore"' \
		| grep -v '"operator":"tokencomp"'\
		| grep -v '"operator":"strlen"' \
		| python3 ./src/converter.py $(INPUTSTR) > build/$*/call_trace.json
	touch $@


## ---- MINE GRAMMAR ---

mine_%: build/.%.mine; @echo mine
build/.%.mine: build/.%.trace
	python3 ./src/mine.py build/$*/call_trace.json
	touch $@


## ---------------------
build: ; mkdir -p build
## ---------------------
backup:; cp build/calc_parse/uninstrumented.ll .uninstrumeted.ll

restore: ; cp  .uninstrumeted.ll build/calc_parse/uninstrumented.ll

reapply:
	$(MAKE) decompile_calc_parse
	cp build/calc_parse/decompiled.ll build/calc_parse/uninstrumented.ll
	rm -f build/.calc_parse.instrumented
	$(MAKE) mine_calc_parse
