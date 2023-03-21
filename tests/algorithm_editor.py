import argparse
import logging
import sys

from PyQt5 import QtWidgets

from tmEditor import tmeditor_rc
from tmEditor.core.Menu import Menu
from tmEditor.core import XmlDecoder
from tmEditor.gui.AlgorithmEditorDialog import AlgorithmEditorDialog


def load_menu():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    return XmlDecoder.load(args.filename)


def type_assert(value, type_):
    assert isinstance(value, type_), "{0} != {1} (expected)".format(type(value), type_)


def dump(value):
    logging.info("%s, %s", value, type(value))


def test_dialog():
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    menu = load_menu()
    app = QtWidgets.QApplication(sys.argv)

    window = AlgorithmEditorDialog(menu)
    window.show()
    app.exec_()

    type_assert(window.expression(), str)

    dump(window.expression())


if __name__ == "__main__":
    test_dialog()
