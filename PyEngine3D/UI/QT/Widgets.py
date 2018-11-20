import sys
import traceback
import os
import time
from functools import partial

import PyQt4
from PyQt4 import Qt, QtCore, QtGui, uic
from PyQt4.Qt import *


class PopupBase(QtGui.QDialog):
    def __init__(self, parent=None, title="", size=[300, 200]):
        super(PopupBase, self).__init__(parent)
        self.set_window_title(title)
        self.resize(*size)

    def showEvent(self, event):
        geom = self.frameGeometry()
        geom.moveCenter(QtGui.QCursor.pos())
        self.setGeometry(geom)
        super(PopupBase, self).showEvent(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            super(PopupBase, self).keyPressEvent(event)


class InputDialogDemo(PopupBase):
    def __init__(self, parent=None, title="", size=[300, 200]):
        super(InputDialogDemo, self).__init__(parent, title, size)

        layout = QFormLayout()

        self.btn = QPushButton("Choose from list")
        self.btn.clicked.connect(self.getItem)
        self.le = QLineEdit()
        layout.addRow(self.btn, self.le)

        self.btn1 = QPushButton("get name")
        self.btn1.clicked.connect(self.gettext)
        self.le1 = QLineEdit()
        layout.addRow(self.btn1, self.le1)

        self.btn2 = QPushButton("Enter an integer")
        self.btn2.clicked.connect(self.getint)
        self.le2 = QLineEdit()
        layout.addRow(self.btn2, self.le2)

        self.setLayout(layout)
        self.set_window_title("Input Dialog demo")

    def getItem(self):
        items = ("C", "C++", "Java", "Python")
        item, ok = QInputDialog.getItem(self, "select input dialog", "list of languages", items, 0, False)
        if ok and item:
            self.le.setText(item)

    def gettext(self):
        text, ok = QInputDialog.getText(self, 'Text Input Dialog', 'Enter your name:')
        if ok:
            self.le1.setText(str(text))

    def getint(self):
        num, ok = QInputDialog.getInt(self, "integer input dualog", "enter a number")
        if ok:
            self.le2.setText(str(num))