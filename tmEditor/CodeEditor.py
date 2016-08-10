# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from PyQt4 import QtCore
from PyQt4 import QtGui

"""Code editor widget derived from:
http://doc.qt.io/qt-4.8/qt-widgets-codeeditor-example.html

With bugfix for SHIFT+RETURN issue from:
http://stackoverflow.com/questions/6571035/qplaintextedit-change-shiftreturn-behaviour
http://www.jjoe64.com/2011/08/qplaintextedit-change-shiftreturn.html
"""

class CodeEditor(QtGui.QPlainTextEdit):
    """Source code editor widget."""

    def __init__(self, parent = None):
        super(CodeEditor, self).__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged[int].connect(self.updateLineNumberAreaWidth)
        self.updateRequest[QtCore.QRect, int].connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth()
        self.highlightCurrentLine()
        # self.document().setDocumentMargin(0)

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QtCore.Qt.lightGray)
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = QtCore.QString.number(blockNumber + 1)
                painter.setPen(QtCore.Qt.darkGray)
                font = painter.font()
                font.setWeight(QtGui.QFont.Bold)
                painter.setFont(font)
                painter.drawText(0, top, self.lineNumberArea.width()-3, self.fontMetrics().height(),
                                 QtCore.Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def lineNumberAreaWidth(self):
        digits = 1
        maximum = max(1, self.blockCount())
        while maximum >= 10:
            maximum /= 10
            digits += 1
        space = 8 + self.fontMetrics().width(QtCore.QChar('9')) * digits
        return space;

    def resizeEvent(self, event):
        super(CodeEditor, self).resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def updateLineNumberAreaWidth(self):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QtGui.QTextEdit.ExtraSelection()
            lineColor = QtGui.QColor(QtCore.Qt.yellow).lighter(170)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth()

    def keyPressEvent(self, event):
        """Bugfix, disables SHIFT+RETURN misbehaviour."""
        if (event.key() == QtCore.Qt.Key_Enter or event.key() == 16777220) and \
           ((event.modifiers() & QtCore.Qt.ShiftModifier) == QtCore.Qt.ShiftModifier):
            # clone object but without shift
            # current modifiers & all possible modifiers, but SHIFT,ALT,CTRL
            event = QtGui.QKeyEvent(
                event.type(), event.key(),
                event.modifiers() & QtCore.Qt.MetaModifier & QtCore.Qt.KeypadModifier,
                event.text(), event.isAutoRepeat(), event.count())
        super(CodeEditor, self).keyPressEvent(event)

class LineNumberArea(QtGui.QWidget):
    """Line number widget for code editor."""

    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QtCore.QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

if __name__ == '__main__':
    import sys, os
    app = QtGui.QApplication(sys.argv)
    editor = CodeEditor()
    editor.show();
    sys.exit(app.exec_())
