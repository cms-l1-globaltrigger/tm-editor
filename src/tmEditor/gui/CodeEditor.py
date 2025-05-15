"""Code editor widget derived from:
http://doc.qt.io/qt-4.8/qt-widgets-codeeditor-example.html

With bugfix for SHIFT+RETURN issue from:
http://stackoverflow.com/questions/6571035/qplaintextedit-change-shiftreturn-behaviour
http://www.jjoe64.com/2011/08/qplaintextedit-change-shiftreturn.html
"""

import string
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

__all__ = ["CodeEditor"]


class CodeEditor(QtWidgets.QPlainTextEdit):
    """Source code editor widget."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth()
        self.highlightCurrentLine()
        # Setup font hints for monospace/typewriter
        font = QtGui.QFont("Monospace")
        font.setStyleHint(font.StyleHint.Monospace)
        self.setFont(font)
        # self.document().setDocumentMargin(0)

    @QtCore.Slot(QtGui.QPaintEvent)
    def lineNumberAreaPaintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QtCore.Qt.GlobalColor.lightGray)
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = format(blockNumber + 1, "d")
                painter.setPen(QtCore.Qt.GlobalColor.darkGray)
                font = painter.font()
                font.setWeight(font.Weight.Bold)
                painter.setFont(font)
                painter.drawText(0, top, self.lineNumberArea.width()-3, self.fontMetrics().height(),
                                 QtCore.Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def lineNumberAreaWidth(self) -> int:
        digits: int = 1
        maximum = float(max(1, self.blockCount()))
        while maximum >= 10.0:
            maximum /= 10.0
            digits += 1
        space = 8 + max([self.fontMetrics().boundingRect(c).width() for c in string.digits]) * digits
        return space

    @QtCore.Slot(QtGui.QResizeEvent)
    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    @QtCore.Slot()
    def updateLineNumberAreaWidth(self) -> None:
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    @QtCore.Slot()
    def highlightCurrentLine(self) -> None:
        extraSelections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            lineColor = QtGui.QColor(QtCore.Qt.GlobalColor.yellow).lighter(170)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def updateLineNumberArea(self, rect: QtCore.QRect, dy: int) -> None:
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth()

    @QtCore.Slot(QtGui.QKeyEvent)
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Bugfix, disables SHIFT+RETURN misbehaviour."""
        if (event.key() == QtCore.Qt.Key.Key_Enter or event.key() == 16777220) and \
           ((event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier) == QtCore.Qt.KeyboardModifier.ShiftModifier):
            # clone object but without shift
            # current modifiers & all possible modifiers, but SHIFT,ALT,CTRL
            event = QtGui.QKeyEvent(
                event.type(), event.key(),
                event.modifiers() & QtCore.Qt.KeyboardModifier.MetaModifier & QtCore.Qt.KeyboardModifier.KeypadModifier,
                event.text(), event.isAutoRepeat(), event.count()
            )
        super().keyPressEvent(event)


class LineNumberArea(QtWidgets.QWidget):
    """Line number widget for code editor."""

    def __init__(self, editor: CodeEditor) -> None:
        super().__init__(editor)
        self.codeEditor: CodeEditor = editor

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    @QtCore.Slot(QtGui.QPaintEvent)
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        self.codeEditor.lineNumberAreaPaintEvent(event)
