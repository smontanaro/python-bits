PY_SCRIPTS = like.py watch.py
MODULES = suspendtracker.py
RST_FILES =

SCRIPTS = $(PY_SCRIPTS)
INSTDIR = $(HOME)/local/bin
MANINSTDIR = $(HOME)/local/share/man
VERSION = 1.0

### Usage:
#
# Source files are stored in SRCDIR.  If you have hand-written ReST
# documentation files, they live in RSTDIR.  The default 'all' target
# will generate output in BINDIR and MANDIR directories.

# Little, if anything, below here should need to be changed.

SCRIPTS = $(PY_SCRIPTS)
BINDIR = bin
SRCDIR = src
MANDIR = share/man/man1
RSTDIR = share/man/rst1

BIN_SCRIPTS = $(foreach s,$(SCRIPTS),$(BINDIR)/$(basename $(s)))
SRC_SCRIPTS = $(foreach s,$(SCRIPTS),$(SRCDIR)/$(s))
SRC_MODULES = $(foreach s,$(MODULES),$(SRCDIR)/$(s))
MAN_FILES = $(foreach s,$(SCRIPTS),$(MANDIR)/$(basename $(s)).1) \
	$(foreach s,$(RST_FILES),$(MANDIR)/$(basename $(s)).1)

.PHONY: all
all : bin man

.PHONY: bin
bin : $(BIN_SCRIPTS)

.PHONY: man
man : $(MAN_FILES)

.PHONY: lint
lint : FORCE
	-pylint $(SRC_SCRIPTS) $(SRC_MODULES)
	-MYPYPATH=typeshed mypy $(SRC_SCRIPTS) $(SRC_MODULES)
	-bandit $(SRC_SCRIPTS) $(SRC_MODULES)

$(BINDIR)/% : $(SRCDIR)/%.py
	mkdir -p $(BINDIR)
	rm -f $@
	sed -e 's/@@VERSION@@/$(VERSION)/g' $< > $@
	chmod 0555 $@

$(MANDIR)/%.1 : $(RSTDIR)/%.rst
	mkdir -p $(MANDIR)
	rm -f $@
	rst2man.py < $< \
	| sed -e '/^\.de1 rstReportMargin/,/^\.\./d' \
	      -e '/^\.de1 INDENT/,/^\.\./d' \
	      -e '/^\.de UNINDENT/,/^\.\./d' \
	| egrep -v '^\.(UN)?INDENT' > $@
	chmod 0444 $@

$(MANDIR)/%.1 : $(SRCDIR)/%.py
	mkdir -p $(MANDIR)
	rm -f $@
	python $< -h 2>&1 | sed -e 's/@@VERSION@@/$(VERSION)/g' | rst2man.py > $@
	chmod 0444 $@

.PHONY: install
install: all
	for f in $(BINDIR)/* ; do \
	    rm -f $(INSTDIR)/`basename $$f` ; \
	    cp -p $$f $(INSTDIR) ; \
	done
	mkdir -p $(MANINSTDIR)/man1
	for f in $(MANDIR)/* ; do \
	    rm -f $(MANINSTDIR)/man1/`basename $$f` ; \
	    cp -p $$f $(MANINSTDIR)/man1 ; \
	done

.PHONY: clean
clean: FORCE
	rm -f $(BIN_SCRIPTS)
	rm -f $(MAN_FILES)

.PHONY: FORCE
FORCE:
