# standard library
import sys, traceback, os, time

# Third-party library
import PyQt4
from PyQt4 import Qt, QtCore, QtGui, uic

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
                cmd = self.exitQueue.get()
                if type(cmd) is tuple:
                    cmd, value = cmd
                # process
                if cmd == CMD_CLOSE_UI:
                    self.running = False
                    self.emit( QtCore.SIGNAL('exit'), None)
                elif cmd == CMD_RECV_PRIMITIVEINFOS:
                    self.emit( QtCore.SIGNAL('RECV_PRIMITIVEINFOS'), value)


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
            # binding button clicked
            btn = self.findChild(QtGui.QPushButton, "add_Triangle")
            btn.clicked.connect(lambda: self.addPrimitive(CMD_ADD_TRIANGLE))

            btn = self.findChild(QtGui.QPushButton, "add_Quad")
            btn.clicked.connect(lambda: self.addPrimitive(CMD_ADD_QUAD))

            btn = self.findChild(QtGui.QPushButton, "add_Cube")
            btn.clicked.connect(lambda: self.addPrimitive(CMD_ADD_CUBE))

            # object list view
            self.objectList = self.findChild(QtGui.QListWidget, "objectList")
            QtCore.QObject.connect(self.objectList, QtCore.SIGNAL("itemClicked(QListWidgetItem *)"), self.fillObjProperty)

            # object property widget
            self.objPropertyTree = self.findChild(QtGui.QTreeWidget, "objPropertyTree")

            # test
            for item in self.objPropertyTree.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
                print(item.text(0), item.text(1))

        except AttributeError:
            self.exit(traceback.format_exc())

        # ui main loop
        self.uiThread = UIThread(self.cmdQueue)
        self.connect( self.uiThread, QtCore.SIGNAL("exit"), self.exit )
        self.connect( self.uiThread, QtCore.SIGNAL("RECV_PRIMITIVEINFOS"), self.recvPrimitiveInfo )
        self.uiThread.start()

        # wait a UI_RUN message, and send success message
        PipeRecvSend(self.cmdPipe, CMD_UI_RUN, CMD_UI_RUN_OK)

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

    #--------------------#
    # Commands
    #--------------------#
    # add primitive
    def addPrimitive(self, objType):
        if objType > CMD_ADD_PRIMITIVE_START and objType < CMD_ADD_PRIMITIVE_END:
            # send message
            self.coreCmdQueue.put(objType)

    def recvPrimitiveInfo(self, objInfo):
        item = QtGui.QListWidgetItem(objInfo['name'])
        self.objectList.addItem(item)

    def fillObjProperty(self, inst):
        objName = inst.text()
        for item in self.objPropertyTree.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            print(item.text(0), item.text(1))

# process - QT Widget
def run_editor(cmdQueue, exitQueue, cmdPipe):
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow.instance(cmdQueue, exitQueue, cmdPipe)
    main_window.show()
    sys.exit(app.exec_())