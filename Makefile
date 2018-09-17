# Environment
package = tm-editor
prefix ?= /usr
utm_dir ?= ..

# Executables
pyrcc ?= pyrcc4

# Lang
tmlang = en_US.UTF-8

# Dependencies

corelibs = \
	$(utm_dir)/tmUtil/libtmutil.so \
	$(utm_dir)/tmXsd/libtmxsd.so \
	$(utm_dir)/tmTable/libtmtable.so \
	$(utm_dir)/tmGrammar/libtmgrammar.so

swiglibs = \
	$(utm_dir)/tmTable/_tmTable.so \
	$(utm_dir)/tmGrammar/_tmGrammar.so

swigmods = \
	$(utm_dir)/tmTable/tmTable.py \
	$(utm_dir)/tmGrammar/tmGrammar.py


.PHONY: all rcc clean distclean

all: rcc

# -----------------------------------------------------------------------------
#  Resource processing.
# -----------------------------------------------------------------------------
rcc: resource/share/$(package)/changelog resource/share/$(package)/copyright tmEditor/tmeditor_rc.py

# -----------------------------------------------------------------------------
#  Distribute a copy of the changelog.
# -----------------------------------------------------------------------------
resource/share/$(package)/changelog: changelog
	cp $< $@

# -----------------------------------------------------------------------------
#  Distribute a copy of copyright information.
# -----------------------------------------------------------------------------
resource/share/$(package)/copyright: copyright
	cp $< $@

# -----------------------------------------------------------------------------
#  Generating PyQT4 resource module.
# -----------------------------------------------------------------------------
tmEditor/tmeditor_rc.py: resource/tmEditor.rcc
	$(pyrcc) -o $@ $<

# -----------------------------------------------------------------------------
#
#  Install distribution and external libraries to $(prefix) location.
#  ==================================================================
#
#  prefix/
#  +-- bin/
#  |   `-- tm-editor --> wrapper shell script (generated)
#  +-- lib/
#  |   `-- tm-editor/
#  |       +-- tmEditor/ --> this python package
#  |       |   `-- *.py
#  |       +-- tmTable.py --> SWIG module copied from tmTable
#  |       +-- tmGrammar.py --> SWIG module copied from tmGrammar
#  |       +-- _tmTable.so --> SWIG library copied from tmTable
#  |       +-- _tmGrammar.so --> SWIG library copied from tmGrammar
#  |       +-- tmUtil.so --> core library copied from tmUtil
#  |       +-- tmXsd.so --> core library copied from tmXsd
#  |       +-- tmTable.so --> core library copied from tmTable
#  |       `-- tmGrammar.so --> core library copied from tmGrammar
#  `-- share/
#      +-- tm-editor/
#      |   `-- tm-editor/
#      |       `-- xsd/
#      |           +-- xsd-types/
#      |           |    `-- *.xsd --> XSD simple and complex types
#      |           `-- *.xsd --> XSD components for valiation
#      +-- doc/
#      |   `-- tm-editor/
#      |       `-- copyright --> copied from tmEditor
#      +-- applications/
#      |   `-- tm-editor.desktop --> freedesktop.org entry for graphical environments
#      `-- icons/
#          `-- hicolor/
#              `-- scalable/
#                  `-- apps/
#                      `-- tm-editor.svg --> applciation icon
# -----------------------------------------------------------------------------
install: all
	echo "//     building directory structure..."
	mkdir -p $(prefix)/bin
	mkdir -p $(prefix)/lib/$(package)
	mkdir -p $(prefix)/lib/$(package)/tmEditor
	mkdir -p $(prefix)/share/$(package)
	mkdir -p $(prefix)/share/$(package)/xsd
	mkdir -p $(prefix)/share/$(package)/xsd/xsd-type
	mkdir -p $(prefix)/share/doc/$(package)

	echo "//     generating executable wrapper..."
	echo "#!/bin/bash" > $(prefix)/bin/$(package)
	echo "export LD_LIBRARY_PATH=/usr/lib/$(package):\$$LD_LIBRARY_PATH" >> $(prefix)/bin/$(package)
	echo "export PYTHONPATH=/usr/lib/$(package):\$$PYTHONPATH" >> $(prefix)/bin/$(package)
	echo "export UTM_ROOT=/usr/share/$(package)" >> $(prefix)/bin/$(package)
	echo "export UTM_XSD_DIR=/usr/share/$(package)/xsd" >> $(prefix)/bin/$(package)
	echo "export LC_ALL=$(tmlang)" >> $(prefix)/bin/$(package)
	echo "/usr/lib/$(package)/$(package) \"\$$@\"" >> $(prefix)/bin/$(package)
	chmod +x $(prefix)/bin/$(package)

	echo "//     adding executable script..."
	cp scripts/$(package) $(prefix)/lib/$(package)
	chmod +x $(prefix)/lib/$(package)/$(package)

	echo "//     adding tmEditor package..."
	cp -r --parents $(shell find tmEditor -name '*.py') $(prefix)/lib/$(package)

	echo "//     adding core libraries..."
	cp $(corelibs) $(prefix)/lib/$(package)

	echo "//     adding SWIG python modules..."
	cp $(swigmods) $(prefix)/lib/$(package)

	echo "//     adding SWIG libraries..."```
	cp $(swiglibs) $(prefix)/lib/$(package)

	echo "//     adding shared files (generating directory tree)..."
	cp -r resource/share/* $(prefix)/share
	rm -rf `find $(prefix) -name .svn`
	cp copyright $(prefix)/share/doc/$(package)

	echo "//     adding XSD files..."
	cp $(tmxsd_dir)/*.xsd $(prefix)/share/$(package)/xsd
	cp $(tmxsd_dir)/xsd-type/*.xsd $(prefix)/share/$(package)/xsd/xsd-type

	echo "//     compressing changelog..."
	cp changelog  $(prefix)/share/doc/$(package)/changelog
	gzip -9 $(prefix)/share/doc/$(package)/changelog

	echo "//     compressing man page..."
	gzip -9 $(prefix)/share/man/man1/$(package).1

clean:
	rm -rf tmEditor/tmeditor_rc.py
	rm -rf `find tmEditor -name '*.pyc'`
	rm -rf `find tmEditor -name '*.pyo'`
	rm -rf `find tmEditor -name '__pycache__'`

distclean: clean
