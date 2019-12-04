import sys
import traceback
import os
import time
from threading import Thread
from collections import OrderedDict
from enum import Enum

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox

import numpy

from PyEngine3D.UI import logger
from PyEngine3D.Common.Command import *
from PyEngine3D.Utilities import Attributes, Attribute

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
    def __init__(self, attribute_name, dataType, parent_info, index):
        self.dataType = dataType
        self.attribute_name = attribute_name
        self.parent_info = parent_info
        self.index = index
        self.oldValue = None

    def set_old_value(self, value):
        self.oldValue = value

    def __repr__(self):
        return "ItemInfo :" + repr(self.__dict__)


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
        self.message_thread.connect(get_command_name(COMMAND.SHOW_UI), self.show)
        self.message_thread.connect(get_command_name(COMMAND.HIDE_UI), self.hide)

        self.message_thread.connect(get_command_name(COMMAND.TRANS_SCREEN_INFO), self.set_screen_info)
        self.message_thread.connect(get_command_name(COMMAND.CLEAR_RENDERTARGET_LIST), self.clear_render_target_list)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RENDERTARGET_INFO), self.add_render_target)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RENDERING_TYPE_LIST), self.add_rendering_type)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_ANTIALIASING_LIST), self.add_anti_aliasing)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_GAME_BACKEND_LIST), self.add_game_backend)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_GAME_BACKEND_INDEX), self.set_game_backend_index)

        self.message_thread.connect(get_command_name(COMMAND.CLOSE_UI), self.exit)
        self.message_thread.connect(get_command_name(COMMAND.SORT_UI_ITEMS), self.sort_items)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_LIST), self.add_resource_list)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_INFO), self.set_resource_info)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_ATTRIBUTE), self.fill_resource_attribute)
        self.message_thread.connect(get_command_name(COMMAND.DELETE_RESOURCE_INFO), self.delete_resource_info)

        self.message_thread.connect(get_command_name(COMMAND.DELETE_OBJECT_INFO), self.delete_object_info)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_OBJECT_INFO), self.add_object_info)
        self.message_thread.connect(get_command_name(COMMAND.TRANS_OBJECT_ATTRIBUTE), self.fill_object_attribute)
        self.message_thread.connect(get_command_name(COMMAND.CLEAR_OBJECT_LIST), self.clear_object_list)

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
        self.set_window_title(project_filename if project_filename else "Default Project")

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
        view_mode_menu.add_command(label="Wireframe", command=lambda: self.set_view_mode(COMMAND.VIEWMODE_WIREFRAME))
        view_mode_menu.add_command(label="Shading", command=lambda: self.set_view_mode(COMMAND.VIEWMODE_SHADING))
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

        self.play_button = tk.Button(command_frame, text="Play")
        self.play_button.pack(fill="x", side="top")
        self.play_button.bind("<Button-1>", self.toggle_play)

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
        button.bind("<Button-1>", self.change_resolution)

        label_frame = ttk.LabelFrame(command_frame, text='Rendering Type')
        label_frame.pack(fill="x", side="top", pady=10)

        self.comboRenderingType = ttk.Combobox(label_frame)
        self.comboRenderingType.pack(fill="x", side="top")
        self.comboRenderingType.bind("<<ComboboxSelected>>", self.set_rendering_type, "+")

        label_frame = ttk.LabelFrame(command_frame, text='Anti Aliasing')
        label_frame.pack(fill="x", side="top", pady=10)

        self.comboAntiAliasing = ttk.Combobox(label_frame)
        self.comboAntiAliasing.pack(fill="x", side="top")
        self.comboAntiAliasing.bind("<<ComboboxSelected>>", self.set_anti_aliasing, "+")

        label_frame = ttk.LabelFrame(command_frame, text='Render Target')
        label_frame.pack(fill="x", side="top", pady=10)

        self.comboRenderTargets = ttk.Combobox(label_frame)
        self.comboRenderTargets.pack(fill="x", side="top")
        self.comboRenderTargets.bind("<<ComboboxSelected>>", self.view_rendertarget, "+")

        # resource layout
        resource_frame = tk.Frame(main_tab, relief="sunken", padx=10, pady=10)

        label_frame = ttk.LabelFrame(resource_frame, text='Create Resource')
        label_frame.pack(fill="x", side="top", pady=10)

        button = tk.Button(label_frame, text="Create Particle")
        button.pack(fill="x", side="top")
        button.bind("<Button-1>", self.create_particle)

        button = tk.Button(label_frame, text="Create Spline")
        button.pack(fill="x", side="top")
        button.bind("<Button-1>", self.create_spline)

        button_collision = tk.Button(label_frame, text="Create Collision")
        button_collision.pack(fill="x", side="top")
        button_collision.bind("<Button-1>", self.create_collision)

        self.resource_menu = tk.Menu(root, tearoff=0)
        self.resource_menu.add_command(label="Load", command=self.load_resource)
        self.resource_menu.add_command(label="Action", command=self.action_resource)
        self.resource_menu.add_command(label="Duplicate", command=self.duplicate_resource)
        self.resource_menu.add_command(label="Save", command=self.save_resource)
        self.resource_menu.add_command(label="Delete", command=self.delete_resource)
        # self.resource_menu.bind("<FocusOut>", self.resource_menu.unpost)

        self.resource_treeview = ttk.Treeview(resource_frame)
        self.resource_treeview["columns"] = ("#1", )
        self.resource_treeview.column("#0", width=property_width)
        self.resource_treeview.column("#1", width=property_width)
        self.resource_treeview.heading("#0", text="Resource Name",
                                       command=lambda: self.sort_treeview(self.resource_treeview, 0))
        self.resource_treeview.heading("#1", text="Resource Type",
                                       command=lambda: self.sort_treeview(self.resource_treeview, 1))

        self.resource_treeview.bind("<<TreeviewSelect>>", self.select_resource)
        self.resource_treeview.bind("<Button-1>", lambda event: self.resource_menu.unpost())
        self.resource_treeview.bind("<Double-1>", lambda event: self.load_resource())
        self.resource_treeview.bind("<Button-3>", self.open_resource_menu)
        self.resource_treeview.bind("<FocusOut>", lambda event: self.resource_menu.unpost())
        self.resource_treeview.bind("<4>", lambda event: self.resource_menu.unpost())
        self.resource_treeview.bind("<5>", lambda event: self.resource_menu.unpost())
        self.resource_treeview.bind("<MouseWheel>", lambda event: self.resource_menu.unpost())

        vsb = ttk.Scrollbar(self.resource_treeview, orient="vertical", command=self.resource_treeview.yview)
        vsb.pack(side='right', fill='y')
        self.resource_treeview.configure(yscrollcommand=vsb.set)
        self.resource_treeview.pack(fill='both', expand=True)

        # object layout
        object_frame = tk.Frame(main_tab, relief="sunken", padx=10, pady=10)

        label_frame = ttk.LabelFrame(object_frame, text='Add Object')
        label_frame.pack(fill="x", side="top", pady=10)

        button = tk.Button(label_frame, text="Add Camera")
        button.pack(fill="x", side="top")
        button.bind("<Button-1>", self.add_camera)

        button = tk.Button(label_frame, text="Add Light")
        button.pack(fill="x", side="top")
        button.bind("<Button-1>", self.add_light)

        self.object_menu = tk.Menu(root, tearoff=0)
        self.object_menu.add_command(label="Action", command=self.action_object)
        self.object_menu.add_command(label="Focus", command=self.focus_object)
        self.object_menu.add_command(label="Delete", command=self.delete_object)
        self.object_menu.bind("<FocusOut>", self.object_menu.unpost)

        self.object_treeview = ttk.Treeview(object_frame)
        self.object_treeview["columns"] = ("#1",)
        self.object_treeview.column("#0", width=property_width)
        self.object_treeview.column("#1", width=property_width)
        self.object_treeview.heading("#0", text="Object Name",
                                     command=lambda: self.sort_treeview(self.object_treeview, 0))
        self.object_treeview.heading("#1", text="Object Type",
                                     command=lambda: self.sort_treeview(self.object_treeview, 1))

        self.object_treeview.bind("<<TreeviewSelect>>", lambda event: self.select_object())
        self.object_treeview.bind("<Button-1>", lambda event: self.object_menu.unpost())
        self.object_treeview.bind("<Double-1>", lambda event: self.focus_object())
        self.object_treeview.bind("<Button-3>", self.open_object_menu)
        self.object_treeview.bind("<FocusOut>", lambda event: self.object_menu.unpost())
        self.object_treeview.bind("<4>", lambda event: self.object_menu.unpost())
        self.object_treeview.bind("<5>", lambda event: self.object_menu.unpost())
        self.object_treeview.bind("<MouseWheel>", lambda event: self.object_menu.unpost())

        vsb = ttk.Scrollbar(self.object_treeview, orient="vertical", command=self.object_treeview.yview)
        vsb.pack(side='right', fill='y')
        self.object_treeview.configure(yscrollcommand=vsb.set)
        self.object_treeview.pack(fill='both', expand=True)

        # attribute layout
        self.attribute_menu = tk.Menu(root, tearoff=0)
        self.attribute_menu.add_command(label="Add", command=self.add_attribute_component)
        self.attribute_menu.add_command(label="Delete", command=self.delete_attribute_component)
        self.object_menu.bind("<FocusOut>", self.attribute_menu.unpost)

        attribute_frame = tk.Frame(main_frame, relief="sunken", padx=10, pady=10)
        self.attribute_treeview = SimpleEditableTreeview(attribute_frame)
        self.attribute_treeview.item_infos = dict()
        self.attribute_treeview["columns"] = ("#1",)
        self.attribute_treeview.column("#0", width=property_width)
        self.attribute_treeview.column("#1", width=property_width)
        self.attribute_treeview.heading("#0", text="Attribute", command=lambda: self.sort_treeview(self.attribute_treeview, 0))
        self.attribute_treeview.heading("#1", text="Value", command=lambda: self.sort_treeview(self.attribute_treeview, 1))

        self.attribute_treeview.bind("<<TreeviewSelect>>", self.select_attribute)
        self.attribute_treeview.bind("<<TreeviewCellEdited>>", self.attribute_changed)
        self.attribute_treeview.bind("<Button-1>", lambda event: self.attribute_menu.unpost())
        self.attribute_treeview.bind("<Button-3>", self.open_attribute_menu)

        def attribute_treeview_on_mouse_wheel(event):
            self.attribute_menu.unpost()
            self.attribute_treeview.clear_inplace_widgets()
        # mouse wheel up, down, click
        self.attribute_treeview.bind("<4>", attribute_treeview_on_mouse_wheel)
        self.attribute_treeview.bind("<5>", attribute_treeview_on_mouse_wheel)
        self.attribute_treeview.bind("<MouseWheel>", attribute_treeview_on_mouse_wheel)

        self.attribute_treeview.pack(fill='both', side='left', expand=True)

        vsb = ttk.Scrollbar(self.attribute_treeview, orient="vertical", command=self.attribute_treeview.yview)
        vsb.pack(side='right', fill='y')
        self.attribute_treeview.configure(yscrollcommand=vsb.set)

        # tabs
        main_tab.add(command_frame, text="Application")
        main_tab.add(resource_frame, text="Resource List")
        main_tab.add(object_frame, text="Object List")
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
        self.root.update()
        self.root.deiconify()

    def hide(self):
        self.root.withdraw()

    def set_window_title(self, title):
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

    def toggle_play(self, event):
        if "Play" == self.play_button['text']:
            self.play_button['text'] = "Stop"
            self.appCmdQueue.put(COMMAND.PLAY)
        else:
            self.play_button['text'] = "Play"
            self.appCmdQueue.put(COMMAND.STOP)

    def set_view_mode(self, mode):
        self.appCmdQueue.put(mode)

    def set_screen_info(self, screen_info):
        width, height, full_screen = screen_info
        self.spinWidth.set(width)
        self.spinHeight.set(height)
        self.checkFullScreen.set(1 if full_screen else 0)

    def clear_render_target_list(self):
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
    def add_render_target(self, rendertarget_name):
        combobox_add_item(self.comboRenderTargets, rendertarget_name)

    def view_rendertarget(self, event):
        rendertarget_index = self.comboRenderTargets.current()
        rendertarget_name = self.comboRenderTargets.get()
        self.appCmdQueue.put(COMMAND.VIEW_RENDERTARGET, (rendertarget_index, rendertarget_name))

    def change_resolution(self, event):
        width = self.spinWidth.get()
        height = self.spinHeight.get()
        full_screen = False if 0 == self.checkFullScreen.get() else True
        screen_info = (width, height, full_screen)
        self.appCmdQueue.put(COMMAND.CHANGE_RESOLUTION, screen_info)

    # ------------------------- #
    # Widget - Propery Tree
    # ------------------------- #
    def attribute_changed(self, event):
        if not self.isFillAttributeTree and self.selected_item is not None:
            # item_id = self.attribute_treeview.identify('item', event.x, event.y)
            column, item_id = self.attribute_treeview.get_event_info()

            if item_id == '':
                return

            item = self.attribute_treeview.item(item_id)
            item_info = self.attribute_treeview.item_infos[item_id]

            if item_info.dataType in (tuple, list, numpy.ndarray, Attributes):
                self.attribute_treeview.set(item_id, '#1', '')
                return

            try:
                new_value = get_value(item)

                # check value chaned
                # if item_info.oldValue == new_value:
                #     return

                item_info.oldValue = new_value

                # check array type, then combine components
                parent_id = self.attribute_treeview.parent(item_id)
                parent = self.attribute_treeview.item(parent_id)
                parent_info = self.attribute_treeview.item_infos.get(parent_id)
                value = None
                attribute_name = ''

                if parent_info is not None and parent_info.dataType in (tuple, list, numpy.ndarray):
                    attribute_name = get_name(parent)
                    values = []
                    for child_id in self.attribute_treeview.get_children(parent_id):
                        child = self.attribute_treeview.item(child_id)
                        child_info = self.attribute_treeview.item_infos.get(child_id)
                        # evaluate value
                        value = get_value(child)
                        if 'True' == value:
                            value = True
                        elif 'False' == value:
                            value = False
                        else:
                            value = child_info.dataType(value)
                        values.append(value)
                    if parent_info.dataType == numpy.ndarray:
                        # numpy array
                        value = numpy.array(values)
                    else:
                        # list or tuple
                        value = parent_info.dataType(values)
                else:
                    attribute_name = get_name(item)
                    dataType = item_info.dataType
                    if bool == dataType or numpy.bool == dataType:
                        # evaluate boolean
                        value = dataType(get_value(item) == "True")
                    elif type(dataType) == type(Enum):
                        index = [dataType(i).name for i in range(len(dataType))].index(get_value(item))
                        value = dataType(index)
                    else:
                        value = get_value(item)
                        try:
                            # try to evaluate int, float, string
                            value = dataType(value)
                        except:
                            pass

                selectedItems = []
                command = None
                if self.selected_item_categoty == 'Object':
                    command = COMMAND.SET_OBJECT_ATTRIBUTE
                    selectedItems = self.get_selected_object()
                elif self.selected_item_categoty == 'Resource':
                    command = COMMAND.SET_RESOURCE_ATTRIBUTE
                    selectedItems = self.get_selected_resource()

                for selected_item in selectedItems:
                    selected_item_name = get_name(selected_item)
                    selected_item_type = get_value(selected_item)

                    item_info_history = [item_info]
                    parent_info = item_info.parent_info
                    while parent_info is not None:
                        item_info_history.insert(0, parent_info)
                        parent_info = parent_info.parent_info

                    # send changed data
                    self.appCmdQueue.put(command,
                                         (selected_item_name,
                                          selected_item_type,
                                          attribute_name,
                                          value,
                                          item_info_history,
                                          item_info.index))
            except BaseException:
                logger.error(traceback.format_exc())
                # failed to convert string to dataType, so restore to old value
                self.attribute_treeview.set(item_id, '#1', item_info.oldValue)

    def select_attribute(self, event):
        for item_id in self.attribute_treeview.selection():
            item_info = self.attribute_treeview.item_infos[item_id]
            if bool == item_info.dataType or numpy.bool == item_info.dataType:
                self.attribute_treeview.inplace_checkbutton('#1', item_id)
            elif type(item_info.dataType) == type(Enum):
                dataType = item_info.dataType
                values = [dataType(i).name for i in range(len(dataType))]
                self.attribute_treeview.inplace_combobox('#1', item_id, values, readonly=False)
            else:
                self.attribute_treeview.inplace_entry('#1', item_id)

    def get_selected_attribute(self):
        return [self.attribute_treeview.item(item_id) for item_id in self.attribute_treeview.selection()]

    def add_attribute(self, parent, attribute_name, value, dataType, parent_info=None, index=0):
        item_id = self.attribute_treeview.insert(parent, 'end', text=attribute_name, open=True)
        item_info = ItemInfo(attribute_name=attribute_name,
                             dataType=dataType,
                             parent_info=parent_info,
                             index=index)
        self.attribute_treeview.item_infos[item_id] = item_info

        if dataType in (tuple, list, numpy.ndarray):
            for i, item_value in enumerate(value):
                self.add_attribute(item_id, "[%d]" % i, item_value, type(item_value), item_info, i)
        elif dataType in (dict, OrderedDict):
            for key in value:
                self.add_attribute(item_id, key, value[key], type(value[key]), item_info, key)
        elif dataType is Attributes:
            for attribute in value.get_attributes():
                self.add_attribute(item_id, attribute.name, attribute.value, attribute.type, item_info, attribute.name)
        else:
            # set value - int, float, string
            self.attribute_treeview.item(item_id, text=attribute_name, values=(value,))
            item_info.set_old_value(value)

    def open_attribute_menu(self, event):
        item_id = self.attribute_treeview.identify('item', event.x, event.y)
        item = self.attribute_treeview.item(item_id)
        if item not in self.get_selected_attribute():
            self.attribute_treeview.selection_set((item_id, ))
        self.attribute_menu.post(event.x_root, event.y_root)

    def add_attribute_component(self, *args):
        if self.selected_item is None or '' == self.selected_item_categoty:
            return

        if 'Resource' == self.selected_item_categoty:
            self.attribute_component_menu(COMMAND.ADD_RESOURCE_COMPONENT)
        elif 'Object' == self.selected_item_categoty:
            self.attribute_component_menu(COMMAND.ADD_OBJECT_COMPONENT)

    def delete_attribute_component(self, *args):
        if self.selected_item is None or '' == self.selected_item_categoty:
            return

        if 'Resource' == self.selected_item_categoty:
            self.attribute_component_menu(COMMAND.DELETE_RESOURCE_COMPONENT)
        elif 'Object' == self.selected_item_categoty:
            self.attribute_component_menu(COMMAND.DELETE_OBJECT_COMPONENT)

    def attribute_component_menu(self, command):
        selected_item_name = get_name(self.selected_item)
        selected_item_type = get_value(self.selected_item)

        for item_id in self.attribute_treeview.selection():
            item = self.attribute_treeview.item(item_id)
            item_info = self.attribute_treeview.item_infos[item_id]
            self.appCmdQueue.put(command,
                                 (selected_item_name,
                                  selected_item_type,
                                  item_info.attribute_name,
                                  item_info.parent_info,
                                  item_info.index))
            return

    def fill_resource_attribute(self, attributes):
        selected_items = self.get_selected_resource()
        if 0 < len(selected_items):
            self.selected_item = selected_items[0]
            self.selected_item_categoty = 'Resource'
            self.fill_attribute(attributes)

    def fill_object_attribute(self, attributes):
        selected_items = self.get_selected_object()
        if 0 < len(selected_items):
            self.selected_item = selected_items[0]
            self.selected_item_categoty = 'Object'
            self.fill_attribute(attributes)

    def clear_attribute(self):
        for item in self.attribute_treeview.get_children():
            self.attribute_treeview.delete(item)

    def fill_attribute(self, attributes):
        # lock edit attribute ui
        self.isFillAttributeTree = True

        self.clear_attribute()

        # fill properties of selected object
        for attribute in attributes.get_attributes():
            self.add_attribute("", attribute.name, attribute.value, attribute.type)

        # unlock edit attribute ui
        self.isFillAttributeTree = False

    # ------------------------- #
    # Widget - Resource List
    # ------------------------- #
    def get_selected_resource(self):
        return [self.resource_treeview.item(item_id) for item_id in self.resource_treeview.selection()]

    def add_resource_list(self, resourceList):
        for resName, resType in resourceList:
            self.resource_treeview.insert("", 'end', text=resName, values=(resType,))

    def set_resource_info(self, resource_info):
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

    def select_resource(self, event):
        items = self.get_selected_resource()

        if items and len(items) > 0:
            item = items[0]
            if TAG_LOADED == get_tag(item):
                self.appCmdQueue.put(COMMAND.REQUEST_RESOURCE_ATTRIBUTE, (get_name(item), get_value(item)))
            else:
                self.clear_attribute()

    def open_resource_menu(self, event):
        item_id = self.resource_treeview.identify('item', event.x, event.y)
        item = self.resource_treeview.item(item_id)
        if item not in self.get_selected_resource():
            self.resource_treeview.selection_set((item_id, ))
        self.resource_menu.post(event.x_root, event.y_root)

    def load_resource(self, item=None):
        items = self.get_selected_resource()
        for item in items:
            self.appCmdQueue.put(COMMAND.LOAD_RESOURCE, (get_name(item), get_value(item)))

    def action_resource(self, item=None):
        items = self.get_selected_resource()
        for item in items:
            self.appCmdQueue.put(COMMAND.ACTION_RESOURCE, (get_name(item), get_value(item)))

    def duplicate_resource(self, item=None):
        items = self.get_selected_resource()
        for item in items:
            self.appCmdQueue.put(COMMAND.DUPLICATE_RESOURCE, (get_name(item), get_value(item)))

    def save_resource(self, item=None):
        items = self.get_selected_resource()
        for item in items:
            self.appCmdQueue.put(COMMAND.SAVE_RESOURCE, (get_name(item), get_value(item)))

    def delete_resource(self, item=None):
        items = self.get_selected_resource()
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
    def add_camera(self, event):
        self.appCmdQueue.put(COMMAND.ADD_CAMERA)

    def add_light(self, event):
        self.appCmdQueue.put(COMMAND.ADD_LIGHT)

    def create_particle(self, event):
        self.appCmdQueue.put(COMMAND.CREATE_PARTICLE)

    def create_spline(self, event):
        self.appCmdQueue.put(COMMAND.CREATE_SPLINE)

    def create_collision(self, event):
        selectedItems = self.get_selected_resource()
        items = self.get_selected_resource()
        for item in items:
            self.appCmdQueue.put(COMMAND.CREATE_COLLISION, (get_name(item), get_value(item)))

    def open_object_menu(self, event):
        item_id = self.object_treeview.identify('item', event.x, event.y)
        item = self.object_treeview.item(item_id)
        if item not in self.get_selected_object():
            self.object_treeview.selection_set((item_id, ))
        self.object_menu.post(event.x_root, event.y_root)

    def get_selected_object(self):
        return [self.object_treeview.item(item_id) for item_id in self.object_treeview.selection()]

    def add_object_info(self, object_info):
        object_name, object_type = object_info
        for item_id in self.object_treeview.get_children():
            item = self.object_treeview.item(item_id)
            if get_name(item) == object_name and get_value(item) == object_type:
                self.object_treeview.item(item_id, text=object_name, values=(object_type, ))
                break
        else:
            self.object_treeview.insert("", 'end', text=object_name, values=(object_type,))

    def action_object(self, *args):
        selectedItems = self.get_selected_object()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.ACTION_OBJECT, get_name(selectedItem))

    def delete_object(self, *args):
        selectedItems = self.get_selected_object()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.DELETE_OBJECT, get_name(selectedItem))

    def delete_object_info(self, objName):
        for item_id in self.object_treeview.get_children():
            item = self.object_treeview.item(item_id)
            if objName == get_name(item):
                self.object_treeview.delete(item_id)

    def clear_object_list(self, *args):
        for item in self.object_treeview.get_children():
            self.object_treeview.delete(item)

    def select_object(self):
        selectedItems = self.get_selected_object()
        if selectedItems:
            item = selectedItems[0]
            selected_objectName = get_name(item)
            selected_objectTypeName = get_value(item)
            # request selected object infomation to fill attribute widget
            self.appCmdQueue.put(COMMAND.SET_OBJECT_SELECT, selected_objectName)
            self.appCmdQueue.put(COMMAND.REQUEST_OBJECT_ATTRIBUTE, (selected_objectName, selected_objectTypeName))

    def focus_object(self, *args):
        selectedItems = self.get_selected_object()
        for selectedItem in selectedItems:
            self.appCmdQueue.put(COMMAND.SET_OBJECT_FOCUS, get_name(selectedItem))
            break


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    root = tk.Tk()
    MainWindow(root, project_filename, cmdQueue, appCmdQueue, cmdPipe)
    root.mainloop()
    sys.exit()
