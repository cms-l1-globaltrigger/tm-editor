from tmEditor.gui.ObjectEditorDialog import ObjectEditorDialog

from tmEditor.core.Menu import Menu
from tmEditor.core import XmlDecoder
from tmEditor import tmeditor_rc

from PyQt5 import QtWidgets

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
    logging.info("%s, %s", value, type(value))

def test_dialog():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    menu = load_menu()
    app = QtWidgets.QApplication(sys.argv)

    window = ObjectEditorDialog(menu)
    window.show()
    app.exec_()

    type_assert(window.objectType(), str)
    type_assert(window.comparisonOperator(), str)
    type_assert(window.threshold(), float)
    type_assert(window.bxOffset(), int)

    dump(window.objectType())
    dump(window.comparisonOperator())
    dump(window.threshold())
    dump(window.bxOffset())

    dump(window.selectedCuts())
    dump(window.expression())


if __name__ == '__main__':
    test_dialog()
