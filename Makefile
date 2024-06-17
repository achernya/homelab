# Set make's shell to bash, and put bash into pedantic mode.
SHELL = /bin/bash
.SHELLFLAGS = -euf -o pipefail -c

# Disable all built-in implicit rules.
.SUFFIXES:

# If any rule invocation fails, delete the output file. This is
# particularly useful for test failures, like the deps-check below, as
# it ensures the test will be re-run rather than assume it passed.
.DELETE_ON_ERROR:

charts := $(wildcard kubernetes/*/Chart.yaml)
helm_deps := $(charts:.yaml=.deps-check)

.ONESHELL:
%.deps-check: %.yaml
	@echo "Checking dependencies of $(dir $<)"
	@tools/helm_missing_deps.sh $(dir $<) > $@
	@[[ -s $@ ]] || exit 0
	@echo "Chart $(dir $<) is missing dependencies"
	@exit 1

# `make check` is an alias for `make test`
.PHONY: check
check: test

# `make test` runs all tests
.PHONY: test
test: $(helm_deps)

# `make clean` deletes all test output
.PHONY: clean
clean:
	-rm $(helm_deps)

.PHONY: all
all: test

