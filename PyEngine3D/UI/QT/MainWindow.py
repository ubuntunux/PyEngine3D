import sys
import traceback
import os
import time

import PyQt4
from PyQt4 import Qt, QtCore, QtGui, uic
from PyQt4.Qt import *
import numpy

from PyEngine3D.Utilities import Singleton, Attribute, Attributes
from PyEngine3D.UI import logger
from PyEngine3D.Common.Command import *

from .Widgets import InputDialogDemo


UI_FILENAME = os.path.join(os.path.split(__file__)[0], "MainWindow.ui")


class SpinBoxDelegate(QtGui.QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtGui.QSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(100)

        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, QtCore.Qt.EditRole)

        spinBox.setValue(value)

    def setModelData(self, spinBox, model, index):
        spinBox.interpretText()
        value = spinBox.value()

        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


def addDirtyMark(text):
    if not text.startswith('*'):
        return '*' + text
    return text


def removeDirtyMark(text):
    if text.startswith('*'):
        return text[1:]
    return text


def findTreeItem(parentItem, findItemName):
    if type(parentItem) == QtGui.QTreeWidget:
        for item in parentItem.findItems("", QtCore.Qt.MatchExactly):
            if item.text(0) == findItemName:
                return item
    elif type(parentItem) == QtGui.QTreeWidgetItem:
        for i in range(parentItem.childCount()):
            item = parentItem.child(i)
            if item.text(0) == findItemName:
                return item
    return None


class MessageThread(QtCore.QThread):
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
                cmdName = get_command_name(cmd)
                # recieved queues
                if cmd == COMMAND.CLOSE_UI:
                    self.running = False
                # call binded signal event
                self.emit(QtCore.SIGNAL(cmdName), value)


