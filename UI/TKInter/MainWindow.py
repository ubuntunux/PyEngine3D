import sys
import traceback
import os
import time
from threading import Thread
import tkinter as tk

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


class MainWindow(tk.Frame):
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

        super(MainWindow, self).__init__(self.root)
        self.pack()

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
        def donothing():
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

        # layout
        command_frame = tk.Frame(self)
        w = tk.Label(command_frame, text="command_frame")
        w.pack()
        command_frame.pack(fill=tk.X, side=tk.LEFT)

        resource_frame = tk.Frame(self)
        w = tk.Label(resource_frame, text="resource_frame")
        w.pack()
        resource_frame.pack(fill=tk.X, side=tk.LEFT)

        object_frame = tk.Frame(self)
        w = tk.Label(object_frame, text="object_frame")
        w.pack()
        object_frame.pack(fill=tk.X, side=tk.LEFT)

        attribute_frame = tk.Frame(self)
        w = tk.Label(attribute_frame, text="attribute_frame")
        w.pack(fill=tk.X)
        attribute_frame.pack(fill=tk.X, side=tk.LEFT)

        # wait a UI_RUN message, and send success message
        if self.cmdPipe:
            self.cmdPipe.RecvAndSend(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)

    def exit(self, *args):
        self.root.withdraw()
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

    def setWindowTitle(self, title):
        self.root.title(title)


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    main_window = MainWindow(project_filename, cmdQueue, appCmdQueue, cmdPipe)
    main_window.show()
    sys.exit()
