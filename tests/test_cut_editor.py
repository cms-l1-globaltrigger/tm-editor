from tmEditor.gui.CutEditorDialog import CutEditorDialog
from tmEditor.core.Algorithm import Cut
from tmEditor.core.Settings import CutSpecs
from tmEditor.core.Menu import Menu
from tmEditor.core import XmlDecoder
from tmEditor import tmeditor_rc

from tmEditor.PyQt5Proxy import QtWidgets

import argparse
import logging
import sys

def load_menu():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    return XmlDecoder.load(args.filename)

def type_assert(value, type_):
    assert isinstance(value, type_), "{0} != {1} (expected)".format(type(value), type_)

def dump(value):
    logging.info("%s  %s", value, type(value))

def test_dialog():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    menu = load_menu()
    app = QtWidgets.QApplication(sys.argv)

    window = CutEditorDialog(menu)
    window.setupCuts(CutSpecs)
    window.show()
    app.exec_()

    cut = window.newCut()
    print "name    :", cut.name
    print "object  :", cut.object
    print "type    :", cut.type
    print "minimum :", format(cut.minimum, '+23.16E')
    print "maximum :", format(cut.maximum, '+23.16E')
    print "data    :", cut.data

if __name__ == '__main__':
    test_dialog()
