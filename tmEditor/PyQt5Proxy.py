# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#
# Transitional PyQt wrapper supporting PyQt4 fallback for PyQt5 codebase.
# See also http://pyqt.sourceforge.net/Docs/PyQt5/pyqt4_differences.html
#

import logging

__all__ = ['QtCore', 'QtGui', 'QtWidgets', 'pyqt4_str', 'pyqt4_toPyObject', 'PyQt4FallbackMode', 'PyQtSignature']

try:
    PyQt4FallbackMode = False
    PyQtSignature = 'PyQt5'

    from PyQt5 import QtCore
    from PyQt5 import QtGui
    from PyQt5 import QtWidgets

except ImportError:
    PyQt4FallbackMode = True
    PyQtSignature = 'PyQt4'

    from PyQt4 import QtCore
    from PyQt4 import QtGui
    from PyQt4 import QtGui as QtWidgets

    QtCore.QSortFilterProxyModel = QtGui.QSortFilterProxyModel
    QtCore.QItemSelectionModel = QtGui.QItemSelectionModel

    # See http://pyqt.sourceforge.net/Docs/PyQt5/pyqt4_differences.html#qfiledialog
    QtWidgets.QFileDialog.getOpenFileName = QtGui.QFileDialog.getOpenFileNameAndFilter
    QtWidgets.QFileDialog.getOpenFileNames = QtGui.QFileDialog.getOpenFileNamesAndFilter
    QtWidgets.QFileDialog.getSaveFileName = QtGui.QFileDialog.getSaveFileNameAndFilter

    class QStandardPaths(object):
        DataLocation = QtGui.QDesktopServices.DataLocation
        @staticmethod
        def displayName(type):
            return QtGui.QDesktopServices.displayName(type)
        @staticmethod
        def writableLocation(type):
            return QtGui.QDesktopServices.storageLocation(type)

    QtCore.QStandardPaths = QStandardPaths

# -----------------------------------------------------------------------------
# PyQt4 fallback methods
# -----------------------------------------------------------------------------

def pyqt4_str(string):
    """PyQt4 fallback wrapper for QString conversion."""
    if PyQt4FallbackMode:
        return str(format(string, 's')) # fix unicode bug
    return str(string) # fix unicode bug

def pyqt4_toPyObject(variant):
    """PyQt4 fallback wrapper for QVariant conversion.
    See also http://pyqt.sourceforge.net/Docs/PyQt5/pyqt_qvariant.html#ref-qvariant."""
    if PyQt4FallbackMode:
        return variant.toPyObject()
    return variant
