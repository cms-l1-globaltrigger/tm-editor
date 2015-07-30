#!/bin/bash
#
# Building a standalone debian package from scratch (as python distutils are
# are of somehow limited use in this particular case).
#

PACKAGE=tm-editor
VERSION=0.1.0
MAINTAINER="Bernhard Arnold <bernhard.arnold@cern.ch>"
DATETIME=`date`
URL=http://globaltrigger.hephy.at/
INSTALLED_SIZE=0
ARCH=`dpkg --print-architecture`

CWD=`pwd`
TARGET_DIR=deb
BASE_DIR=$TARGET_DIR/$PACKAGE-$VERSION

TM_UTIL_DIR=../tmUtil
TM_XSD_DIR=../tmXsd
TM_TABLE_DIR=../tmTable
TM_GRAMMAR_DIR=../tmGrammar


function report {
    echo "//    $@"
}

function copy {
    report "copying $@"
    cp -rv "$@" || exit 1
}

rm -rfv $BASE_DIR

report "generating directories..."
mkdir -pv deb
mkdir -pv $BASE_DIR/DEBIAN
mkdir -pv $BASE_DIR/usr/bin
mkdir -pv $BASE_DIR/usr/lib/$PACKAGE
mkdir -pv $BASE_DIR/usr/lib/$PACKAGE/tmEditor
mkdir -pv $BASE_DIR/usr/share/$PACKAGE
mkdir -pv $BASE_DIR/usr/share/$PACKAGE/xsd
mkdir -pv $BASE_DIR/usr/share/$PACKAGE/xsd/xsd-type
mkdir -pv $BASE_DIR/usr/share/$PACKAGE/xsd/xsd-type
mkdir -pv $BASE_DIR/usr/share/doc/$PACKAGE
mkdir -pv $BASE_DIR/usr/share/applications
mkdir -pv $BASE_DIR/usr/share/icons/hicolor/scalable/apps

report "starting popolating directories..."

report "generating executable wrapper..."
cat > $BASE_DIR/usr/bin/$PACKAGE <<EOF
#!/bin/bash
export LD_LIBRARY_PATH=/usr/lib/$PACKAGE:\$LD_LIBRARY_PATH
export PYTHONPATH=/usr/lib/$PACKAGE:\$PYTHONPATH
export TM_EDITOR_XSD_DIR=/usr/share/$PACKAGE/xsd
/usr/lib/$PACKAGE/$PACKAGE "\$@"
EOF
chmod +x $BASE_DIR/usr/bin/$PACKAGE

report "adding executable script..."
copy scripts/$PACKAGE $BASE_DIR/usr/lib/$PACKAGE
chmod +x $BASE_DIR/usr/lib/$PACKAGE/$PACKAGE

report "adding tmEditor package..."
copy tmEditor/*.py $BASE_DIR/usr/lib/$PACKAGE/tmEditor

report "adding SWIG modules..."
copy $TM_TABLE_DIR/tmTable.py $BASE_DIR/usr/lib/$PACKAGE
copy $TM_GRAMMAR_DIR/tmGrammar.py $BASE_DIR/usr/lib/$PACKAGE

report "adding SWIG libraries..."
copy $TM_TABLE_DIR/_tmTable.so $BASE_DIR/usr/lib/$PACKAGE
copy $TM_GRAMMAR_DIR/_tmGrammar.so $BASE_DIR/usr/lib/$PACKAGE

report "adding core libraries..."
copy $TM_UTIL_DIR/libtmutil.so $BASE_DIR/usr/lib/$PACKAGE
copy $TM_XSD_DIR/libtmxsd.so $BASE_DIR/usr/lib/$PACKAGE
copy $TM_TABLE_DIR/libtmtable.so $BASE_DIR/usr/lib/$PACKAGE
copy $TM_GRAMMAR_DIR/libtmgrammar.so $BASE_DIR/usr/lib/$PACKAGE

report "adding XSD files..."
copy $TM_XSD_DIR/*.xsd $BASE_DIR/usr/share/$PACKAGE/xsd
copy $TM_XSD_DIR/xsd-type/*.xsd $BASE_DIR/usr/share/$PACKAGE/xsd/xsd-type

report "adding various side files..."
copy resource/tm-editor.desktop $BASE_DIR/usr/share/applications
copy resource/icons/identity.svg $BASE_DIR/usr/share/icons/hicolor/scalable/apps/tm-editor.svg
copy copyright $BASE_DIR/usr/share/doc/$PACKAGE

report "adding additional python modules for python < 2.7..."
copy /usr/lib/python2.7/argparse.py $BASE_DIR/usr/lib/$PACKAGE

report "auto generate dummy changelog..."
cat > $BASE_DIR/usr/share/doc/$PACKAGE/changelog.DEBIAN <<EOF
$PACKAGE ($VERSION) extra; urgency=low

  * Added Changelog for compliance with debian rules.

 -- $MAINTAINER  $DATETIME
EOF

report "compressing changelogs..."
gzip $BASE_DIR/usr/share/doc/$PACKAGE/changelog.DEBIAN

cd $BASE_DIR
report "fetching installation files list..."
ALL_FILES=`find . -type f -printf "%P\n"`
report "calculating MD5 sums for all files..."
md5sum $ALL_FILES > DEBIAN/md5sums || exit 1
cd $CWD

report "calculating installation size..."
INSTALLED_SIZE=`du -sk . | awk '{print $1}'`

report "writing DEBIAN control file..."
cat > $BASE_DIR/DEBIAN/control <<EOF
Package: $PACKAGE
Version: $VERSION
Architecture: $ARCH
Maintainer: $MAINTAINER
Installed-Size: $INSTALLED_SIZE
Depends: python (>= 2.6), python-qt4 (>= 4.6), libc6 (>= 2.4), libxerces-c28 (>= 2.8)
Replaces: $PACKAGE
Provides: $PACKAGE
Section: gnome
Priority: optional
Homepage: $URL
Description: Trigger Menu Editor
 Graphical editor for editing Level-1 trigger menu XML files.
EOF

report "generateing DEBIAN package..."
fakeroot dpkg-deb -Zgzip -b $BASE_DIR $TARGET_DIR/$PACKAGE-$VERSION-$ARCH.deb || exit 1

report "success."
