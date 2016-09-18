# standard library
import sys, traceback, os, time, traceback
from functools import partial

# Third-party library
import PyQt4
from PyQt4 import Qt, QtCore, QtGui, uic
import numpy

from Utilities import Singleton
from UI import logger
from Core import *

UI_FILENAME = os.path.join(os.path.split(__file__)[0], "MainWindow.ui")


def findTreeItem(parentItem, findItemName):
    if type(parentItem) == QtGui.QTreeWidget:
        for item in parentItem.findItems("", QtCore.Qt.MatchContains):
            if item.text(0) == findItemName:
                return item
    elif type(parentItem) == QtGui.QTreeWidgetItem:
        for i in range(parentItem.childCount()):
            item = parentItem.child(i)
            if item.text(0) == findItemName:
                return item
    return None


class UIThread(QtCore.QThread):
    def __init__(self, cmdQueue):
        QtCore.QThread.__init__(self)
        self.running = True
        self.cmdQueue = cmdQueue

        self.limitDelta = 1.0 / 60.0  # 60fps
        self.delta = 0.0
        self.lastTime = 0.0

    def run(self):
        self.lastTime = time.time()
        while self.running:
            # Timer
            self.delta = time.time() - self.lastTime
            if self.delta < self.limitDelta:
                time.sleep(self.limitDelta - self.delta)
            # print(1.0/(time.time() - self.lastTime))
            self.lastTime = time.time()

            # Process recieved queues
            if not self.cmdQueue.empty():
                # receive value must be tuple type
                cmd, value = self.cmdQueue.get()
                cmdName = getCommandName(cmd)
                # recieved queues
                if cmd == CMD_CLOSE_UI:
                    self.running = False
                # call binded signal event
                self.emit(QtCore.SIGNAL(cmdName), value)


