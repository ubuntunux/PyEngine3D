import sys
import traceback
import os
import time
from threading import Thread

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox

import numpy

from UI import logger
from Common.Command import *
from .EditableTreeview import SimpleEditableTreeview


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


def get_value(item, index=0):
    return item['values'][index]


def get_tag(item):
    return item['tags'][0] if 'tags' in item and 0 < len(item['tags']) else ''


def combobox_add_item(combobox, value):
    values = combobox['values']
    if values:
        values += (value,)
    else:
        values = (value,)
    combobox.configure(values=values)

    if 1 == len(values):
        combobox.current(0)


def combobox_clear(combobox):
    combobox.configure(values=())


class ItemInfo:
    def __init__(self, value, dataType, depth, index):
        self.oldValue = value
        self.dataType = dataType
        self.depth = depth
        self.index = index
        self.remove = False


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
        self.message_thread.connect(get_command_name(COMMAND.TRANS_SCREEN_INFO), self.setScreenInfo)
        self.message_thread.connect(get_command_name(COMMAND.CLEAR_RENDERTARGET_LIST), self.clearRenderTargetList)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RENDERTARGET_INFO), self.addRenderTarget)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RENDERING_TYPE_LIST), self.add_rendering_type)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_ANTIALIASING_LIST), self.add_anti_aliasing)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_GAME_BACKEND_LIST), self.add_game_backend)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_GAME_BACKEND_INDEX), self.set_game_backend_index)

        self.message_thread.connect(get_command_name(COMMAND.CLOSE_UI), self.exit)
        self.message_thread.connect(get_command_name(COMMAND.SORT_UI_ITEMS), self.sort_items)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_LIST), self.addResourceList)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_INFO), self.setResourceInfo)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_ATTRIBUTE), self.fillResourceAttribute)
        self.message_thread.connect(get_command_name(COMMAND.DELETE_RESOURCE_INFO), self.delete_resource_info)

        self.message_thread.connect(get_command_name(COMMAND.DELETE_OBJECT_INFO), self.deleteObjectInfo)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_OBJECT_INFO), self.addObjectInfo)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_OBJECT_ATTRIBUTE), self.fillObjectAttribute)
        self.message_thread.connect(get_command_name(COMMAND.CLEAR_OBJECT_LIST), self.clearObjectList)

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
        self.comboGameBackend = ttk.Combobox(command_frame, textvariable=variable)
        self.comboGameBackend.bind("<<ComboboxSelected>>", self.change_game_backend, "+")
        self.comboGameBackend.pack(fill="x", side="top")

        separator = ttk.Separator(command_frame, orient='horizontal')
        separator.pack(fill="x", side="top", pady=10)

        button = tk.Button(command_frame, text="Add Camera")
        button.pack(fill="x", side="top")
        button.bind("<Button-1>", self.addCamera)

        button = tk.Button(command_frame, text="Add Light")
        button.pack(fill="x", side="top")
        button.bind("<Button-1>", self.addLight)

        button = tk.Button(command_frame, text="Add Particle")
        button.pack(fill="x", side="top")
        button.bind("<Button-1>", self.add_particle)

        label_frame = ttk.LabelFrame(command_frame, text='Resolution')
        label_frame.pack(fill="x", side="top", pady=10)

        frame = tk.Frame(label_frame, relief="sunken", padx=5)
        frame.pack(fill="x", side="top")
        label = tk.Label(frame, text="Width", width=1)
        label.pack(fill="x", side="left", expand=True)

        self.spinWidth = tk.IntVar()
        self.spinWidth.set(10)
        spinbox = tk.Spinbox(frame, from_=0, to=9999, textvariable=self.spinWidth, width=1)
        spinbox.pack(fill="x", side="left", expand=True)

        frame = tk.Frame(label_frame, relief="sunken", padx=5)
        frame.pack(fill="x", side="top")
        label = tk.Label(frame, text="Height", width=1)
        label.pack(fill="x", side="left", expand=True)

        self.spinHeight = tk.IntVar()
        self.spinHeight.set(0)
        spinbox = tk.Spinbox(frame, from_=0, to=9999, textvariable=self.spinHeight, width=1)
        spinbox.pack(fill="x", side="left", expand=True)

        self.checkFullScreen = tk.IntVar()
        self.checkFullScreen.set(0)
        checkbutton = tk.Checkbutton(label_frame, text="Full Screen", variable=self.checkFullScreen)
        checkbutton.pack(fill="x", side="top")

        button = tk.Button(label_frame, text="Change Resolution")
        button.pack(fill="x", side="top")
        button.bind("<Button-1>", self.changeResolution)

        self.comboRenderingType = ttk.Combobox(command_frame)
        self.comboRenderingType.bind("<<ComboboxSelected>>", donothing, "+")
        self.comboRenderingType.pack(fill="x", side="top")
        self.comboRenderingType.bind("<<ComboboxSelected>>", self.set_rendering_type, "+")

        self.comboAntiAliasing = ttk.Combobox(command_frame)
        self.comboAntiAliasing.bind("<<ComboboxSelected>>", donothing, "+")
        self.comboAntiAliasing.pack(fill="x", side="top")
        self.comboAntiAliasing.bind("<<ComboboxSelected>>", self.set_anti_aliasing, "+")

        self.comboRenderTargets = ttk.Combobox(command_frame)
        self.comboRenderTargets.bind("<<ComboboxSelected>>", donothing, "+")
        self.comboRenderTargets.pack(fill="x", side="top")
        self.comboRenderTargets.bind("<<ComboboxSelected>>", self.view_rendertarget, "+")

        # resource layout
        self.resource_menu = tk.Menu(root, tearoff=0)
        self.resource_menu.add_command(label="Load", command=self.loadResource)
        self.resource_menu.add_command(label="Action", command=self.actionResource)
        self.resource_menu.add_command(label="Duplicate", command=self.duplicateResource)
        self.resource_menu.add_command(label="Save", command=self.saveResource)
        self.resource_menu.add_command(label="Delete", command=self.deleteResource)
        # self.resource_menu.bind("<FocusOut>", self.resource_menu.unpost)

        self.resource_treeview = ttk.Treeview(main_tab)
        self.resource_treeview["columns"] = ("#1", )
        self.resource_treeview.column("#0", width=property_width)
        self.resource_treeview.column("#1", width=property_width)
        self.resource_treeview.heading("#0", text="Resource Name",
                                       command=lambda: self.sort_treeview(self.resource_treeview, 0))
        self.resource_treeview.heading("#1", text="Resource Type",
                                       command=lambda: self.sort_treeview(self.resource_treeview, 1))

        self.resource_treeview.bind("<<TreeviewSelect>>", self.selectResource)
        self.resource_treeview.bind("<Button-1>", lambda event: self.resource_menu.unpost())
        self.resource_treeview.bind("<Double-1>", lambda event: self.loadResource())
        self.resource_treeview.bind("<Button-3>", self.open_resource_menu)
        self.resource_treeview.bind("<FocusOut>", lambda event: self.resource_menu.unpost())

        vsb = ttk.Scrollbar(self.resource_treeview, orient="vertical", command=self.resource_treeview.yview)
        vsb.pack(side='right', fill='y')
        self.resource_treeview.configure(yscrollcommand=vsb.set)

        # object layout
        self.object_menu = tk.Menu(root, tearoff=0)
        self.object_menu.add_command(label="Action", command=self.actionObject)
        self.object_menu.add_command(label="Focus", command=self.focusObject)
        self.object_menu.add_command(label="Delete", command=self.deleteObject)
        self.object_menu.bind("<FocusOut>", self.object_menu.unpost)

        self.object_treeview = ttk.Treeview(main_tab)
        self.object_treeview["columns"] = ("#1",)
        self.object_treeview.column("#0", width=property_width)
        self.object_treeview.column("#1", width=property_width)
        self.object_treeview.heading("#0", text="Object Name",
                                     command=lambda: self.sort_treeview(self.object_treeview, 0))
        self.object_treeview.heading("#1", text="Object Type",
                                     command=lambda: self.sort_treeview(self.object_treeview, 1))

        self.object_treeview.bind("<<TreeviewSelect>>", lambda event: self.selectObject())
        self.object_treeview.bind("<Button-1>", lambda event: self.object_menu.unpost())
        self.object_treeview.bind("<Double-1>", lambda event: self.focusObject())
        self.object_treeview.bind("<Button-3>", self.open_object_menu)
        self.object_treeview.bind("<FocusOut>", lambda event: self.object_menu.unpost())

        vsb = ttk.Scrollbar(self.object_treeview, orient="vertical", command=self.object_treeview.yview)
        vsb.pack(side='right', fill='y')
        self.object_treeview.configure(yscrollcommand=vsb.set)

        # attribute layout
        attribute_frame = tk.Frame(main_frame, relief="sunken", padx=10, pady=10)
        self.attribute_treeview = SimpleEditableTreeview(attribute_frame)
        self.attribute_treeview.item_infos = dict()
        self.attribute_treeview["columns"] = ("#1",)
        self.attribute_treeview.column("#0", width=property_width)
        self.attribute_treeview.column("#1", width=property_width)
        self.attribute_treeview.heading("#0", text="Attribute",
                                        command=lambda: self.sort_treeview(self.attribute_treeview, 0))
        self.attribute_treeview.heading("#1", text="Value",
                                        command=lambda: self.sort_treeview(self.attribute_treeview, 1))

        self.attribute_treeview.bind("<<TreeviewSelect>>", self.selectAttribute)
        self.attribute_treeview.bind("<<TreeviewCellEdited>>", self.attributeChanged)
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
        pass
        # x = self.root.winfo_rootx()
        # y = self.root.winfo_rooty()
        # width = self.root.winfo_width()
        # height = self.root.winfo_height()

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
            treeview.orders[column_index] = False
        else:
            treeview.orders[column_index] = not treeview.orders[column_index]

        def sort_func(item_id):
            item = treeview.item(item_id)
            if 0 == column_index:
                return get_name(item)
            else:
                return get_value(item, column_index - 1)

        items = list(treeview.get_children(''))
        items.sort(key=sort_func, reverse=treeview.orders[column_index])

        for i, item in enumerate(items):
            treeview.move(item, '', i)

    def sort_items(self):
        self.sort_treeview(self.resource_treeview, 0)
        self.sort_treeview(self.resource_treeview, 1)
        self.sort_treeview(self.object_treeview, 0)
        self.sort_treeview(self.object_treeview, 1)

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
        self.spinWidth.set(width)
        self.spinHeight.set(height)
        self.checkFullScreen.set(1 if full_screen else 0)

    def clearRenderTargetList(self):
        combobox_clear(self.comboRenderTargets)

    # Game Backend
    def add_game_backend(self, game_backend_list):
        for game_backend_name in game_backend_list:
            combobox_add_item(self.comboGameBackend, game_backend_name)

    def change_game_backend(self, event):
        game_backend_index = self.comboGameBackend.current()
        self.appCmdQueue.put(COMMAND.CHANGE_GAME_BACKEND, game_backend_index)

    def set_game_backend_index(self, game_backend_index):
        self.comboGameBackend.current(game_backend_index)

    # Rendering Type
    def add_rendering_type(self, rendering_type_list):
        for rendering_type_name in rendering_type_list:
            combobox_add_item(self.comboRenderingType, rendering_type_name)

    def set_rendering_type(self, event):
        rendering_type_index = self.comboRenderingType.current()
        self.appCmdQueue.put(COMMAND.SET_RENDERING_TYPE, rendering_type_index)

    # Anti Aliasing
    def add_anti_aliasing(self, anti_aliasing_list):
        for anti_aliasing_name in anti_aliasing_list:
            combobox_add_item(self.comboAntiAliasing, anti_aliasing_name)

    def set_anti_aliasing(self, event):
        anti_aliasing_index = self.comboAntiAliasing.current()
        self.appCmdQueue.put(COMMAND.SET_ANTIALIASING, anti_aliasing_index)

    # Render Target
    def addRenderTarget(self, rendertarget_name):
        combobox_add_item(self.comboRenderTargets, rendertarget_name)

    def view_rendertarget(self, event):
        rendertarget_index = self.comboRenderTargets.current()
        rendertarget_name = self.comboRenderTargets.get()
        self.appCmdQueue.put(COMMAND.VIEW_RENDERTARGET, (rendertarget_index, rendertarget_name))

    def changeResolution(self, event):
        width = self.spinWidth.get()
        height = self.spinHeight.get()
        full_screen = False if 0 == self.checkFullScreen.get() else True
        screen_info = (width, height, full_screen)
        self.appCmdQueue.put(COMMAND.CHANGE_RESOLUTION, screen_info)

    # ------------------------- #
    # Widget - Propery Tree
    # ------------------------- #
    def attributeChanged(self, event):
        if not self.isFillAttributeTree and self.selected_item is not None:
            column, item_id = self.attribute_treeview.get_event_info()
            item = self.attribute_treeview.item(item_id)
            item_info = self.attribute_treeview.item_infos[item_id]

            try:
                # check value chaned
                new_value = get_value(item)
                if item_info.oldValue == new_value:
                    return

                item_info.oldValue = new_value

                # check array type, then combine components
                parent_id = self.attribute_treeview.parent(item_id)
                parent = self.attribute_treeview.item(parent_id)
                parent_info = self.attribute_treeview.item_infos.get(parent_id)
                value = None
                attributeName = ''

                if parent_info is not None and parent_info.dataType in (tuple, list, numpy.ndarray):
                    attributeName = get_name(parent)
                    values = []
                    for child_id in self.attribute_treeview.get_children(parent_id):
                        child = self.attribute_treeview.item(child_id)
                        child_info = self.attribute_treeview.item_infos.get(child_id)
                        # evaluate value
                        values.append(child_info.dataType(get_value(child)))
                    if parent_info.dataType == numpy.ndarray:
                        # numpy array
                        value = numpy.array(values)
                    else:
                        # list or tuple
                        value = parent_info.dataType(values)
                else:
                    attributeName = get_name(item)
                    if bool == item_info.dataType:
                        # evaluate boolean
                        value = item_info.dataType(get_value(item) == "True")
                    else:
                        # evaluate int, float, string
                        value = item_info.dataType(get_value(item))

                selectedItems = []
                command = None
                if self.selected_item_categoty == 'Object':
                    command = COMMAND.SET_OBJECT_ATTRIBUTE
                    selectedItems = self.getSelectedObject()
                elif self.selected_item_categoty == 'Resource':
                    command = COMMAND.SET_RESOURCE_ATTRIBUTE
                    selectedItems = self.getSelectedResource()

                for selected_item in selectedItems:
                    selected_item_name = get_name(selected_item)
                    selected_item_type = get_value(selected_item)
                    # send changed data
                    self.appCmdQueue.put(
                        command, (selected_item_name, selected_item_type, attributeName, value, item_info.index)
                    )
            except BaseException:
                logger.error(traceback.format_exc())
                # failed to convert string to dataType, so restore to old value
                item.setText(1, item.oldValue)

    def selectAttribute(self, event):
        for item_id in self.attribute_treeview.selection():
            item_info = self.attribute_treeview.item_infos[item_id]
            if bool == item_info.dataType:
                self.attribute_treeview.inplace_checkbutton('#1', item_id)
            else:
                self.attribute_treeview.inplace_entry('#1', item_id)

    def addAttribute(self, parent, attributeName, value, depth=0, index=0):
        dataType = type(value)
        item_id = self.attribute_treeview.insert(parent, 'end', text=attributeName, open=True)

        self.attribute_treeview.item_infos[item_id] = ItemInfo(value=value,
                                                               dataType=dataType,
                                                               depth=depth,
                                                               index=index)

        # set value
        if dataType in (tuple, list, numpy.ndarray):  # set list type
            for i, itemValue in enumerate(value):  # add child component
                self.addAttribute(item_id, "[%d]" % i, itemValue, depth + 1, i)
        else:
            # set general type value - int, float, string
            self.attribute_treeview.item(item_id, text=attributeName, values=(value,))

    def fillResourceAttribute(self, attributes):
        selected_items = self.getSelectedResource()
        if 0 < len(selected_items):
            self.selected_item = selected_items[0]
            self.selected_item_categoty = 'Resource'
            self.fillAttribute(attributes)

    def fillObjectAttribute(self, attributes):
        selected_items = self.getSelectedObject()
        if 0 < len(selected_items):
            self.selected_item = selected_items[0]
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
            self.addAttribute("", attribute.name, attribute.value)

        # unlock edit attribute ui
        self.isFillAttributeTree = False

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
            if get_name(item) == resource_name and get_value(item) == resource_type:
                self.resource_treeview.item(item_id, text=resource_name, values=(resource_type,), tags=(tag, ))
                break
        else:
            # insert item
            self.resource_treeview.insert("", 'end', text=resource_name, values=(resource_type,), tags=(tag, ))

    def selectResource(self, event):
        items = self.getSelectedResource()

        if items and len(items) > 0:
            item = items[0]
            if TAG_LOADED == get_tag(item):
                self.appCmdQueue.put(COMMAND.REQUEST_RESOURCE_ATTRIBUTE, (get_name(item), get_value(item)))
            else:
                self.clearAttribute()

    def open_resource_menu(self, event):
        item_id = self.resource_treeview.identify('item', event.x, event.y)
        item = self.resource_treeview.item(item_id)
        if item not in self.getSelectedResource():
            self.resource_treeview.selection_set((item_id, ))
        self.resource_menu.post(event.x_root, event.y_root)

    def loadResource(self, item=None):
        items = self.getSelectedResource()
        for item in items:
            self.appCmdQueue.put(COMMAND.LOAD_RESOURCE, (get_name(item), get_value(item)))

    def actionResource(self, item=None):
        items = self.getSelectedResource()
        for item in items:
            self.appCmdQueue.put(COMMAND.OPEN_RESOURCE, (get_name(item), get_value(item)))

    def duplicateResource(self, item=None):
        items = self.getSelectedResource()
        for item in items:
            self.appCmdQueue.put(COMMAND.DUPLICATE_RESOURCE, (get_name(item), get_value(item)))

    def saveResource(self, item=None):
        items = self.getSelectedResource()
        for item in items:
            self.appCmdQueue.put(COMMAND.SAVE_RESOURCE, (get_name(item), get_value(item)))

    def deleteResource(self, item=None):
        items = self.getSelectedResource()
        if 0 < len(items):
            contents = "\n".join(["%s : %s" % (get_value(item), get_name(item)) for item in items])
            choice = messagebox.askyesno('Delete resource', 'Are you sure you want to delete the\n%s?' % contents)
            if choice:
                for item in items:
                    self.appCmdQueue.put(COMMAND.DELETE_RESOURCE, (get_name(item), get_value(item)))

    def delete_resource_info(self, resource_info):
        resource_name, resource_type_name, is_loaded = resource_info
        for item_id in self.resource_treeview.get_children():
            item = self.resource_treeview.item(item_id)
            if get_name(item) == resource_name and get_value(item) == resource_type_name:
                self.resource_treeview.delete(item_id)

    # ------------------------- #
    # Widget - Object List
    # ------------------------- #
    def addCamera(self, event):
        self.appCmdQueue.put(COMMAND.ADD_CAMERA)

    def addLight(self, event):
        self.appCmdQueue.put(COMMAND.ADD_LIGHT)

    def add_particle(self, event):
        self.appCmdQueue.put(COMMAND.ADD_PARTICLE)

    def open_object_menu(self, event):
        item_id = self.object_treeview.identify('item', event.x, event.y)
        item = self.object_treeview.item(item_id)
        if item not in self.getSelectedObject():
            self.object_treeview.selection_set((item_id, ))
        self.object_menu.post(event.x_root, event.y_root)

    def getSelectedObject(self):
        return [self.object_treeview.item(item_id) for item_id in self.object_treeview.selection()]

    def addObjectInfo(self, object_info):
        object_name, object_type = object_info
        for item_id in self.object_treeview.get_children():
            item = self.object_treeview.item(item_id)
            if get_name(item) == object_name and get_value(item) == object_type:
                self.object_treeview.item(item_id, text=object_name, values=(object_type, ))
                break
        else:
            self.object_treeview.insert("", 'end', text=object_name, values=(object_type,))

    def actionObject(self, *args):
        selectedItems = self.getSelectedObject()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.ACTION_OBJECT, get_name(selectedItem))

    def deleteObject(self, *args):
        selectedItems = self.getSelectedObject()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.DELETE_OBJECT, get_name(selectedItem))

    def deleteObjectInfo(self, objName):
        for item_id in self.object_treeview.get_children():
            item = self.object_treeview.item(item_id)
            if objName == get_name(item):
                self.object_treeview.delete(item_id)

    def clearObjectList(self, *args):
        for item in self.object_treeview.get_children():
            self.object_treeview.delete(item)

    def selectObject(self):
        selectedItems = self.getSelectedObject()
        if selectedItems:
            item = selectedItems[0]
            selected_objectName = get_name(item)
            selected_objectTypeName = get_value(item)
            # request selected object infomation to fill attribute widget
            self.appCmdQueue.put(COMMAND.SET_OBJECT_SELECT, selected_objectName)
            self.appCmdQueue.put(COMMAND.REQUEST_OBJECT_ATTRIBUTE, (selected_objectName, selected_objectTypeName))

    def focusObject(self, *args):
        selectedItems = self.getSelectedObject()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.SET_OBJECT_FOCUS, get_name(selectedItem))
            break


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    root = tk.Tk()
    main_window = MainWindow(root, project_filename, cmdQueue, appCmdQueue, cmdPipe)
    main_window.show()
    sys.exit()
