#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
#print os.path.abspath('.')

__copyright__ = "Copyright (c) 2015, ubuntunux"
__license__ = """
Copyright (c) 2015, ubuntunux
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
__version__ = '0.1'

import sys

# log
import platform
from Utilities import getLogger
logger = getLogger('default', 'logs', False)
logger.info('Platform :', platform.platform())

# QT
from PyQt4 import QtCore, QtGui, QtOpenGL

# import custom library
from Render import Renderer

class Window(QtGui.QWidget):
    canExit = False

    def __init__(self):
        super(Window, self).__init__()
        logger.info("Create QT Window...")

        # opengl widget
        self.glWidget = GLWidget()

        # main layout
        mainlayout = QtGui.QHBoxLayout()

        # obj list
        list_widget = QtGui.QListWidget()
        list_widget.addItem("obj")

        # add buttons
        button = QtGui.QPushButton("Start")

        # add widgets
        mainlayout.addWidget(self.glWidget)
        mainlayout.addWidget(list_widget)
        mainlayout.addWidget(button)

        # set layouy & window
        self.setLayout(mainlayout)
        self.setWindowTitle("Hello GL")
        self.canExit = True

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        if self.canExit:
            # let the window close
            logger.info("Bye")
            event.accept()
        else:
            # exit ignore
            logger.info("Ignore exit")
            event.ignore()

class GLWidget(QtOpenGL.QGLWidget):
    init = False

    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        logger.info("Create QtOpenGL Widget...")

        self.lastPos = QtCore.QPoint()
        self.trolltechGreen = QtGui.QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
        self.trolltechPurple = QtGui.QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

        # get renderer
        self.renderer = Renderer()

    def minimumSizeHint(self):
        return QtCore.QSize(50, 50)

    def sizeHint(self):
        return QtCore.QSize(1024, 768)

    def update(self):
        self.updateGL()

    def initializeGL(self):
        # clear qt color
        self.qglClearColor(self.trolltechPurple.dark())

        # updateGL loop
        timer = QtCore.QTimer(self)
        self.connect(timer, QtCore.SIGNAL("timeout()"), self, QtCore.SLOT("updateGL()"))
        timer.start(0)

        # set renderer init
        self.renderer.initializeGL()

    def paintGL(self):
        # render scene
        self.renderer.renderScene()

    def resizeGL(self, width, height):
        # resize scene
        self.renderer.resizeScene(width, height)

    def mousePressEvent(self, event):
        self.lastPos = event.pos()
        eventButtons = event.buttons()
        if eventButtons & QtCore.Qt.LeftButton:
            pass
        elif eventButtons & QtCore.Qt.RightButton:
            pass

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        self.lastPos = event.pos()

    def keyPressEvent(self, e):
        #print e
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        # do stuff
        if self.canExit():
            event.accept()  # let the window close
        else:
            event.ignore()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
