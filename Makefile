PY_SCRIPTS = like.py
RST_FILES =

INSTDIR = $(HOME)/local/bin

SCRIPTS = like

all: $(SCRIPTS)

% : %.py
	rm -f $@
	cp $< $@
	chmod 0555 $@

.PHONY: install
install: all
	for f in $(SCRIPTS) ; do \
	    rm -f $(INSTDIR)/$$f ; \
	    cp -p $$f $(INSTDIR) ; \
	done

.PHONY: clean
clean: FORCE
	rm -f $(SCRIPTS)

.PHONY: FORCE
FORCE:
