# Environment
shell=/bin/sh
prefix ?= /usr
rootdir ?= ..
package = tm-editor
version := $(shell python tmEditor/version.py --version)
release := $(shell python tmEditor/version.py --release)
pkgdir = $(package)-$(version)-$(release)
maintainer = Bernhard Arnold <bernhard.arnold@cern.ch>
url = http://globaltrigger.hephy.at/
timestamp := $(shell date)
arch := $(shell uname -p)
distro ?= linux

# for tarball target
tarballdir = tarball/$(pkgdir)-$(distro)-$(arch)

# Only execute on debian systems
debian_arch = $(shell dpkg --print-architecture)

# Executables
pyrcc4 = pyrcc4

# Directories
tmutil_dir = $(rootdir)/tmUtil
tmxsd_dir = $(rootdir)/tmXsd
tmtable_dir = $(rootdir)/tmTable
tmgrammar_dir = $(rootdir)/tmGrammar

# Lang
tmlang = en_US.UTF-8

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

title = "Trigger Menu Editor"
description = "Graphical editor for editing Level-1 trigger menu XML files."

.PHONY: all install rpm rpmbuild deb debbuild tar tarbuild clean rpmclean debclean

all: rcc

# -----------------------------------------------------------------------------
#  Resource processing.
# -----------------------------------------------------------------------------
rcc: resource/share/$(package)/changelog tmEditor/tmeditor_rc.py

# -----------------------------------------------------------------------------
#  Distribute a copy og the changelog.
# -----------------------------------------------------------------------------
resource/share/$(package)/changelog: changelog
	cp $< $@

# -----------------------------------------------------------------------------
#  Generating PyQT4 resource module.
# -----------------------------------------------------------------------------
tmEditor/tmeditor_rc.py: resource/tmEditor.rcc
	$(pyrcc4) -o $@ $<

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

	echo "//     adding SWIG libraries..."
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

# -----------------------------------------------------------------------------
#  Create a RPM package from scratch.
# -----------------------------------------------------------------------------
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
	cp -r tmEditor resource scripts copyright changelog rpm/$(package)-$(version)/.
	rm -rf $(find rpm/$(package)-$(version) -name '.svn')
	rm -rf $(find rpm/$(package)-$(version) -name '*.pyc')
	cd rpm && tar czf RPMBUILD/SOURCES/$(package)-$(version).tar.gz $(package)-$(version)
	echo "%define _topdir   $(shell pwd)/rpm/RPMBUILD" > rpm/$(package).spec
	echo "%define name      $(package)" >> rpm/$(package).spec
	echo "%define release   $(release)" >> rpm/$(package).spec
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
	echo "Requires:  python >= 2.6" >> rpm/$(package).spec
	echo "Requires:  python-argparse" >> rpm/$(package).spec
	echo "Requires:	 PyQt4 >= 4.6" >> rpm/$(package).spec
	echo "Requires:  glibc >= 2.4" >> rpm/$(package).spec
	echo "Requires:  xerces-c >= 3.0" >> rpm/$(package).spec
	echo "Requires:  gnome-icon-theme" >> rpm/$(package).spec
	echo >> rpm/$(package).spec
	echo "%description" >> rpm/$(package).spec
	echo "$(title)" >> rpm/$(package).spec
	echo " $(description)" >> rpm/$(package).spec
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
	# Generating *.pyc and *.pyo file lists.
	cd rpm/$(package)-$(version)-build && find . -type f -name '*.py' -printf "/usr/%Po\n" >> ../$(package).spec
	cd rpm/$(package)-$(version)-build && find . -type f -name '*.py' -printf "/usr/%Pc\n" >> ../$(package).spec
	mv rpm/$(package).spec rpm/RPMBUILD/SPECS/$(package).spec
	rpmbuild -v -bb rpm/RPMBUILD/SPECS/$(package).spec

# -----------------------------------------------------------------------------
#  Create a debian package from scratch.
# -----------------------------------------------------------------------------
deb: debbuild

