#!/usr/bin/env python
# coding=utf-8

# log
from Utilities.Logger import logger
logger.init('logtest', 'logs', False)

# import library
import sys, math, os
import time as timeModule
from PyQt4 import QtCore, QtGui, QtOpenGL

try:
    #PyGame
    import pygame
    from pygame.locals import *
    from pygame.constants import *
    pygame.init()

    # PyOpenGL 3.0.1 introduces this convenience module...
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    from OpenGL.GLU import *
    from OpenGL.GL.shaders import *
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(None, "OpenGL hellogl", "PyOpenGL must be installed to run this example.")
    sys.exit(1)

# import custom library
from Primitive import *
from ObjLoader import *

default_vertex_shader = '''
    varying vec3 normal;
    void main() {
        normal = gl_NormalMatrix * gl_Normal;
        gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    }'''

default_pixel_shader = '''
     varying vec3 normal;
    void main() {
        float intensity;
        vec4 color;
        vec3 n = normalize(normal);
        vec3 l = normalize(gl_LightSource[0].position).xyz;        
        intensity = saturate(dot(l, n));
        color = gl_LightSource[0].ambient + gl_LightSource[0].diffuse * intensity;
    
        gl_FragColor = color;
    }'''


class Window(QtGui.QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.glWidget = GLWidget()
        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(self.glWidget)        
        self.setLayout(mainLayout)
        self.setWindowTitle("Hello GL")

class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)

        self.object = 0
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0

        self.lastPos = QtCore.QPoint()

        self.trolltechGreen = QtGui.QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
        self.trolltechPurple = QtGui.QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

    def minimumSizeHint(self):
        return QtCore.QSize(50, 50)

    def sizeHint(self):
        return QtCore.QSize(1024, 768)
    
    self.updateGL()

    def initializeGL(self):
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

        # init shader
        self.default_shader = compileProgram(
            compileShader(default_vertex_shader, GL_VERTEX_SHADER),
            compileShader(default_pixel_shader, GL_FRAGMENT_SHADER), )

        print "Display : ", glGetDoublev(GL_VIEWPORT)

        # create object
        self.obj_Triangle = Triangle()
        self.obj_Square = Square()
        self.obj = OBJ(os.path.join("Mesh", "aaa.obj"), 1.0, True)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # set shader
        glUseProgram(self.default_shader)

        # draw triangle
        self.obj_Triangle.translate(-1, 0, -6)
        self.obj_Triangle.draw()

        # draw square
        self.obj_Square.translate(1, 0, -6)
        self.obj_Square.draw()

        # rotate obj
        glLoadIdentity()
        glTranslated(0.0, 0.0, -10.0)
        glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
        glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
        glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
        self.obj.draw()

    def resizeGL(self, width, height):
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

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & QtCore.Qt.LeftButton:
            self.setXRotation()
        elif event.buttons() & QtCore.Qt.RightButton:
            pass

        self.lastPos = event.pos()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
