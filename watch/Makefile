
PYFILES := $(shell find . -name '*.py')

lint : $(PYFILES)
	pylint --disable=too-many-ancestors,missing-docstring,invalid-name $(PYFILES) ; pyflakes $(PYFILES)

.PHONY : lint
