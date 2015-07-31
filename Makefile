# Environment
prefix ?= /usr
rootdir ?= ..
package = tm-editor
version = 0.1.0
maintainer = Bernhard Arnold <bernhard.arnold@cern.ch>
url = http://globaltrigger.hephy.at/
timestamp := $(shell date)

# Only execute on debian systems
debian_arch = $(shell dpkg --print-architecture)

# Executables
pyrcc4 = pyrcc4

# Directories
tmutil_dir = $(rootdir)/tmUtil
tmxsd_dir = $(rootdir)/tmXsd
tmtable_dir = $(rootdir)/tmTable
tmgrammar_dir = $(rootdir)/tmGrammar

# Dependencies

corelibs = \
	$(tmutil_dir)/libtmutil.so \
	$(tmxsd_dir)/libtmxsd.so \
	$(tmtable_dir)/libtmtable.so \
	$(tmgrammar_dir)/libtmgrammar.so

swiglibs = \
	$(tmtable_dir)/_tmTable.so \
	$(tmgrammar_dir)/_tmGrammar.so

swigmods = \
	$(tmtable_dir)/tmTable.py \
	$(tmgrammar_dir)/tmGrammar.py

.PHONY: all install rpm rpmbuild deb debbuild clean rpmclean debclean

all: tmEditor/tmeditor_rc.py

tmEditor/tmeditor_rc.py: resource/tmeditor_rc.rcc
	$(pyrcc4) -o $@ $<

