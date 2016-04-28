# standard library
import sys, traceback, os, time, traceback

# Third-party library
import PyQt4
from PyQt4 import Qt, QtCore, QtGui, uic
import numpy

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
        self.cmdQueue = cmdQueue
        self.isFillobjPropertyTree = False

    def run(self):
        while self.running:
            if not self.cmdQueue.empty():
                cmd = self.cmdQueue.get()
                value = None

                # check type for tuple - (cmd, value)
                if type(cmd) is tuple:
                    cmd, value = cmd

                logger.info("GUI Command Queue (%d, %s)" % (cmd, value))

                # process
                if cmd == CMD_CLOSE_UI:
                    self.running = False
                    self.emit( QtCore.SIGNAL('exit'), None)
                elif cmd == CMD_SEND_PRIMITIVENAME:
                    self.emit( QtCore.SIGNAL('CMD_SEND_PRIMITIVENAME'), value)
                elif cmd == CMD_SEND_PRIMITIVEINFOS:
                    self.emit( QtCore.SIGNAL('CMD_SEND_PRIMITIVEINFOS'), value)



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
            QtCore.QObject.connect(self.objectList, QtCore.SIGNAL("itemClicked(QListWidgetItem *)"), self.selectObject)

            # object property widget
            self.objPropertyTree = self.findChild(QtGui.QTreeWidget, "objPropertyTree")
            # hook editable event
            self.objPropertyTree.setEditTriggers(self.objPropertyTree.NoEditTriggers)
            # set object property events
            self.objPropertyTree.itemSelectionChanged.connect(self.checkEdit)
            self.objPropertyTree.itemClicked.connect(self.checkEdit)
            self.objPropertyTree.itemChanged.connect(self.objPropertyChanged)

        except AttributeError:
            self.exit(traceback.format_exc())

        # ui main loop
        self.uiThread = UIThread(self.cmdQueue)
        self.connect( self.uiThread, QtCore.SIGNAL("exit"), self.exit )
        self.connect( self.uiThread, QtCore.SIGNAL("CMD_SEND_PRIMITIVENAME"), self.addPrimitiveName )
        self.connect( self.uiThread, QtCore.SIGNAL("CMD_SEND_PRIMITIVEINFOS"), self.fillPrimitiveInfo )
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

    # on closed event
    def closeEvent(self, event):
        # let the window close
        logger.info("Bye")
        event.accept()
        self.exit()

    #--------------------#
    # Propery Tree Widget
    #--------------------#
    # in your connected slot, you can implement any edit-or-not-logic. you want
    def checkEdit(self, item=None, column=0):
        if item == None:
            item = self.objPropertyTree.currentItem()
            column = self.objPropertyTree.currentColumn()

        # e.g. to allow editing only of column 1:
        if column == 1 and item.childCount() == 0:
            self.objPropertyTree.editItem(item, column)

    def objPropertyChanged(self, item, column):
        # check object property initialize or not
        if not self.isFillobjPropertyTree:
            try:
                # check value chaned
                if item.oldValue == item.text(1):
                    return

                item.oldValue = item.text(1)
                propertyName = None
                value = item.dataType(item.text(1))

                # check array type, then combine components
                parent = item.parent()
                if type(parent) == QtGui.QTreeWidgetItem and parent.dataType in (tuple, list, numpy.ndarray):
                    propertyName = parent.text(0)
                    value = []
                    for i in range(parent.childCount()):
                        child = parent.child(i)
                        value.append(child.dataType(child.text(1)))
                    # numpy array
                    if parent.dataType == numpy.ndarray:
                        value = numpy.array(value)
                    # list or tuple
                    else:
                        value = parent.dataType(value)
                else:
                    propertyName = item.text(0)
                    value = item.dataType(child.text(1))
                # send data
                currentObjectName = self.objectList.currentItem().text()
                self.coreCmdQueue.put((CMD_SET_PRIMITIVEINFO, (currentObjectName, propertyName, value)))
            except:
                print(traceback.format_exc())
                # failed to convert string to dataType, so restore to old value
                item.setText(1, item.oldValue)


    def addProperty(self, parent, name, value):
        item = QtGui.QTreeWidgetItem(parent)
        item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        item.setExpanded(True)
        item.setText(0, name)
        item.dataType = type(value)
        item.oldValue = None

        if item.dataType == bool:
            item.setCheckState(1, QtCore.Qt.Checked if value else QtCore.Qt.Unhecked)
        elif item.dataType in (tuple, list, numpy.ndarray) :
            for i, itemValue in enumerate(value):
                self.addProperty(item, "[%d]" % i, itemValue)
        else:
            item.setText(1, str(value))
        item.oldValue = item.text(1)

    # objectList selected event
    def selectObject(self, inst):
        selectedObjectName = inst.text()
        # request selected object infomation to fill property widget
        self.coreCmdQueue.put((CMD_REQUEST_PRIMITIVEINFOS, selectedObjectName))

    # SIGNAL - CMD_SEND_PRIMITIVEINFOS_TO_GUI
    def fillPrimitiveInfo(self, objInfo):
        self.isFillobjPropertyTree = True
        # clear property widget
        self.objPropertyTree.clear()
        # fill properties of selected object
        for valueName in objInfo.keys():
            self.addProperty(self.objPropertyTree, valueName, objInfo[valueName])
        self.isFillobjPropertyTree = False

    def showProperties(self):
        for item in self.objPropertyTree.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            print(item.text(0), item.text(1))

    #--------------------#
    # Object List Widget
    #--------------------#
    # SIGNAL - CMD_SEND_PRIMITIVENAME_TO_GUI
    def addPrimitiveName(self, objName):
        # add object name to list
        item = QtGui.QListWidgetItem(objName)
        self.objectList.addItem(item)

    #--------------------#
    # Commands
    #--------------------#
    # add primitive
    def addPrimitive(self, objType):
        if objType > CMD_ADD_PRIMITIVE_START and objType < CMD_ADD_PRIMITIVE_END:
            self.coreCmdQueue.put(objType) # send message and receive


# process - QT Widget
def run_editor(cmdQueue, coreCmdQueue, cmdPipe):
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow.instance(cmdQueue, coreCmdQueue, cmdPipe)
    main_window.show()
    sys.exit(app.exec_())
