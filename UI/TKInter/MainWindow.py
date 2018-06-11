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

import functools


class EditableTreeview(ttk.Treeview):
    """A simple editable treeview

    It uses the following events from Treeview:
        <<TreviewSelect>>
        <4>
        <5>
        <KeyRelease>
        <Home>
        <End>
        <Configure>
        <Button-1>
        <ButtonRelease-1>
        <Motion>
    If you need them use add=True when calling bind method.

    It Generates two virtual events:
        <<TreeviewInplaceEdit>>
        <<TreeviewCellEdited>>
    The first is used to configure cell editors.
    The second is called after a cell was changed.
    You can know wich cell is being configured or edited, using:
        get_event_info()
    """

    def __init__(self, master=None, **kw):
        ttk.Treeview.__init__(self, master, **kw)

        self._curfocus = None
        self._inplace_widgets = {}
        self._inplace_widgets_show = {}
        self._inplace_vars = {}
        self._header_clicked = False
        self._header_dragged = False

        # Wheel events?
        self.bind('<<TreeviewSelect>>', self.check_focus)
        self.bind('<4>', lambda e: self.after_idle(self.__updateWnds))
        self.bind('<5>', lambda e: self.after_idle(self.__updateWnds))
        self.bind('<KeyRelease>', self.check_focus)
        self.bind('<Home>', functools.partial(self.__on_key_press, 'Home'))
        self.bind('<End>', functools.partial(self.__on_key_press, 'End'))
        self.bind('<Button-1>', self.__on_button1)
        self.bind('<ButtonRelease-1>', self.__on_button1_release)
        self.bind('<Motion>', self.__on_mouse_motion)
        self.bind('<Configure>', lambda e: self.after_idle(self.__updateWnds))

    def __on_button1(self, event):
        r = event.widget.identify_region(event.x, event.y)
        if r in ('separator', 'header'):
            self._header_clicked = True

    def __on_mouse_motion(self, event):
        if self._header_clicked:
            self._header_dragged = True

    def __on_button1_release(self, event):
        if self._header_dragged:
            self.after_idle(self.__updateWnds)
        self._header_clicked = False
        self._header_dragged = False

    def __on_key_press(self, key, event):
        if key == 'Home':
            self.selection_set("")
            self.focus(self.get_children()[0])
        if key == 'End':
            self.selection_set("")
            self.focus(self.get_children()[-1])

    def delete(self, *items):
        self.after_idle(self.__updateWnds)
        ttk.Treeview.delete(self, *items)

    def yview(self, *args):
        """Update inplace widgets position when doing vertical scroll"""
        self.after_idle(self.__updateWnds)
        ttk.Treeview.yview(self, *args)

    def yview_scroll(self, number, what):
        self.after_idle(self.__updateWnds)
        ttk.Treeview.yview_scroll(self, number, what)

    def yview_moveto(self, fraction):
        self.after_idle(self.__updateWnds)
        ttk.Treeview.yview_moveto(self, fraction)

    def xview(self, *args):
        """Update inplace widgets position when doing horizontal scroll"""
        self.after_idle(self.__updateWnds)
        ttk.Treeview.xview(self, *args)

    def xview_scroll(self, number, what):
        self.after_idle(self.__updateWnds)
        ttk.Treeview.xview_scroll(self, number, what)

    def xview_moveto(self, fraction):
        self.after_idle(self.__updateWnds)
        ttk.Treeview.xview_moveto(self, fraction)

    def check_focus(self, event):
        """Checks if the focus has changed"""

        changed = False
        if not self._curfocus:
            changed = True
        elif self._curfocus != self.focus():
            self.__clear_inplace_widgets()
            changed = True
        newfocus = self.focus()
        if changed:
            if newfocus:
                self._curfocus = newfocus
                self.__focus(newfocus)
            self.__updateWnds()

    def __focus(self, item):
        """Called when focus item has changed"""
        cols = self.__get_display_columns()
        for col in cols:
            self.__event_info = (col, item)
            self.event_generate('<<TreeviewInplaceEdit>>')
            if col in self._inplace_widgets:
                w = self._inplace_widgets[col]
                w.bind('<Key-Tab>', lambda e: w.tk_focusNext().focus_set())
                w.bind('<Shift-Key-Tab>', lambda e: w.tk_focusPrev().focus_set())

    def __updateWnds(self, event=None):
        if not self._curfocus:
            return

        item = self._curfocus
        cols = self.__get_display_columns()
        for col in cols:
            if col in self._inplace_widgets:
                wnd = self._inplace_widgets[col]
                if self.exists(item):
                    bbox = self.bbox(item, column=col)
                    # if col in self._inplace_widgets_show:
                    wnd.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
                else:
                    wnd.place_forget()

    def __clear_inplace_widgets(self):
        """Remove all inplace edit widgets."""
        cols = self.__get_display_columns()
        # print('Clear:', cols)
        for c in cols:
            if c in self._inplace_widgets:
                widget = self._inplace_widgets[c]
                widget.place_forget()
                self._inplace_widgets_show.pop(c, None)

    def __get_display_columns(self):
        cols = self.cget('displaycolumns')
        show = (str(s) for s in self.cget('show'))
        if '#all' in cols:
            cols = self.cget('columns') + ('#0',)
        elif 'tree' in show:
            cols = cols + ('#0',)
        return cols

    def get_event_info(self):
        return self.__event_info;

    def __get_value(self, col, item):
        if col == '#0':
            return self.item(item, 'text')
        else:
            return self.set(item, col)

    def __set_value(self, col, item, value):
        if col == '#0':
            self.item(item, text=value)
        else:
            self.set(item, col, value)
        self.__event_info = (col, item)
        self.event_generate('<<TreeviewCellEdited>>')

    def __update_value(self, col, item):
        if not self.exists(item):
            return
        value = self.__get_value(col, item)
        newvalue = self._inplace_vars[col].get()
        if value != newvalue:
            self.__set_value(col, item, newvalue)

    def inplace_entry(self, col, item):
        if col not in self._inplace_vars:
            self._inplace_vars[col] = tk.StringVar()
        svar = self._inplace_vars[col]
        svar.set(self.__get_value(col, item))
        if col not in self._inplace_widgets:
            self._inplace_widgets[col] = ttk.Entry(self, textvariable=svar)
        entry = self._inplace_widgets[col]
        entry.bind('<Return>', lambda e: self.__update_value(col, item))
        entry.bind('<Unmap>', lambda e: self.__update_value(col, item))
        entry.bind('<FocusOut>', lambda e: self.__update_value(col, item))
        self._inplace_widgets_show[col] = True

    def inplace_checkbutton(self, col, item, onvalue='True', offvalue='False'):
        if col not in self._inplace_vars:
            self._inplace_vars[col] = tk.StringVar()
        svar = self._inplace_vars[col]
        svar.set(self.__get_value(col, item))
        if col not in self._inplace_widgets:
            self._inplace_widgets[col] = ttk.Checkbutton(self,
                                                         textvariable=svar, variable=svar, onvalue=onvalue,
                                                         offvalue=offvalue)
        cb = self._inplace_widgets[col]
        cb.bind('<Return>', lambda e: self.__update_value(col, item))
        cb.bind('<Unmap>', lambda e: self.__update_value(col, item))
        cb.bind('<FocusOut>', lambda e: self.__update_value(col, item))
        self._inplace_widgets_show[col] = True

    def inplace_combobox(self, col, item, values, readonly=True):
        state = 'readonly' if readonly else 'normal'
        if col not in self._inplace_vars:
            self._inplace_vars[col] = tk.StringVar()
        svar = self._inplace_vars[col]
        svar.set(self.__get_value(col, item))
        if col not in self._inplace_widgets:
            self._inplace_widgets[col] = ttk.Combobox(self,
                                                      textvariable=svar, values=values, state=state)
        cb = self._inplace_widgets[col]
        cb.bind('<Return>', lambda e: self.__update_value(col, item))
        cb.bind('<Unmap>', lambda e: self.__update_value(col, item))
        cb.bind('<FocusOut>', lambda e: self.__update_value(col, item))
        self._inplace_widgets_show[col] = True

    def inplace_spinbox(self, col, item, min, max, step):
        if col not in self._inplace_vars:
            self._inplace_vars[col] = tk.StringVar()
        svar = self._inplace_vars[col]
        svar.set(self.__get_value(col, item))
        if col not in self._inplace_widgets:
            self._inplace_widgets[col] = tk.Spinbox(self,
                                                    textvariable=svar, from_=min, to=max, increment=step)
        sb = self._inplace_widgets[col]
        sb.bind('<Return>', lambda e: self.__update_value(col, item))
        sb.bind('<Unmap>', lambda e: self.__update_value(col, item))
        cb.bind('<FocusOut>', lambda e: self.__update_value(col, item))
        self._inplace_widgets_show[col] = True

    def inplace_custom(self, col, item, widget):
        if col not in self._inplace_vars:
            self._inplace_vars[col] = tk.StringVar()
        svar = self._inplace_vars[col]
        svar.set(self.__get_value(col, item))
        self._inplace_widgets[col] = widget
        widget.bind('<Return>', lambda e: self.__update_value(col, item))
        widget.bind('<Unmap>', lambda e: self.__update_value(col, item))
        widget.bind('<FocusOut>', lambda e: self.__update_value(col, item))
        self._inplace_widgets_show[col] = True


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

        button = tk.Button(command_frame, text="Add Light")
        button.pack(fill="x", side="top")

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
        self.object_treeview.bind("<Double-1>", lambda event: self.focusObject())
        self.object_treeview.bind("<Button-3>", lambda event: self.object_menu.post(event.x_root, event.y_root))

        vsb = ttk.Scrollbar(self.object_treeview, orient="vertical", command=self.object_treeview.yview)
        vsb.pack(side='right', fill='y')
        self.object_treeview.configure(yscrollcommand=vsb.set)

        # attribute layout
        attribute_frame = tk.Frame(main_frame, relief="sunken", padx=10, pady=10)
        self.attribute_treeview = EditableTreeview(attribute_frame)
        self.attribute_treeview.item_infos = dict()
        self.attribute_treeview["columns"] = ("#1",)
        self.attribute_treeview.column("#0", width=property_width)
        self.attribute_treeview.column("#1", width=property_width)
        self.attribute_treeview.heading("#0", text="Attribute",
                                        command=lambda: self.sort_treeview(self.attribute_treeview, 0))
        self.attribute_treeview.heading("#1", text="Value",
                                        command=lambda: self.sort_treeview(self.attribute_treeview, 1))

        self.attribute_treeview.bind("<<TreeviewSelect>>", self.selectAttribute)
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

    def change_game_backend(self, game_backend_index):
        self.appCmdQueue.put(COMMAND.CHANGE_GAME_BACKEND, game_backend_index)

    def set_game_backend_index(self, game_backend_index):
        self.comboGameBackend.current(game_backend_index)

    # Rendering Type
    def add_rendering_type(self, rendering_type_list):
        for rendering_type_name in rendering_type_list:
            combobox_add_item(self.comboRenderingType, rendering_type_name)

    def set_rendering_type(self, rendering_type_index):
        self.appCmdQueue.put(COMMAND.SET_RENDERING_TYPE, rendering_type_index)

    # Anti Aliasing
    def add_anti_aliasing(self, anti_aliasing_list):
        for anti_aliasing_name in anti_aliasing_list:
            combobox_add_item(self.comboAntiAliasing, anti_aliasing_name)

    def set_anti_aliasing(self, anti_aliasing_index):
        self.appCmdQueue.put(COMMAND.SET_ANTIALIASING, anti_aliasing_index)

    # Render Target
    def addRenderTarget(self, rendertarget_name):
        combobox_add_item(self.comboRenderTargets, rendertarget_name)

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
        self.self.resource_menu.exec_(self.resource_treeview.viewport().mapToGlobal(position))

    def openObjectMenu(self, position):
        self.object_menu.exec_(self.object_treeview.viewport().mapToGlobal(position))

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
                if item.oldValue == get_value(item):
                    return
                item.oldValue = get_value(item)
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
                    attributeName = get_name(item)
                    if item.dataType == bool:
                        value = item.dataType(get_value(item) == "True")
                    else:
                        value = item.dataType(get_value(item))

                selectedItems = []
                command = None
                if self.selected_item_categoty == 'Object':
                    command = COMMAND.SET_OBJECT_ATTRIBUTE
                    selectedItems = self.object_treeview.selectedItems()

                elif self.selected_item_categoty == 'Resource':
                    command = COMMAND.SET_RESOURCE_ATTRIBUTE
                    selectedItems = self.resource_treeview.selectedItems()

                for selectedItem in selectedItems:
                    selected_item_name = selectedget_name(item)
                    selected_item_type = selectedget_value(item)
                    # send changed data
                    self.appCmdQueue.put(command,
                                         (selected_item_name, selected_item_type, attributeName, value, index))
            except:
                logger.error(traceback.format_exc())
                # failed to convert string to dataType, so restore to old value
                item.setText(1, item.oldValue)

    def selectAttribute(self, event):
        for item_id in self.attribute_treeview.selection():
            item_info = self.attribute_treeview.item_infos[item_id]
            if bool == item_info['dataType']:
                self.attribute_treeview.inplace_checkbutton('#1', item_id)
            else:
                self.attribute_treeview.inplace_entry('#1', item_id)
            self.attribute_treeview.check_focus(event)

    def addAttribute(self, parent, attributeName, value, depth=0, index=0):
        dataType = type(value)

        item_id = self.attribute_treeview.insert(parent, 'end', text=attributeName, open=True)

        self.attribute_treeview.item_infos[item_id] = dict(
            oldValue=value,
            dataType=dataType,
            remove=False,  # this is flag for remove item when Layout Refresh
            depth=depth,
            index=index
        )

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

    def showProperties(self):
        for item in self.attributeTree.findItems("", QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive):
            print(get_name(item), get_value(item))

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
        # item = self.resource_treeview.identify('item', event.x, event.y)
        # if item == '':
        #     self.resource_menu.unpost()

        items = self.getSelectedResource()

        if items and len(items) > 0:
            item = items[0]
            if TAG_LOADED == get_tag(item):
                self.appCmdQueue.put(COMMAND.REQUEST_RESOURCE_ATTRIBUTE, (get_name(item), get_value(item)))
            else:
                self.clearAttribute()

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

        if items and len(items) > 0:
            contents = "\n".join(["%s : %s" % (get_value(item), get_name(item)) for item in items])
            choice = QtGui.QMessageBox.question(self, 'Delete resource.',
                                                "Are you sure you want to delete the\n%s?" % contents,
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if choice == QtGui.QMessageBox.Yes:
                for item in items:
                    self.appCmdQueue.put(COMMAND.DELETE_RESOURCE, (get_name(item), get_value(item)))

    def delete_resource_info(self, resource_info):
        resource_name, resource_type_name, is_loaded = resource_info
        for item in self.resource_treeview.get_children():
            if get_name(item) == resource_name and get_value(item) == resource_type_name:
                self.resource_treeview.delete(item)

    # ------------------------- #
    # Widget - Object List
    # ------------------------- #
    def addLight(self):
        self.appCmdQueue.put(COMMAND.ADD_LIGHT)

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
        for item in self.object_treeview.get_children():
            if objName == get_name(item):
                self.object_treeview.delete(item)

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

    def focusObject(self, item=None):
        if item:
            selected_objectName = get_name(item)
            self.appCmdQueue.put(COMMAND.SET_OBJECT_FOCUS, selected_objectName)


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    root = tk.Tk()
    main_window = MainWindow(root, project_filename, cmdQueue, appCmdQueue, cmdPipe)
    main_window.show()
    sys.exit()
