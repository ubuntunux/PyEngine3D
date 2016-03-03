# Third-party library
from PyQt4 import QtCore, QtGui, QtOpenGL

from Core import coreManager, logger
from . import MainWindow
from Utilities import Singleton
from Render import renderer, shaderManager, materialManager
from Object import objectManager


#--------------------------------#
# CLASS : OpenGL Redering Widget
#--------------------------------#
class GLWidget(QtOpenGL.QGLWidget, Singleton):
    init = False

    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        logger.info("Create QtOpenGL Widget")

        self.lastPos = QtCore.QPoint()
        self.trolltechGreen = QtGui.QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
        self.trolltechPurple = QtGui.QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

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

        # initialize managers
        renderer.initialize()
        objectManager.initialize()
        shaderManager.initialize()
        materialManager.initialize()


    def paintGL(self):
        # render scene
        renderer.renderScene()

    def resizeGL(self, width, height):
        # resize scene
        renderer.resizeScene(width, height)