install: all
	echo "//     building directory structure..."
	mkdir -p $(prefix)/bin
	mkdir -p $(prefix)/lib/$(package)
	mkdir -p $(prefix)/lib/$(package)/tmEditor
	mkdir -p $(prefix)/share/$(package)
	mkdir -p $(prefix)/share/$(package)/xsd
	mkdir -p $(prefix)/share/$(package)/xsd/xsd-type
	mkdir -p $(prefix)/share/doc/$(package)
	mkdir -p $(prefix)/share/applications
	mkdir -p $(prefix)/share/icons/hicolor/scalable/apps

	echo "//     generating executable wrapper..."
	echo "#!/bin/bash" > $(prefix)/bin/$(package)
	echo "export LD_LIBRARY_PATH=/usr/lib/$(package):\$$LD_LIBRARY_PATH" >> $(prefix)/bin/$(package)
	echo "export PYTHONPATH=/usr/lib/$(package):\$$PYTHONPATH" >> $(prefix)/bin/$(package)
	echo "export TM_EDITOR_XSD_DIR=/usr/share/$(package)/xsd" >> $(prefix)/bin/$(package)
	echo "/usr/lib/$(package)/$(package) \"\$$@\"" >> $(prefix)/bin/$(package)
	chmod +x $(prefix)/bin/$(package)

	echo "//     adding executable script..."
	cp scripts/$(package) $(prefix)/lib/$(package)
	chmod +x $(prefix)/lib/$(package)/$(package)

	echo "//     adding tmEditor package..."
	cp tmEditor/*.py $(prefix)/lib/$(package)/tmEditor

	echo "//     adding core libraries..."
	cp $(corelibs) $(prefix)/lib/$(package)

	echo "//     adding SWIG python modules..."
	cp $(swigmods) $(prefix)/lib/$(package)

	echo "//     adding SWIG libraries..."
	cp $(swiglibs) $(prefix)/lib/$(package)

	echo "//     adding XSD files..."
	cp $(tmxsd_dir)/*.xsd $(prefix)/share/$(package)/xsd
	cp $(tmxsd_dir)/xsd-type/*.xsd $(prefix)/share/$(package)/xsd/xsd-type

	echo "//     adding various side files..."
	cp resource/tm-editor.desktop $(prefix)/share/applications
	cp resource/icons/identity.svg $(prefix)/share/icons/hicolor/scalable/apps/tm-editor.svg
	cp copyright $(prefix)/share/doc/$(package)

rpm: rpmbuild

rpmbuild: all
	rm -rf rpm/RPMBUILD
	mkdir -p rpm/RPMBUILD/BUILD
	mkdir -p rpm/RPMBUILD/RPMS
	mkdir -p rpm/RPMBUILD/SOURCES
	mkdir -p rpm/RPMBUILD/SPECS
	mkdir -p rpm/RPMBUILD/SRPMS
	make -f Makefile install prefix=rpm/$(package)-$(version)-build
	mkdir -p rpm/$(package)-$(version)
	cp Makefile rpm/$(package)-$(version)/.
	cp -r tmEditor resource scripts copyright rpm/$(package)-$(version)/.
	cd rpm && tar czf RPMBUILD/SOURCES/$(package)-$(version).tar.gz $(package)-$(version)
	echo "%define _topdir   $(shell pwd)/rpm/RPMBUILD" > rpm/$(package).spec
	echo "%define name      $(package)" >> rpm/$(package).spec
	echo "%define release   1" >> rpm/$(package).spec
	echo "%define version   $(version)" >> rpm/$(package).spec
	echo "%define buildroot %{_topdir}/%{name}-%{version}-root" >> rpm/$(package).spec
	echo >> rpm/$(package).spec
	echo "BuildRoot: %{buildroot}" >> rpm/$(package).spec
	echo "Summary:   Level-1 Global Trigger Menu Editor" >> rpm/$(package).spec
	echo "License:   proprietary" >> rpm/$(package).spec
	echo "Name:      %{name}" >> rpm/$(package).spec
	echo "Version:   %{version}" >> rpm/$(package).spec
	echo "Release:   %{release}" >> rpm/$(package).spec
	echo "Source:    %{name}-%{version}.tar.gz" >> rpm/$(package).spec
	echo "Prefix:    /usr" >> rpm/$(package).spec
	echo "Group:     Development/Tools" >> rpm/$(package).spec
	echo >> rpm/$(package).spec
	echo "%description" >> rpm/$(package).spec
	echo "a foobar app" >> rpm/$(package).spec
	echo >> rpm/$(package).spec
	echo "%prep" >> rpm/$(package).spec
	echo "%setup -q" >> rpm/$(package).spec
	echo >> rpm/$(package).spec
	echo "%build" >> rpm/$(package).spec
	echo "make rootdir=$(shell pwd)/.." >> rpm/$(package).spec
	echo >> rpm/$(package).spec
	echo "%install" >> rpm/$(package).spec
	echo "make install rootdir=$(shell pwd)/.. prefix=\$$RPM_BUILD_ROOT/usr" >> rpm/$(package).spec
	echo >> rpm/$(package).spec
	echo "%files" >> rpm/$(package).spec
	echo "%defattr(-,root,root)" >> rpm/$(package).spec
	cd rpm/$(package)-$(version)-build && find . -type f -printf "/usr/%P\n" >> ../$(package).spec
	mv rpm/$(package).spec rpm/RPMBUILD/SPECS/$(package).spec
	rpmbuild -v -bb --clean rpm/RPMBUILD/SPECS/$(package).spec

deb: debbuild

debbuild: all
	rm -rf deb/$(package)-$(version)
	mkdir -p deb/$(package)-$(version)
	make -f Makefile install prefix=deb/$(package)-$(version)/usr
	mkdir -p deb/$(package)-$(version)/DEBIAN
	echo "//     auto generate dummy changelog..."
	echo "$(package) ($VERSION) extra; urgency=low" > deb/changelog.DEBIAN
	echo > deb/changelog.DEBIAN
	echo "  * Added Changelog for compliance with debian rules." > deb/changelog.DEBIAN
	echo > deb/changelog.DEBIAN
	echo " -- $(maintainer)  $(timestamp)" > deb/changelog.DEBIAN
	echo "//     compressing changelogs..."
	gzip deb/changelog.DEBIAN
	mv deb/changelog.DEBIAN.gz deb/$(package)-$(version)/usr/share/doc/$(package)/.
	echo "//     calculating MD5 sums..."
	cd deb/$(package)-$(version) && md5sum $(shell find . -type f -printf "%P\n") > DEBIAN/md5sums
	echo "//     writing DEBIAN control file..."
	echo "Package: $(package)" > deb/control
	echo "Version: $(version)" >> deb/control
	echo "Architecture: $(debian_arch)"  >> deb/control
	echo "Maintainer: $(maintainer)" >> deb/control
	echo "Installed-Size: $(shell du -sk . | awk '{print $1}')" >> deb/control
	echo "Depends: python (>= 2.6), python-qt4 (>= 4.6), libc6 (>= 2.4), libxerces-c28 (>= 2.8)" >> deb/control
	echo "Replaces: $(package)" >> deb/control
	echo "Provides: $(package)" >> deb/control
	echo "Section: gnome" >> deb/control
	echo "Priority: optional" >> deb/control
	echo "Homepage: $(url)" >> deb/control
	echo "Description: Trigger Menu Editor" >> deb/control
	echo " Graphical editor for editing Level-1 trigger menu XML files." >> deb/control
	mv deb/control deb/$(package)-$(version)/DEBIAN/.
	echo "//     generateing DEBIAN package..."
	fakeroot dpkg-deb -Zgzip -b deb/$(package)-$(version) deb/$(package)-$(version)-$(debian_arch).deb

clean:
	rm -rf tmEditor/tmeditor_rc.py

rpmclean:
	rm -rf rpm

debclean:
	rm -rf deb

distclean: clean rpmclean debclean
