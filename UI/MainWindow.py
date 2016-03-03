# standard library
import sys, traceback, os

# Third-party library
from PyQt4 import QtCore, QtGui, uic

from Core import coreManager, logger
from Utilities import Singleton
from UI.GLWidget import GLWidget
from Object import objectManager, Triangle, Quad


UI_FILENAME = os.path.join(os.path.split(__file__)[0], "MainWindow.ui")


#----------------------#
# CLASS : Main Window
#----------------------#
class MainWindow(QtGui.QMainWindow, Singleton):
    def __init__(self):
        logger.info("Create MainWindow.")
        super(MainWindow, self).__init__()
        self.inited = True
        # regist
        coreManager.regist("Main Window", self)

        try:
            # load ui file
            uic.loadUi(UI_FILENAME, self)
        except:
            self.exit(traceback.format_exc())

        try:
            # add opengl widget
            layout = self.findChild(QtGui.QFormLayout, "glWidget")
            glWidget = GLWidget.instance()
            layout.addWidget(glWidget)

            # add primitive
            def addPrimitive(objType):
                objectManager.addPrimitive(objType)

            # binding button clicked
            btn = self.findChild(QtGui.QPushButton, "addTriangle")
            btn.clicked.connect(lambda: addPrimitive(Triangle))

            btn = self.findChild(QtGui.QPushButton, "addQuad")
            btn.clicked.connect(lambda: addPrimitive(Quad))

            # object list view
            self.objectList = self.findChild(QtGui.QListWidget, "objectList")
            QtCore.QObject.connect(self.objectList, QtCore.SIGNAL("itemClicked(QListWidgetItem *)"), self.fillObjProperty)

            # object property widget
            self.objPropertyTree = self.findChild(QtGui.QTreeWidget, "objPropertyTree")

            b1 = QtGui.QSpinBox()
            self.objPropertyTree.setItemWidget(self.objPropertyTree.topLevelItem(0), 1, b1) # add button to row 0, column

        except AttributeError:
            self.exit(traceback.format_exc())


    def fillObjProperty(self):
        pass


    def exit(self, *args):
        logger.info(*args)
        self.close()
        sys.exit()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        # let the window close
        logger.info("Bye")
        event.accept()