class MainWindow(QtGui.QMainWindow, Singleton):
    def __init__(self, cmdQueue, coreCmdQueue, cmdPipe):
        logger.info("Create MainWindow.")
        super(MainWindow, self).__init__()
        self.cmdQueue = cmdQueue
        self.coreCmdQueue = coreCmdQueue
        self.cmdPipe = cmdPipe
        self.isFillobjPropertyTree = False

        # load ui file
        uic.loadUi(UI_FILENAME, self)

        # action menus
        actionExit = self.findChild(QtGui.QAction, "actionExit")
        QtCore.QObject.connect(actionExit, QtCore.SIGNAL("triggered()"), self.exit)

        # action draw mode
        actionWireframe = self.findChild(QtGui.QAction, "actionWireframe")
        actionShading = self.findChild(QtGui.QAction, "actionShading")
        QtCore.QObject.connect(actionWireframe, QtCore.SIGNAL("triggered()"),
                               lambda: self.setViewMode(CMD_VIEWMODE_WIREFRAME))
        QtCore.QObject.connect(actionShading, QtCore.SIGNAL("triggered()"),
                               lambda: self.setViewMode(CMD_VIEWMODE_SHADING))

        # Tab - resource list
        self.resourceListWidget = self.findChild(QtGui.QTreeWidget, "resourceListWidget")
        self.resourceListWidget.itemDoubleClicked.connect(self.addResource)

        # Tab - object list
        self.objectList = self.findChild(QtGui.QListWidget, "objectList")
        QtCore.QObject.connect(self.objectList, QtCore.SIGNAL("itemClicked(QListWidgetItem *)"), self.selectObject)
        QtCore.QObject.connect(self.objectList, QtCore.SIGNAL("itemActivated(QListWidgetItem *)"), self.selectObject)
        QtCore.QObject.connect(self.objectList, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.focusObject)

        # object property widget
        self.objPropertyTree = self.findChild(QtGui.QTreeWidget, "objPropertyTree")
        # hook editable event
        self.objPropertyTree.setEditTriggers(self.objPropertyTree.NoEditTriggers)
        # set object property events
        self.objPropertyTree.itemSelectionChanged.connect(self.checkEditable)
        self.objPropertyTree.itemClicked.connect(self.checkEditable)
        self.objPropertyTree.itemChanged.connect(self.objPropertyChanged)

        #------------------------#
        # UIThread - Regist Recieve Signals
        #------------------------#
        self.uiThread = UIThread(self.cmdQueue)
        self.connect(self.uiThread, QtCore.SIGNAL(getCommandName(CMD_CLOSE_UI)), self.exit)
        self.connect(self.uiThread, QtCore.SIGNAL(getCommandName(CMD_SEND_RESOURCE_LIST)), self.addResourceList)
        self.connect(self.uiThread, QtCore.SIGNAL(getCommandName(CMD_SEND_OBJECT_NAME)), self.addObjectName)
        self.connect(self.uiThread, QtCore.SIGNAL(getCommandName(CMD_SEND_OBJECT_DATA)), self.fillObjectData)
        self.uiThread.start()

        # wait a UI_RUN message, and send success message
        self.cmdPipe.RecvAndSend(CMD_UI_RUN, None, CMD_UI_RUN_OK, None)
        # request available mesh list
        self.coreCmdQueue.put(CMD_REQUEST_RESOURCE_LIST)

    def exit(self, *args):
        if args != () and args[0] is not None:
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
    # Widget - Resource List
    #--------------------#
    def addResourceList(self, resourceList):
        for resName, resType in resourceList:
            item = QtGui.QTreeWidgetItem(self.resourceListWidget)
            item.setText(0, resName)
            item.setText(1, resType)

    #--------------------#
    # Widget - Propery Tree
    #--------------------#
    def checkEditable(self, item=None, column=0):
        """in your connected slot, you can implement any edit-or-not-logic. you want"""
        if item is None:
            item = self.objPropertyTree.currentItem()
            column = self.objPropertyTree.currentColumn()

        # e.g. to allow editing only of column and have not child item:
        if column == 1 and item.childCount() == 0 and not self.isFillobjPropertyTree:
            self.objPropertyTree.editItem(item, column)

    def objPropertyChanged(self, item):
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
                    value = item.dataType(item.text(1))
                # send data
                currentObjectName = self.objectList.currentItem().text()
                self.coreCmdQueue.put(CMD_SET_OBJECT_DATA, (currentObjectName, propertyName, value))
            except:
                print(traceback.format_exc())
                # failed to convert string to dataType, so restore to old value
                item.setText(1, item.oldValue)

    def addProperty(self, parent, propertyName, value):
        item = QtGui.QTreeWidgetItem(parent)
        item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        item.setExpanded(True)
        # property name and type
        item.setText(0, propertyName)
        item.dataType = type(value)
        item.remove = False  # this is flag for remove item when Layout Refresh

        # set value
        if item.dataType == bool:  # bool type
            item.setCheckState(1, QtCore.Qt.Checked if value else QtCore.Qt.Unchecked)
        elif item.dataType in (tuple, list, numpy.ndarray):  # set list type
            item.setText(1, "")  # set value to None
            for i, itemValue in enumerate(value):  # add child component
                self.addProperty(item, "[%d]" % i, itemValue)
        else:  # set general type value - int, float, string
            item.setText(1, str(value))
        item.oldValue = item.text(1)  # set old value

    # objectList selected event
    def selectObject(self, inst):
        selectedObjectName = inst.text()
        # request selected object infomation to fill property widget
        self.coreCmdQueue.put(CMD_SET_OBJECT_SELECT, selectedObjectName)
        self.coreCmdQueue.put(CMD_REQUEST_OBJECT_DATA, selectedObjectName)

    def focusObject(self, inst):
        selectedObjectName = inst.text()
        self.coreCmdQueue.put(CMD_SET_OBJECT_FOCUS, selectedObjectName)

    def fillObjectData(self, objData):
        # lock edit property ui
        self.isFillobjPropertyTree = True

        self.objPropertyTree.clear()  # clear

        # fill properties of selected object
        for valueName in objData.keys():
            self.addProperty(self.objPropertyTree, valueName, objData[valueName])

        # self.showProperties()

        # unlock edit property ui
        self.isFillobjPropertyTree = False

    def showProperties(self):
        for item in self.objPropertyTree.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            print(item.text(0), item.text(1))

    #--------------------#
    # Widget - Object List
    #--------------------#
    def addObjectName(self, objName):
        # add object name to list
        item = QtGui.QListWidgetItem(objName)
        self.objectList.addItem(item)

    #--------------------#
    # Commands
    #--------------------#
    # add resource
    def addResource(self, item=None):
        self.coreCmdQueue.put(CMD_ADD_RESOURCE, (item.text(0), item.text(1)))  # send message and receive

    # set view mode
    def setViewMode(self, mode):
        self.coreCmdQueue.put(mode)


# process - QT Widget
def run_editor(cmdQueue, coreCmdQueue, cmdPipe):
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow.instance(cmdQueue, coreCmdQueue, cmdPipe)
    main_window.show()
    sys.exit(app.exec_())
