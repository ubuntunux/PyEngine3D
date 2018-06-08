import sys
import traceback
import os
import time
from threading import Thread

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

import numpy

from Utilities import Singleton, Attribute, Attributes
from UI import logger
from Common.Command import *


TAG_NORMAL = 'normal'
TAG_LOADED = 'loaded'


def addDirtyMark(text):
    if not text.startswith('*'):
        return '*' + text
    return text


def removeDirtyMark(text):
    if text.startswith('*'):
        return text[1:]
    return text


def get_name(item):
    return item['text']


def get_value(item):
    return item['values'][0]


def get_tag(item):
    return item['tag'][0] if 'tag' in item and 0 < len(item['tag']) else ''


class MessageThread(Thread):
    def __init__(self, cmdQueue):
        Thread.__init__(self)
        self.running = True
        self.cmdQueue = cmdQueue
        self.commands = {}

        self.limitDelta = 1.0 / 60.0  # 60fps
        self.delta = 0.0
        self.lastTime = 0.0

    def connect(self, command_name, command):
        self.commands[command_name] = command

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
                if cmdName in self.commands:
                    command = self.commands[cmdName]
                    if value is not None:
                        command(value)
                    else:
                        command()


class MainWindow:
    def __init__(self, root, project_filename, cmdQueue, appCmdQueue, cmdPipe):
        logger.info("Create MainWindow.")

        self.root = root
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
        self.message_thread.connect(get_command_name(COMMAND.CLOSE_UI), self.exit)
        self.message_thread.connect(get_command_name(COMMAND.SORT_UI_ITEMS), self.sort_items)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_LIST), self.addResourceList)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_INFO), self.setResourceInfo)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_ATTRIBUTE), self.fillResourceAttribute)
        self.message_thread.connect(get_command_name(COMMAND.DELETE_RESOURCE_INFO), self.delete_resource_info)

        width = 600
        height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = int(screen_width - width)
        y = int((screen_height / 2) - (height / 2))
        frame_width = int(width / 2)
        property_width = int(frame_width / 2)

        root.resizable(width=True, height=True)
        root.bind('<Escape>', self.exit)
        root.geometry('%dx%d+%d+%d' % (width, height, x, y))

        main_frame = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_frame.pack(fill="both", expand=True)
        main_tab = ttk.Notebook(main_frame)

        # set windows title
        self.setWindowTitle(project_filename if project_filename else "Default Project")

        def donothing(*args):
            pass

        # Menu
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        menu = tk.Menu(menubar, tearoff=0)
        menu.add_command(label="New Project", command=self.new_project)
        menu.add_command(label="Open Project", command=self.open_project)
        menu.add_command(label="Save Project", command=self.save_project)
        menu.add_separator()
        menu.add_command(label="New Scene", command=self.new_scene)
        menu.add_command(label="Save Scene", command=self.save_scene)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.exit)
        menubar.add_cascade(label="Menu", menu=menu)

        view_mode_menu = tk.Menu(menubar, tearoff=0)
        view_mode_menu.add_command(label="Wireframe", command=lambda: self.setViewMode(COMMAND.VIEWMODE_WIREFRAME))
        view_mode_menu.add_command(label="Shading", command=lambda: self.setViewMode(COMMAND.VIEWMODE_SHADING))
        view_mode_menu.add_separator()
        menubar.add_cascade(label="View Mode", menu=view_mode_menu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help", command=donothing)
        helpmenu.add_command(label="About...", command=donothing)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # command layout
        command_frame = tk.Frame(main_tab, relief="sunken", padx=10, pady=10)

        variable = tk.StringVar()
        values = ("pyglet", "pygame")
        combobox = ttk.Combobox(command_frame, values=values, textvariable=variable)
        combobox.bind("<<ComboboxSelected>>", donothing, "+")
        combobox.pack(fill="x", side="top")
        combobox.current(0)

        separator = ttk.Separator(command_frame, orient='horizontal')
        separator.pack(fill="x", side="top", pady=10)

        button = tk.Button(command_frame, text="Add Camera")
        button.pack(fill="x", side="top")

        button = tk.Button(command_frame, text="Add Light")
        button.pack(fill="x", side="top")

        label_frame = ttk.LabelFrame(command_frame, text='Resolution')
        label_frame.pack(fill="x", side="top", pady=10)

        frame = tk.Frame(label_frame, relief="sunken", padx=5)
        frame.pack(fill="x", side="top")
        label = tk.Label(frame, text="Width", width=1)
        label.pack(fill="x", side="left", expand=True)

        spinbox = tk.Spinbox(frame, from_=0, to=9999, width=1)
        spinbox.pack(fill="x", side="left", expand=True)

        frame = tk.Frame(label_frame, relief="sunken", padx=5)
        frame.pack(fill="x", side="top")
        label = tk.Label(frame, text="Height", width=1)
        label.pack(fill="x", side="left", expand=True)
        spinbox = tk.Spinbox(frame, from_=0, to=9999, width=1)
        spinbox.pack(fill="x", side="left", expand=True)

        variable = tk.IntVar()
        check_button = tk.Checkbutton(label_frame, text="Full Screen", variable=variable)
        check_button.pack(fill="x", side="top")

        button = tk.Button(label_frame, text="Change Resolution")
        button.pack(fill="x", side="top")

        combobox = ttk.Combobox(command_frame)
        combobox.bind("<<ComboboxSelected>>", donothing, "+")
        combobox.pack(fill="x", side="top")

        combobox = ttk.Combobox(command_frame)
        combobox.bind("<<ComboboxSelected>>", donothing, "+")
        combobox.pack(fill="x", side="top")

        combobox = ttk.Combobox(command_frame)
        combobox.bind("<<ComboboxSelected>>", donothing, "+")
        combobox.pack(fill="x", side="top")

        # resource layout
        self.resource_menu = tk.Menu(root, tearoff=0)
        self.resource_menu.add_command(label="Load", command=self.loadResource)
        self.resource_menu.add_command(label="Open", command=self.openResource)
        self.resource_menu.add_command(label="Duplicate", command=self.duplicateResource)
        self.resource_menu.add_command(label="Save", command=self.saveResource)
        self.resource_menu.add_command(label="Delete", command=self.deleteResource)
        self.resource_menu.bind("<FocusOut>", self.resource_menu.unpost)

        self.resource_treeview = ttk.Treeview(main_tab)
        self.resource_treeview["columns"] = ("#1", )
        self.resource_treeview.column("#0", width=property_width)
        self.resource_treeview.column("#1", width=property_width)
        self.resource_treeview.heading("#0", text="Resource Name",
                                       command=lambda: self.sort_treeview(self.resource_treeview, 0))
        self.resource_treeview.heading("#1", text="Resource Type",
                                       command=lambda: self.sort_treeview(self.resource_treeview, 1))

        self.resource_treeview.bind("<<TreeviewSelect>>", self.selectResource)
        # self.resource_treeview.bind("<Button-1>", self.selectResource)
        self.resource_treeview.bind("<Double-1>", lambda event: self.loadResource())
        self.resource_treeview.bind("<Button-3>", lambda event: self.resource_menu.post(event.x_root, event.y_root))

        vsb = ttk.Scrollbar(self.resource_treeview, orient="vertical", command=self.resource_treeview.yview)
        vsb.pack(side='right', fill='y')
        self.resource_treeview.configure(yscrollcommand=vsb.set)

        # object layout
        self.object_treeview = ttk.Treeview(main_tab)
        self.object_treeview["columns"] = ("#1",)
        self.object_treeview.column("#0", width=property_width)
        self.object_treeview.column("#1", width=property_width)
        self.object_treeview.heading("#0", text="Object Name",
                                     command=lambda: self.sort_treeview(self.object_treeview, 0))
        self.object_treeview.heading("#1", text="Object Type",
                                     command=lambda: self.sort_treeview(self.object_treeview, 1))

        vsb = ttk.Scrollbar(self.object_treeview, orient="vertical", command=self.object_treeview.yview)
        vsb.pack(side='right', fill='y')
        self.object_treeview.configure(yscrollcommand=vsb.set)

        # attribute layout
        attribute_frame = tk.Frame(main_frame, relief="sunken", padx=10, pady=10)
        self.attribute_treeview = ttk.Treeview(attribute_frame)
        self.attribute_treeview["columns"] = ("#1",)
        self.attribute_treeview.column("#0", width=property_width)
        self.attribute_treeview.column("#1", width=property_width)
        self.attribute_treeview.heading("#0", text="Attribute",
                                        command=lambda: self.sort_treeview(self.attribute_treeview, 0))
        self.attribute_treeview.heading("#1", text="Value",
                                        command=lambda: self.sort_treeview(self.attribute_treeview, 1))
        self.attribute_treeview.pack(fill='both', side='left', expand=True)

        vsb = ttk.Scrollbar(self.attribute_treeview, orient="vertical", command=self.attribute_treeview.yview)
        vsb.pack(side='right', fill='y')
        self.attribute_treeview.configure(yscrollcommand=vsb.set)

        # tabs
        main_tab.add(command_frame, text="Application")
        main_tab.add(self.resource_treeview, text="Resource List")
        main_tab.add(self.object_treeview, text="Object List")
        main_frame.add(main_tab, width=frame_width)
        main_frame.add(attribute_frame, width=frame_width)

        # wait a UI_RUN message, and send success message
        if self.cmdPipe:
            self.cmdPipe.RecvAndSend(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)

    def exit(self, *args):
        logger.info("Bye")
        self.save_config()
        self.root.quit()
        self.appCmdQueue.put(COMMAND.CLOSE_APP)
        sys.exit()

    def load_config(self):
        pass

    def save_config(self):
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        width = self.root.winfo_width()
        height = self.root.winfo_height()

    def show(self):
        self.root.mainloop()

    def setWindowTitle(self, title):
        self.root.title(title)

    # ------------------------- #
    # Menu
    # ------------------------- #
    def sort_treeview(self, treeview, column_index):
        if not hasattr(treeview, 'orders'):
            treeview.orders = {}

        if column_index not in treeview.orders:
            treeview.orders[column_index] = True
        else:
            treeview.orders[column_index] = not treeview.orders[column_index]

        def sort_func(item_id):
            item = treeview.item(item_id)
            if 0 == column_index:
                return item['text']
            else:
                return item['values'][column_index - 1]

        items = list(treeview.get_children(''))
        items.sort(key=sort_func, reverse=treeview.orders[column_index])

        for i, item in enumerate(items):
            treeview.move(item, '', i)

    def sort_items(self):
        self.sort_treeview(self.resource_treeview, 0)
        self.sort_treeview(self.resource_treeview, 1)

    def new_project(self):
        filename = filedialog.asksaveasfilename(initialdir=".",
                                                title="New Project",
                                                filetypes=(("project name", "*.*"), ))
        self.appCmdQueue.put(COMMAND.NEW_PROJECT, filename)

    def open_project(self):
        filename = filedialog.askopenfilename(initialdir=".",
                                              title="Open Project",
                                              filetypes=(("project file", "*.project"), ("all files", "*.*")))
        self.appCmdQueue.put(COMMAND.OPEN_PROJECT, filename)

    def save_project(self):
        self.appCmdQueue.put(COMMAND.SAVE_PROJECT)

    def new_scene(self):
        self.appCmdQueue.put(COMMAND.NEW_SCENE)

    def save_scene(self):
        self.appCmdQueue.put(COMMAND.SAVE_SCENE)

    def setViewMode(self, mode):
        self.appCmdQueue.put(mode)

    def setScreenInfo(self, screen_info):
        width, height, full_screen = screen_info
        self.spinWidth.setValue(width)
        self.spinHeight.setValue(height)
        self.checkFullScreen.setChecked(full_screen or False)

    def clearRenderTargetList(self):
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
    def addRenderTarget(self, rendertarget_name):
        self.comboRenderTargets.addItem(rendertarget_name)

    def view_rendertarget(self, rendertarget_index):
        rendertarget_name = self.comboRenderTargets.itemText(rendertarget_index)
        self.appCmdQueue.put(COMMAND.VIEW_RENDERTARGET, (rendertarget_index, rendertarget_name))

    def changeResolution(self):
        width = self.spinWidth.value()
        height = self.spinHeight.value()
        full_screen = self.checkFullScreen.isChecked()
        screen_info = (width, height, full_screen)
        self.appCmdQueue.put(COMMAND.CHANGE_RESOLUTION, screen_info)

    def openResourceMenu(self, position):
        self.self.resource_menu.exec_(self.resourceListWidget.viewport().mapToGlobal(position))

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

    def attributeChanged(self, item):
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
                    attributeName = parent.text(0)
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
                    attributeName = item.text(0)
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
                    self.appCmdQueue.put(command,
                                         (selected_item_name, selected_item_type, attributeName, value, index))
            except:
                logger.error(traceback.format_exc())
                # failed to convert string to dataType, so restore to old value
                item.setText(1, item.oldValue)

    def addAttribute(self, parent, attributeName, value, depth=0, index=0):
        item = QtGui.QTreeWidgetItem(parent)
        item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        item.setExpanded(True)
        # attribute name and type
        item.setText(0, attributeName)
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
                self.addAttribute(item, "[%d]" % i, itemValue, depth + 1, i)
        else:  # set general type value - int, float, string
            item.setText(1, str(value))
        item.oldValue = item.text(1)  # set old value

    def fillResourceAttribute(self, attributes):
        self.selected_item = self.resourceListWidget.currentItem()
        self.selected_item_categoty = 'Resource'
        self.fillAttribute(attributes)

    def fillObjectAttribute(self, attributes):
        self.selected_item = self.objectList.currentItem()
        self.selected_item_categoty = 'Object'
        self.fillAttribute(attributes)

    def clearAttribute(self):
        for item in self.attribute_treeview.get_children():
            self.attribute_treeview.delete(item)

    def fillAttribute(self, attributes):
        # lock edit attribute ui
        self.isFillAttributeTree = True

        self.clearAttribute()

        # fill properties of selected object
        attribute_values = list(attributes.getAttributes())
        attribute_values.sort(key=lambda x: x.name)
        for attribute in attribute_values:
            self.addAttribute(self.attributeTree, attribute.name, attribute.value)

        # unlock edit attribute ui
        self.isFillAttributeTree = False

    def showProperties(self):
        for item in self.attributeTree.findItems("", QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive):
            print(item.text(0), item.text(1))

    # ------------------------- #
    # Widget - Resource List
    # ------------------------- #
    def getSelectedResource(self):
        return [self.resource_treeview.item(item_id) for item_id in self.resource_treeview.selection()]

    def addResourceList(self, resourceList):
        for resName, resType in resourceList:
            self.resource_treeview.insert("", 'end', text=resName, values=(resType,))

    def setResourceInfo(self, resource_info):
        resource_name, resource_type, is_loaded = resource_info

        self.resource_treeview.tag_configure(TAG_NORMAL, foreground="gray")
        self.resource_treeview.tag_configure(TAG_LOADED, foreground="black")
        tag = TAG_LOADED if is_loaded else TAG_NORMAL

        for item_id in self.resource_treeview.get_children(''):
            item = self.resource_treeview.item(item_id)
            # edit item
            if item['text'] == resource_name and item['values'][0] == resource_type:
                self.resource_treeview.item(item_id, text=resource_name, values=(resource_type,), tags=(tag, ))
        else:
            # insert item
            self.resource_treeview.insert("", 'end', text=resource_name, values=(resource_type,), tags=(tag, ))

    def selectResource(self, event):
        item = self.resource_treeview.identify('item', event.x, event.y)

        if item == '':
            self.resource_menu.unpost()

        items = self.getSelectedResource()

        for item in items:
            print(get_name(item))

        if items and len(items) > 0:
            if TAG_LOADED == get_tag(items[0]):
                self.appCmdQueue.put(COMMAND.REQUEST_RESOURCE_ATTRIBUTE, (get_name(items[0]), get_value(items[0])))
            else:
                self.clearAttribute()

    def loadResource(self, item=None):
        items = self.getSelectedResource()
        for item in items:
            self.appCmdQueue.put(COMMAND.LOAD_RESOURCE, (item.text(0), item.text(1)))

    def openResource(self, item=None):
        items = self.getSelectedResource()
        for item in items:
            self.appCmdQueue.put(COMMAND.OPEN_RESOURCE, (item.text(0), item.text(1)))

    def duplicateResource(self, item=None):
        items = self.getSelectedResource()
        for item in items:
            self.appCmdQueue.put(COMMAND.DUPLICATE_RESOURCE, (item.text(0), item.text(1)))

    def saveResource(self, item=None):
        items = self.getSelectedResource()
        for item in items:
            self.appCmdQueue.put(COMMAND.SAVE_RESOURCE, (item.text(0), item.text(1)))

    def deleteResource(self, item=None):
        items = self.getSelectedResource()

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

    # ------------------------- #
    # Widget - Object List
    # ------------------------- #
    def addLight(self):
        self.appCmdQueue.put(COMMAND.ADD_LIGHT)

    def addObjectInfo(self, object_info):
        object_name, object_type = object_info
        item = QtGui.QTreeWidgetItem(self.objectList)
        item.setText(0, object_name)
        item.setText(1, object_type)

    def actionObject(self, *args):
        selectedItems = self.objectList.selectedItems()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.ACTION_OBJECT, selectedItem.text(0))

    def deleteObject(self, *args):
        selectedItems = self.objectList.selectedItems()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.DELETE_OBJECT, selectedItem.text(0))

    def deleteObjectInfo(self, objName):
        items = self.objectList.findItems(objName, QtCore.Qt.MatchExactly, column=0)
        for item in items:
            index = self.objectList.indexOfTopLevelItem(item)
            self.objectList.takeTopLevelItem(index)

    def clearObjectList(self, *args):
        self.objectList.clear()

    def selectObject(self):
        selectedItems = self.objectList.selectedItems()
        if selectedItems:
            item = selectedItems[0]
            selected_objectName = item.text(0)
            selected_objectTypeName = item.text(1)
            # request selected object infomation to fill attribute widget
            self.appCmdQueue.put(COMMAND.SET_OBJECT_SELECT, selected_objectName)
            self.appCmdQueue.put(COMMAND.REQUEST_OBJECT_ATTRIBUTE, (selected_objectName, selected_objectTypeName))

    def focusObject(self, item=None):
        if item:
            selected_objectName = item.text(0)
            self.appCmdQueue.put(COMMAND.SET_OBJECT_FOCUS, selected_objectName)


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    root = tk.Tk()
    main_window = MainWindow(root, project_filename, cmdQueue, appCmdQueue, cmdPipe)
    main_window.show()
    sys.exit()
