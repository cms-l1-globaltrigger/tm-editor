from tmEditor.gui.CutEditorDialog import CutEditorDialog

from tmEditor.core.toolbox import CutSpecification
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
    window.show()
    app.exec_()

    type_assert(window.spec, CutSpecification)
    type_assert(window.name, str)
    type_assert(window.type, str)
    type_assert(window.object, str)
    type_assert(window.typename, str)
    type_assert(window.suffix, str)
    type_assert(window.minimum, float)
    type_assert(window.maximum, float)
    type_assert(window.data, str)

    dump(window.spec.__dict__)
    dump(window.name)
    dump(window.type)
    dump(window.object)
    dump(window.typename)
    dump(window.suffix)
    dump(window.minimum)
    dump(window.maximum)
    dump(window.data)

if __name__ == '__main__':
    test_dialog()
