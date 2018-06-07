import sys
import traceback
import os
import time
from threading import Thread

import tkinter as tk
import tkinter.ttk as ttk

import numpy

from Utilities import Singleton, Attribute, Attributes
from UI import logger
from Common.Command import *


def addDirtyMark(text):
    if not text.startswith('*'):
        return '*' + text
    return text


def removeDirtyMark(text):
    if text.startswith('*'):
        return text[1:]
    return text


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


class MainWindow(tk.PanedWindow):
    def __init__(self, project_filename, cmdQueue, appCmdQueue, cmdPipe):
        logger.info("Create MainWindow.")
        self.root = tk.Tk()
        self.root.resizable(width=True, height=True)
        self.root.bind('<Escape>', self.exit)

        # set windows title
        self.setWindowTitle(project_filename if project_filename else "Default Project")

        width = 1024
        height = 768
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.root.geometry('%dx%d+%d+%d' % (width, height, x, y))

        super(MainWindow, self).__init__(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(self)

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

        # Menu
        def donothing(*args):
            pass

        menubar = tk.Menu(self.root)

        menu = tk.Menu(menubar, tearoff=0)
        menu.add_command(label="New Project", command=donothing)
        menu.add_command(label="Open Project", command=donothing)
        menu.add_command(label="Save Project", command=donothing)
        menu.add_separator()
        menu.add_command(label="New Scene", command=donothing)
        menu.add_command(label="Save Scene", command=donothing)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.exit)
        menubar.add_cascade(label="Menu", menu=menu)

        view_mode_menu = tk.Menu(menubar, tearoff=0)
        view_mode_menu.add_command(label="Wireframe", command=donothing)
        view_mode_menu.add_command(label="Shading", command=donothing)
        view_mode_menu.add_separator()
        menubar.add_cascade(label="View Mode", menu=view_mode_menu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help", command=donothing)
        helpmenu.add_command(label="About...", command=donothing)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.root.config(menu=menubar)

        # command layout
        command_frame = tk.Frame(self.notebook, relief="sunken", padx=10, pady=10)

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
        resource_frame = tk.Frame(self.notebook, relief="sunken", padx=10, pady=10)
        tree_view = ttk.Treeview(resource_frame)
        tree_view["columns"] = ("one", "two")

        tree_view.column("#0", width=100)
        tree_view.column("one", width=100)
        tree_view.column("two", width=100)

        tree_view.heading("#0", text="Name")
        tree_view.heading("one", text="coulmn A")
        tree_view.heading("two", text="column B")

        def selectItem(a):
            curItem = tree_view.focus()
            print(type(tree_view.item(curItem)))
        tree_view.bind('<ButtonRelease-1>', selectItem)

        tree_view.insert("", 0, text="Line 1", values=("1A", "1b"))
        # t.font = ("Times 20 bold")
        print(tree_view.get_children(0))


        id2 = tree_view.insert("", 1, "dir2", text="Dir 2")
        tree_view.insert(id2, "end", "dir 2", text="sub dir 2", values=("2A", "2B"))

        tree_view.insert("", 3, "dir3", text="Dir 3")
        tree_view.insert("dir3", 3, text=" sub dir 3", values=("3A", " 3B"))

        tree_view.pack(fill="both", side="top", expand=True)

        # object layout
        object_frame = tk.Frame(self.notebook, relief="sunken", padx=10, pady=10)
        w = tk.Label(object_frame, text="object_frame")
        w.pack()

        # attribute layout
        attribute_frame = tk.Frame(self, relief="sunken", padx=10, pady=10)
        w = tk.Label(attribute_frame, text="attribute_frame")
        w.pack()

        self.notebook.add(command_frame,text="Tag1")
        self.notebook.add(resource_frame,text="Tag2")
        self.notebook.add(object_frame,text="Tag3")
        self.add(self.notebook, width=width * 1 / 2)
        self.add(attribute_frame, width=width * 1 / 2)

        # wait a UI_RUN message, and send success message
        # if self.cmdPipe:
        #     self.cmdPipe.RecvAndSend(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)

    def exit(self, *args):
        self.root.destroy()
        self.appCmdQueue.put(COMMAND.CLOSE_APP)
        sys.exit()

    def load_config(self):
        pass

    def save_config(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width / 2) - (w / 2)
        y = (screen_height / 2) - (h / 2)
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def show(self):
        self.mainloop()
        self.root.destroy()

    def setWindowTitle(self, title):
        self.root.title(title)


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    main_window = MainWindow(project_filename, cmdQueue, appCmdQueue, cmdPipe)
    main_window.show()
    sys.exit()