debbuild: all
	rm -rf deb/$(pkgdir)
	mkdir -p deb/$(pkgdir)
	make -f Makefile install prefix=deb/$(pkgdir)/usr
	mkdir -p deb/$(pkgdir)/DEBIAN
	cp changelog deb/changelog.Debian
	echo "//     compressing changelogs..."
	gzip -9 deb/changelog.Debian
	mv deb/changelog.Debian.gz deb/$(pkgdir)/usr/share/doc/$(package)/.
	# Strip debug symbols from libraries (linitian complains).
	strip --strip-unneeded deb/$(pkgdir)/usr/lib/$(package)/*.so
	echo "//     writing DEBIAN control file..."
	echo "Package: $(package)" > deb/control
	echo "Version: $(version)-$(release)" >> deb/control
	echo "Architecture: $(debian_arch)"  >> deb/control
	echo "Maintainer: $(maintainer)" >> deb/control
	echo "Installed-Size: $(shell du -sk . | awk '{print $1}')" >> deb/control
	echo "Depends: python (>= 2.6), python-qt4 (>= 4.6), libc6 (>= 2.4), libxerces-c3.1 (>= 3.1), gnome-icon-theme" >> deb/control
	echo "Replaces: $(package)" >> deb/control
	echo "Provides: $(package)" >> deb/control
	echo "Section: gnome" >> deb/control
	echo "Priority: optional" >> deb/control
	echo "Homepage: $(url)" >> deb/control
	echo "Description: $(title)" >> deb/control
	echo " $(description)" >> deb/control
	mv deb/control deb/$(pkgdir)/DEBIAN/.
	echo "//     generateing DEBIAN package..."
	fakeroot dpkg-deb -Zgzip -b deb/$(pkgdir) deb/$(pkgdir)-$(debian_arch).deb

tar: tarbuild

tarbuild: all
	rm -rf $(tarballdir)
	mkdir -p $(tarballdir)
	mkdir -p $(tarballdir)/lib/tmeditor-$(version)
	@echo "//     writing README..."
	echo "tm-editor ${version}-${release} for ${distro} ${arch}" > $(tarballdir)/README
	echo >> $(tarballdir)/README
	echo 'Dependecies:' >> $(tarballdir)/README
	echo >> $(tarballdir)/README
	echo '$$ sudo yum install python python-argparse PyQt4 xerces-c gnome-icon-theme' >> $(tarballdir)/README
	echo >> $(tarballdir)/README
	echo 'Run:' >> $(tarballdir)/README
	echo >> $(tarballdir)/README
	echo '$$ ./tm-editor [file|url ...]' >> $(tarballdir)/README
	@echo "//     writing tm-editor wrapper..."
	echo '#!/bin/bash' > $(tarballdir)/$(package)
	echo >> $(tarballdir)/$(package)
	echo 'DIR="$$( cd "$$( dirname "$${BASH_SOURCE[0]}" )" && pwd )"' >> $(tarballdir)/$(package)
	echo 'UTM_DIR=$$DIR/lib/tmeditor-'$(version) >> $(tarballdir)/$(package)
	echo >> $(tarballdir)/$(package)
	echo '# Setup environment' >> $(tarballdir)/$(package)
	echo 'source $$UTM_DIR/setup.sh' >> $(tarballdir)/$(package)
	echo >> $(tarballdir)/$(package)
	echo '# Source the external lib dir (not provided on lxplus)' >> $(tarballdir)/$(package)
	echo 'export LD_LIBRARY_PATH=$$UTM_DIR/extern:$$LD_LIBRARY_PATH' >> $(tarballdir)/$(package)
	echo >> $(tarballdir)/$(package)
	echo '# Run editor' >> $(tarballdir)/$(package)
	echo 'tm-editor $$@' >> $(tarballdir)/$(package)
	echo >> $(tarballdir)/$(package)
	echo 'exit $$?' >> $(tarballdir)/$(package)
	chmod +x $(tarballdir)/$(package)
	cp ../setup.sh $(tarballdir)/lib/tmeditor-$(version)
	mkdir -p $(tarballdir)/lib/tmeditor-$(version)/extern
	cp $(shell find /usr -name 'libxerces-c-*.so') $(tarballdir)/lib/tmeditor-$(version)/extern
	mkdir -p $(tarballdir)/lib/tmeditor-$(version)/tmUtil
	cp -r ../tmUtil/libtmutil.so $(tarballdir)/lib/tmeditor-$(version)/tmUtil/
	mkdir -p $(tarballdir)/lib/tmeditor-$(version)/tmXsd
	cp -r ../tmXsd/libtmxsd.so $(tarballdir)/lib/tmeditor-$(version)/tmXsd/
	cp -r ../tmXsd/*.xsd $(tarballdir)/lib/tmeditor-$(version)/tmXsd/
	cp -r ../tmXsd/xsd-type $(tarballdir)/lib/tmeditor-$(version)/tmXsd/
	mkdir -p $(tarballdir)/lib/tmeditor-$(version)/tmTable
	cp -r ../tmTable/libtmtable.so ../tmTable/_tmTable.so ../tmTable/tmTable.py $(tarballdir)/lib/tmeditor-$(version)/tmTable/
	mkdir -p $(tarballdir)/lib/tmeditor-$(version)/tmGrammar
	cp -r ../tmGrammar/libtmgrammar.so ../tmGrammar/_tmGrammar.so ../tmGrammar/tmGrammar.py $(tarballdir)/lib/tmeditor-$(version)/tmGrammar/
	mkdir -p $(tarballdir)/lib/tmeditor-$(version)/tmEventSetup
	cp -r ../tmEventSetup/libtmeventsetup.so ../tmEventSetup/_tmEventSetup.so ../tmEventSetup/tmEventSetup.py $(tarballdir)/lib/tmeditor-$(version)/tmEventSetup/
	mkdir -p $(tarballdir)/lib/tmeditor-$(version)/tmEditor
	mkdir -p $(tarballdir)/lib/tmeditor-$(version)/tmEditor/scripts
	cp -r ../tmEditor/scripts/tm-editor $(tarballdir)/lib/tmeditor-$(version)/tmEditor/scripts
	cp -r -r --parents $(shell find ../tmEditor/tmEditor -name '*.py') $(tarballdir)/lib/tmeditor-$(version)/tmEditor
	cp -r ../tmEditor/changelog ../tmEditor/copyright ../tmEditor/README.md $(tarballdir)/lib/tmeditor-$(version)/tmEditor
	@echo "//     packing tarball..."
	cd tarball && tar czf $(pkgdir)-$(distro)-$(arch).tar.gz $(pkgdir)-$(distro)-$(arch)
	@echo "done."

clean:
	rm -rf tmEditor/tmeditor_rc.py
	rm -rf `find tmEditor -name '*.pyc'`
	rm -rf `find tmEditor -name '*.pyo'`

rpmclean:
	rm -rf rpm

debclean:
	rm -rf deb

tarclean:
	rm -rf tarball

distclean: clean rpmclean debclean
