# Executables
QT_PYRCC4 = pyrcc4


all: tmEditor/tmeditor_rc.py

tmEditor/tmeditor_rc.py: resource/tmeditor_rc.rcc
	$(QT_PYRCC4) -o $@ $<
