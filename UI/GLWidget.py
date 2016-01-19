# Third-party library
from PyQt4 import QtCore, QtGui, QtOpenGL

from __main__ import logger
from . import MainWindow
from Utilities import Singleton
from Render import Renderer, ShaderManager, MaterialManager
from Object import ObjectManager


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
        Renderer.initialize()
        ObjectManager.initialize()
        ShaderManager.initialize()
        MaterialManager.initialize()

        # on_addPrimitive
        def on_addPrimitive(objName):
            item = QtGui.QListWidgetItem(objName)
            main_window = MainWindow.MainWindow.instance()
            main_window.objectList.addItem(item)

        # binding - callback function
        ObjectManager.bind_addPrimitive(on_addPrimitive)

    # addPrimitive
    def addPrimitive(self, objType):
        ObjectManager.addPrimitive(objType)

    def paintGL(self):
        # render scene
        Renderer.renderScene()

    def resizeGL(self, width, height):
        # resize scene
        Renderer.resizeScene(width, height)

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
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()