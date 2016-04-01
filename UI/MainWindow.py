# standard library
import sys, traceback, os

# Third-party library
from PyQt4 import QtCore, QtGui, uic

from Utilities import Singleton
from UI import logger
from Core import *

UI_FILENAME = os.path.join(os.path.split(__file__)[0], "MainWindow.ui")

#----------------------#
# CLASS : Main Window
#----------------------#
class UIThread(QtCore.QThread):
    def __init__(self, cmdQueue):
        QtCore.QThread.__init__(self)
        self.running = True
        self.exitQueue = cmdQueue

    def run(self):
      while self.running:
          if not self.exitQueue.empty():
              if self.exitQueue.get() == CMD_CLOSE_UI:
                  self.running = False
                  self.emit( QtCore.SIGNAL('exit'), None)
                  break

#----------------------#
# CLASS : Main Window
#----------------------#
class MainWindow(QtGui.QMainWindow, Singleton):
    def __init__(self, cmdQueue, coreCmdQueue, cmdPipe):
        logger.info("Create MainWindow.")
        super(MainWindow, self).__init__()
        self.cmdQueue = cmdQueue
        self.coreCmdQueue = coreCmdQueue
        self.cmdPipe = cmdPipe

        try:
            # load ui file
            uic.loadUi(UI_FILENAME, self)
        except:
            self.exit(traceback.format_exc())

        try:
            # add primitive
            def addPrimitive(objType):
                print(objType)
                # queueCreateObject.put(objType)
                # recv
                #item = QtGui.QListWidgetItem(objName)
                #self.objectList.addItem(item)

            # binding button clicked
            btn = self.findChild(QtGui.QPushButton, "addTriangle")
            btn.clicked.connect(lambda: addPrimitive("Triangle"))

            btn = self.findChild(QtGui.QPushButton, "addQuad")
            btn.clicked.connect(lambda: addPrimitive("Quad"))

            # object list view
            self.objectList = self.findChild(QtGui.QListWidget, "objectList")
            QtCore.QObject.connect(self.objectList, QtCore.SIGNAL("itemClicked(QListWidgetItem *)"), self.fillObjProperty)

            # object property widget
            self.objPropertyTree = self.findChild(QtGui.QTreeWidget, "objPropertyTree")

            b1 = QtGui.QSpinBox()
            self.objPropertyTree.setItemWidget(self.objPropertyTree.topLevelItem(0), 1, b1) # add button to row 0, column

        except AttributeError:
            self.exit(traceback.format_exc())

        # ui main loop
        self.uiThread = UIThread(self.cmdQueue)
        self.connect( self.uiThread, QtCore.SIGNAL("exit"), self.exit )
        self.uiThread.start()

        # wait a UI_RUN message, and send success message
        PipeRecvSend(self.cmdPipe, CMD_UI_RUN, CMD_UI_RUN_OK)

    def fillObjProperty(self):
        pass

    def exit(self, *args):
        if args != () and args[0] != None:
            logger.info(*args)
        self.coreCmdQueue.put(CMD_CLOSE_APP)
        self.close()
        sys.exit()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.exit()

    def closeEvent(self, event):
        # let the window close
        logger.info("Bye")
        event.accept()

# process - QT Widget
def run_editor(cmdQueue, exitQueue, cmdPipe):
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow.instance(cmdQueue, exitQueue, cmdPipe)
    main_window.show()
    sys.exit(app.exec_())