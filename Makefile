# Environment
package = tm-editor

# Executables
pyrcc ?= pyrcc4

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

clean:
	rm -rf tmEditor/tmeditor_rc.py
	rm -rf `find tmEditor -name '*.pyc'`
	rm -rf `find tmEditor -name '*.pyo'`
	rm -rf `find tmEditor -name '__pycache__'`

distclean: clean
