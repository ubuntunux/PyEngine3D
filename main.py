#!/usr/bin/env python
# -*- coding: utf-8 -*-
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


# log
import platform
from Utilities import Logger
logger = Logger()
logger.init('main', 'logs', )
logger.info('Platform :', platform.platform())

# QT
from PyQt4 import QtCore, QtGui, QtOpenGL

# PyOpenGL 3.0.1 introduces this convenience module...
from OpenGL.GLUT import *
from OpenGL.GLU import *
import Shader

# import custom library
from Object.Primitive import *
from Object.ObjLoader import *

class Window(QtGui.QWidget):
    canExit = False
    
    def __init__(self):
        super(Window, self).__init__()

        self.glWidget = GLWidget()
        mainLayout = QtGui.QHBoxLayout()
        # obj list
        list_widget = QtGui.QListWidget()
        list_widget.addItem("obj")
        
        button = QtGui.QPushButton("Start")
        mainLayout.addWidget(self.glWidget)
        mainLayout.addWidget(list_widget)
        mainLayout.addWidget(button)        
        
        self.setLayout(mainLayout)
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
    def __init__(self, parent=None):
        logger.info("GLWidget.__init__")
        super(GLWidget, self).__init__(parent)
        self.lastPos = QtCore.QPoint()
        
        # default shader
        self.shader = Shader.Shader()
        
        self.trolltechGreen = QtGui.QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
        self.trolltechPurple = QtGui.QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)
        self.init = False

    def minimumSizeHint(self):
        return QtCore.QSize(50, 50)

    def sizeHint(self):
        return QtCore.QSize(1024, 768)
    
    def update(self):
        self.updateGL()

    def initializeGL(self):
        logger.info("InitializeGL :", glGetDoublev(GL_VIEWPORT))        
        self.qglClearColor(self.trolltechPurple.dark())
        # set render environment
        glClearColor(0.0, 0.0, 0.0, 0.0)  # This Will Clear The Background Color To Black
        glClearDepth(1.0)  # Enables Clearing Of The Depth Buffer
        glDepthFunc(GL_LESS)  # The Type Of Depth Test To Do
        glEnable(GL_DEPTH_TEST)  # Enables Depth Testing
        glShadeModel(GL_SMOOTH)  # Enables Smooth Color Shading
        glEnable(GL_CULL_FACE)

        # Start - fixed pipline light setting
        glLightfv(GL_LIGHT0, GL_POSITION, (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        # End - fixed pipline light setting
        
        # initialize shader
        self.shader.init()
        
        # create object
        self.obj_Triangle = Triangle()
        self.obj_Square = Square()
        self.init = True        

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader.default_shader)
        # draw triangle
        self.obj_Triangle.translate(-1, 0, -6)
        self.obj_Triangle.draw()

        # draw square
        self.obj_Square.translate(1, 0, -6)
        self.obj_Square.draw()

    def resizeGL(self, width, height):
        logger.info("resizeGL")
        
        side = min(width, height)
        if side < 0:
            return

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, float(width) / float(height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def mousePressEvent(self, event):
        self.lastPos = event.pos()
        
        eventButtons = event.buttons()

        if eventButtons & QtCore.Qt.LeftButton:
            logger.info("Click - Left")
        elif eventButtons & QtCore.Qt.RightButton:
            logger.info("Click - Right")

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        self.lastPos = event.pos()
        
    def keyPressEvent(self, e):
        print e
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
            
    def closeEvent(self, event):
        logger.info("exit")
        # do stuff
        if self.canExit():
            event.accept() # let the window close
        else:
            event.ignore()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