class MainWindow(QtGui.QMainWindow, Singleton):
    def __init__(self, project_filename, cmdQueue, appCmdQueue, cmdPipe):
        logger.info("Create MainWindow.")
        super(MainWindow, self).__init__()
        self.project_filename = project_filename
        self.cmdQueue = cmdQueue
        self.appCmdQueue = appCmdQueue
        self.cmdPipe = cmdPipe
        self.selected_item = None
        self.selected_item_categoty = ''
        self.isFillAttributeTree = False

        # MessageThread
        self.message_thread = MessageThread(self.cmdQueue)
        self.message_thread.start()

        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.CLOSE_UI)), self.exit)

        # load ui file
        uic.loadUi(UI_FILENAME, self)

        # set windows title
        self.set_window_title(project_filename if project_filename else "Default Project")

        # exit
        actionExit = self.findChild(QtGui.QAction, "actionExit")
        QtCore.QObject.connect(actionExit, QtCore.SIGNAL("triggered()"), self.exit)
        # project
        actionNewProject = self.findChild(QtGui.QAction, "actionNewProject")
        QtCore.QObject.connect(actionNewProject, QtCore.SIGNAL("triggered()"), self.new_project)
        actionOpenProject = self.findChild(QtGui.QAction, "actionOpenProject")
        QtCore.QObject.connect(actionOpenProject, QtCore.SIGNAL("triggered()"), self.open_project)
        actionSaveProject = self.findChild(QtGui.QAction, "actionSaveProject")
        QtCore.QObject.connect(actionSaveProject, QtCore.SIGNAL("triggered()"), self.save_project)
        # scene
        actionNewScene = self.findChild(QtGui.QAction, "actionNewScene")
        QtCore.QObject.connect(actionNewScene, QtCore.SIGNAL("triggered()"), self.new_scene)
        actionSaveScene = self.findChild(QtGui.QAction, "actionSaveScene")
        QtCore.QObject.connect(actionSaveScene, QtCore.SIGNAL("triggered()"), self.save_scene)

        # action draw mode
        actionWireframe = self.findChild(QtGui.QAction, "actionWireframe")
        actionShading = self.findChild(QtGui.QAction, "actionShading")
        QtCore.QObject.connect(actionWireframe, QtCore.SIGNAL("triggered()"),
                               lambda: self.set_view_mode(COMMAND.VIEWMODE_WIREFRAME))
        QtCore.QObject.connect(actionShading, QtCore.SIGNAL("triggered()"),
                               lambda: self.set_view_mode(COMMAND.VIEWMODE_SHADING))

        # sort ui items
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.SORT_UI_ITEMS)), self.sort_items)

        # Resource list
        self.resourceListWidget = self.findChild(QtGui.QTreeWidget, "resourceListWidget")
        self.resource_menu = QMenu()
        self.resource_menu.addAction(self.tr("Load"), self.load_resource)
        self.resource_menu.addAction(self.tr("Open"), self.openResource)
        self.resource_menu.addAction(self.tr("Duplicate"), self.duplicate_resource)
        self.resource_menu.addAction(self.tr("Save"), self.save_resource)
        self.resource_menu.addAction(self.tr("Delete"), self.delete_resource)
        self.resourceListWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resourceListWidget.customContextMenuRequested.connect(self.openResourceMenu)
        self.resourceListWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.resourceListWidget.setSortingEnabled(True)
        self.resourceListWidget.sortItems(0, 0)
        self.resourceListWidget.sortItems(1, 0)
        self.resourceListWidget.itemDoubleClicked.connect(self.load_resource)
        self.resourceListWidget.itemClicked.connect(self.select_resource)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_RESOURCE_LIST)),
                     self.add_resource_list)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_RESOURCE_INFO)),
                     self.set_resource_info)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_RESOURCE_ATTRIBUTE)),
                     self.fill_resource_attribute)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.DELETE_RESOURCE_INFO)),
                     self.delete_resource_info)

        btn = self.findChild(QtGui.QPushButton, "btnOpenResource")
        btn.clicked.connect(self.openResource)

        btn = self.findChild(QtGui.QPushButton, "btnSaveResource")
        btn.clicked.connect(self.save_resource)

        btn = self.findChild(QtGui.QPushButton, "btnDeleteResource")
        btn.clicked.connect(self.delete_resource)

        btn = self.findChild(QtGui.QPushButton, "btnTest")
        btn.clicked.connect(self.test)

        btn = self.findChild(QtGui.QPushButton, "btnAddLight")
        btn.clicked.connect(self.add_light)

        # screen
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_SCREEN_INFO)),
                     self.set_screen_info)
        self.spinWidth = self.findChild(QtGui.QSpinBox, "spinWidth")
        self.spinHeight = self.findChild(QtGui.QSpinBox, "spinHeight")
        self.checkFullScreen = self.findChild(QtGui.QCheckBox, "checkFullScreen")

        btn = self.findChild(QtGui.QPushButton, "btnChangeResolution")
        btn.clicked.connect(self.change_resolution)

        # render targets
        self.comboRenderTargets = self.findChild(QtGui.QComboBox, "comboRenderTargets")
        self.comboRenderTargets.activated.connect(self.view_rendertarget)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.CLEAR_RENDERTARGET_LIST)),
                     self.clear_render_target_list)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_RENDERTARGET_INFO)),
                     self.add_render_target)

        # rendering type
        self.comboRenderingType = self.findChild(QtGui.QComboBox, "comboRenderingType")
        self.comboRenderingType.currentIndexChanged.connect(self.set_rendering_type)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_RENDERING_TYPE_LIST)),
                     self.add_rendering_type)

        # anti aliasing
        self.comboAntiAliasing = self.findChild(QtGui.QComboBox, "comboAntiAliasing")
        self.comboAntiAliasing.currentIndexChanged.connect(self.set_anti_aliasing)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_ANTIALIASING_LIST)),
                     self.add_anti_aliasing)

        # game backend
        self.comboGameBackend = self.findChild(QtGui.QComboBox, "comboGameBackend")
        self.comboGameBackend.currentIndexChanged.connect(self.change_game_backend)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_GAME_BACKEND_LIST)),
                     self.add_game_backend)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_GAME_BACKEND_INDEX)),
                     self.set_game_backend_index)

        # Object list
        self.objectList = self.findChild(QtGui.QTreeWidget, "objectListWidget")
        self.object_menu = QMenu()
        self.object_menu.addAction(self.tr("Action"), self.action_object)
        self.object_menu.addAction(self.tr("Remove"), self.delete_object)
        self.objectList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.objectList.customContextMenuRequested.connect(self.openObjectMenu)
        self.objectList.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.objectList.setSortingEnabled(True)
        self.objectList.sortItems(0, 0)
        self.objectList.sortItems(1, 0)
        self.objectList.itemClicked.connect(self.select_object)
        self.objectList.itemActivated.connect(self.select_object)
        self.objectList.itemDoubleClicked.connect(self.focus_object)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.DELETE_OBJECT_INFO)),
                     self.delete_object_info)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_OBJECT_INFO)),
                     self.add_object_info)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_OBJECT_ATTRIBUTE)),
                     self.fill_object_attribute)
        self.connect(self.message_thread, QtCore.SIGNAL(get_command_name(COMMAND.CLEAR_OBJECT_LIST)),
                     self.clear_object_list)

        btn = self.findChild(QtGui.QPushButton, "btnRemoveObject")
        btn.clicked.connect(self.delete_object)

        # Object attribute tree
        self.attributeTree = self.findChild(QtGui.QTreeWidget, "attributeTree")
        self.attributeTree.setEditTriggers(self.attributeTree.NoEditTriggers) # hook editable event
        self.attributeTree.itemSelectionChanged.connect(self.checkEditable)
        self.attributeTree.itemClicked.connect(self.checkEditable)
        self.attributeTree.itemChanged.connect(self.attribute_changed)

        # wait a UI_RUN message, and send success message
        if self.cmdPipe:
            self.cmdPipe.RecvAndSend(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.exit()

    # on closed event
    def closeEvent(self, event):
        # let the window close
        logger.info("Bye")
        event.accept()
        self.exit()

    # ------------------------- #
    # Menu
    # ------------------------- #
    def exit(self, *args):
        if args != () and args[0] is not None:
            logger.info(*args)
        self.appCmdQueue.put(COMMAND.CLOSE_APP)
        self.close()
        sys.exit()

    def sort_items(self):
        self.resourceListWidget.sortItems(0, 0)
        self.resourceListWidget.sortItems(1, 0)
        self.objectList.sortItems(0, 0)
        self.objectList.sortItems(1, 0)

    def new_project(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'New Project', os.path.join(".", "Projects"))
        self.appCmdQueue.put(COMMAND.NEW_PROJECT, filename)

    def open_project(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File', os.path.join(".", "Projects"),
                                                     "Project file (*.project)\nAll files (*.*)")
        self.appCmdQueue.put(COMMAND.OPEN_PROJECT, filename)

    def save_project(self):
        self.appCmdQueue.put(COMMAND.SAVE_PROJECT)

    def new_scene(self):
        self.appCmdQueue.put(COMMAND.NEW_SCENE)

    def save_scene(self):
        self.appCmdQueue.put(COMMAND.SAVE_SCENE)

    def set_view_mode(self, mode):
        self.appCmdQueue.put(mode)

    def set_screen_info(self, screen_info):
        width, height, full_screen = screen_info
        self.spinWidth.setValue(width)
        self.spinHeight.setValue(height)
        self.checkFullScreen.setChecked(full_screen or False)

    def clear_render_target_list(self):
        self.comboRenderTargets.clear()

    # Game Backend
    def add_game_backend(self, game_backend_list):
        for game_backend_name in game_backend_list:
            self.comboGameBackend.addItem(game_backend_name)

    def change_game_backend(self, game_backend_index):
        self.appCmdQueue.put(COMMAND.CHANGE_GAME_BACKEND, game_backend_index)

    def set_game_backend_index(self, game_backend_index):
        self.comboGameBackend.setCurrentIndex(game_backend_index)

    # Rendering Type
    def add_rendering_type(self, rendering_type_list):
        for rendering_type_name in rendering_type_list:
            self.comboRenderingType.addItem(rendering_type_name)

    def set_rendering_type(self, rendering_type_index):
        self.appCmdQueue.put(COMMAND.SET_RENDERING_TYPE, rendering_type_index)

    # Anti Aliasing
    def add_anti_aliasing(self, anti_aliasing_list):
        for anti_aliasing_name in anti_aliasing_list:
            self.comboAntiAliasing.addItem(anti_aliasing_name)

    def set_anti_aliasing(self, anti_aliasing_index):
        self.appCmdQueue.put(COMMAND.SET_ANTIALIASING, anti_aliasing_index)

    # Render Target
    def add_render_target(self, rendertarget_name):
        self.comboRenderTargets.addItem(rendertarget_name)

    def view_rendertarget(self, rendertarget_index):
        rendertarget_name = self.comboRenderTargets.itemText(rendertarget_index)
        self.appCmdQueue.put(COMMAND.VIEW_RENDERTARGET, (rendertarget_index, rendertarget_name))

    def change_resolution(self):
        width = self.spinWidth.value()
        height = self.spinHeight.value()
        full_screen = self.checkFullScreen.isChecked()
        screen_info = (width, height, full_screen)
        self.appCmdQueue.put(COMMAND.CHANGE_RESOLUTION, screen_info)

    def openResourceMenu(self, position):
        self.resource_menu.exec_(self.resourceListWidget.viewport().mapToGlobal(position))

    def openObjectMenu(self, position):
        self.object_menu.exec_(self.objectList.viewport().mapToGlobal(position))

    # ------------------------- #
    # Widget - Propery Tree
    # ------------------------- #
    def checkEditable(self, item=None, column=0):
        """in your connected slot, you can implement any edit-or-not-logic. you want"""
        if item is None:
            item = self.attributeTree.currentItem()
            column = self.attributeTree.currentColumn()

        # e.g. to allow editing only of column and have not child item:
        if column == 1 and item.childCount() == 0 and not self.isFillAttributeTree:
            if item.dataType == bool:
                item.setText(1, "True" if item.checkState(1) == QtCore.Qt.Checked else "False")
            self.attributeTree.editItem(item, column)

    def attribute_changed(self, item):
        if not self.isFillAttributeTree and self.selected_item:
            try:
                # check value chaned
                if item.oldValue == item.text(1):
                    return
                item.oldValue = item.text(1)
                index = item.index
                # check array type, then combine components
                parent = item.parent()
                if type(parent) == QtGui.QTreeWidgetItem and parent.dataType in (tuple, list, numpy.ndarray):
                    attribute_name = parent.text(0)
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
                    attribute_name = item.text(0)
                    if item.dataType == bool:
                        value = item.dataType(item.text(1) == "True")
                    else:
                        value = item.dataType(item.text(1))

                selectedItems = []
                command = None
                if self.selected_item_categoty == 'Object':
                    command = COMMAND.SET_OBJECT_ATTRIBUTE
                    selectedItems = self.objectList.selectedItems()

                elif self.selected_item_categoty == 'Resource':
                    command = COMMAND.SET_RESOURCE_ATTRIBUTE
                    selectedItems = self.resourceListWidget.selectedItems()

                for selectedItem in selectedItems:
                    selected_item_name = selectedItem.text(0)
                    selected_item_type = selectedItem.text(1)
                    # send changed data
                    self.appCmdQueue.put(command, (selected_item_name, selected_item_type, attribute_name, value, index))
            except:
                logger.error(traceback.format_exc())
                # failed to convert string to dataType, so restore to old value
                item.setText(1, item.oldValue)

    def add_attribute(self, parent, attribute_name, value, depth=0, index=0):
        item = QtGui.QTreeWidgetItem(parent)
        item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        item.setExpanded(True)
        # attribute name and type
        item.setText(0, attribute_name)
        item.dataType = type(value)
        item.remove = False  # this is flag for remove item when Layout Refresh
        item.depth = depth
        item.index = index

        # set value
        if item.dataType == bool:  # bool type
            item.setCheckState(1, QtCore.Qt.Checked if value else QtCore.Qt.Unchecked)
            item.setText(1, "True" if item.checkState(1) == QtCore.Qt.Checked else "False")
        elif item.dataType in (tuple, list, numpy.ndarray):  # set list type
            item.setText(1, "")  # set value to None
            for i, itemValue in enumerate(value):  # add child component
                self.add_attribute(item, "[%d]" % i, itemValue, depth + 1, i)
        else:  # set general type value - int, float, string
            item.setText(1, str(value))
        item.oldValue = item.text(1)  # set old value

    def fill_resource_attribute(self, attributes):
        self.selected_item = self.resourceListWidget.currentItem()
        self.selected_item_categoty = 'Resource'
        self.fill_attribute(attributes)

    def fill_object_attribute(self, attributes):
        self.selected_item = self.objectList.currentItem()
        self.selected_item_categoty = 'Object'
        self.fill_attribute(attributes)

    def clear_attribute(self):
        self.attributeTree.clear()  # clear

    def fill_attribute(self, attributes):
        # lock edit attribute ui
        self.isFillAttributeTree = True

        self.clear_attribute()

        # fill properties of selected object
        attribute_values = list(attributes.get_attributes())
        attribute_values.sort(key=lambda x: x.name)
        for attribute in attribute_values:
            self.add_attribute(self.attributeTree, attribute.name, attribute.value)

        # self.showProperties()

        # unlock edit attribute ui
        self.isFillAttributeTree = False

    def showProperties(self):
        for item in self.attributeTree.findItems("", QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive):
            print(item.text(0), item.text(1))

    # ------------------------- #
    # Widget - Resource List
    # ------------------------- #
    def get_selected_resource(self):
        return self.resourceListWidget.selectedItems()

    def add_resource_list(self, resourceList):
        for resName, resType in resourceList:
            item = QtGui.QTreeWidgetItem(self.resourceListWidget)
            item.setText(0, resName)
            item.setText(1, resType)

    def set_resource_info(self, resource_info):
        resource_name, resource_type, is_loaded = resource_info
        items = self.resourceListWidget.findItems(resource_name, QtCore.Qt.MatchExactly, column=0)
        for item in items:
            if item.text(1) == resource_type:
                break
        else:
            item = QtGui.QTreeWidgetItem(self.resourceListWidget)

        item.is_loaded = is_loaded
        fontColor = 'black' if is_loaded else 'gray'
        item.setTextColor(0, QtGui.QColor(fontColor))
        item.setTextColor(1, QtGui.QColor(fontColor))
        item.setText(0, resource_name)
        item.setText(1, resource_type)

    def select_resource(self):
        items = self.get_selected_resource()
        if items and len(items) > 0:
            if items[0].is_loaded:
                self.appCmdQueue.put(COMMAND.REQUEST_RESOURCE_ATTRIBUTE, (items[0].text(0), items[0].text(1)))
            else:
                self.clear_attribute()

    def load_resource(self, item=None):
        items = self.get_selected_resource()
        for item in items:
            self.appCmdQueue.put(COMMAND.LOAD_RESOURCE, (item.text(0), item.text(1)))

    def openResource(self, item=None):
        items = self.get_selected_resource()
        for item in items:
            self.appCmdQueue.put(COMMAND.ACTION_RESOURCE, (item.text(0), item.text(1)))

    def duplicate_resource(self, item=None):
        items = self.get_selected_resource()
        for item in items:
            self.appCmdQueue.put(COMMAND.DUPLICATE_RESOURCE, (item.text(0), item.text(1)))

    def save_resource(self, item=None):
        items = self.get_selected_resource()
        for item in items:
            self.appCmdQueue.put(COMMAND.SAVE_RESOURCE, (item.text(0), item.text(1)))

    def delete_resource(self, item=None):
        items = self.get_selected_resource()

        if items and len(items) > 0:
            contents = "\n".join(["%s : %s" % (item.text(1), item.text(0)) for item in items])
            choice = QtGui.QMessageBox.question(self, 'Delete resource.',
                                                "Are you sure you want to delete the\n%s?" % contents,
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if choice == QtGui.QMessageBox.Yes:
                for item in items:
                    self.appCmdQueue.put(COMMAND.DELETE_RESOURCE, (item.text(0), item.text(1)))

    def delete_resource_info(self, resource_info):
        resource_name, resource_type_name, is_loaded = resource_info
        items = self.resourceListWidget.findItems(resource_name, QtCore.Qt.MatchExactly, column=0)
        for item in items:
            if item.text(1) == resource_type_name:
                index = self.resourceListWidget.indexOfTopLevelItem(item)
                self.resourceListWidget.takeTopLevelItem(index)

    def test(self):
        myPopUp = InputDialogDemo(self, "Create Static Mesh")
        myPopUp.exec_()

    # ------------------------- #
    # Widget - Object List
    # ------------------------- #
    def add_light(self):
        self.appCmdQueue.put(COMMAND.ADD_LIGHT)

    def add_object_info(self, object_info):
        object_name, object_type = object_info
        item = QtGui.QTreeWidgetItem(self.objectList)
        item.setText(0, object_name)
        item.setText(1, object_type)

    def action_object(self, *args):
        selectedItems = self.objectList.selectedItems()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.ACTION_OBJECT, selectedItem.text(0))

    def delete_object(self, *args):
        selectedItems = self.objectList.selectedItems()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.DELETE_OBJECT, selectedItem.text(0))

    def delete_object_info(self, objName):
        items = self.objectList.findItems(objName, QtCore.Qt.MatchExactly, column=0)
        for item in items:
            index = self.objectList.indexOfTopLevelItem(item)
            self.objectList.takeTopLevelItem(index)

    def clear_object_list(self, *args):
        self.objectList.clear()

    def select_object(self):
        selectedItems = self.objectList.selectedItems()
        if selectedItems:
            item = selectedItems[0]
            selected_objectName = item.text(0)
            selected_objectTypeName = item.text(1)
            # request selected object infomation to fill attribute widget
            self.appCmdQueue.put(COMMAND.SET_OBJECT_SELECT, selected_objectName)
            self.appCmdQueue.put(COMMAND.REQUEST_OBJECT_ATTRIBUTE, (selected_objectName, selected_objectTypeName))

    def focus_object(self, item=None):
        if item:
            selected_objectName = item.text(0)
            self.appCmdQueue.put(COMMAND.SET_OBJECT_FOCUS, selected_objectName)


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    """process - QT Widget"""
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow.instance(project_filename, cmdQueue, appCmdQueue, cmdPipe)
    main_window.show()
    sys.exit(app.exec_())
