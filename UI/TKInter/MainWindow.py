import sys
import traceback
import os
import time

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


class MainWindow(tk.Frame):
    def __init__(self, project_filename, cmdQueue, appCmdQueue, cmdPipe):
        logger.info("Create MainWindow.")
        self.root = tk.Tk()
        super(MainWindow, self).__init__(self.root)

        self.project_filename = project_filename
        self.cmdQueue = cmdQueue
        self.appCmdQueue = appCmdQueue
        self.cmdPipe = cmdPipe
        self.selected_item = None
        self.selected_item_categoty = ''
        self.isFillAttributeTree = False

        # MessageThread
        # self.message_thread = MessageThread(self.cmdQueue)
        # self.message_thread.start

        self.pack()
        self.hi_there = tk.Button(self)
        self.hi_there["text"] = "Hello World\n(click me)"
        self.hi_there["command"] = lambda: print("Hi")
        self.hi_there.pack(side="top")

        self.quit = tk.Button(self, text="QUIT", fg="red", command=self.exit)
        self.quit.pack(side="bottom")

        self.root.bind('<Escape>', self.exit)

        # set windows title
        # self.setWindowTitle(project_filename if project_filename else "Default Project")

        # wait a UI_RUN message, and send success message
        if self.cmdPipe:
            self.cmdPipe.RecvAndSend(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)

    def exit(self, *args):
        self.root.withdraw()
        self.appCmdQueue.put(COMMAND.CLOSE_APP)
        sys.exit()

    def show(self):
        self.mainloop()


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    main_window = MainWindow(project_filename, cmdQueue, appCmdQueue, cmdPipe)
    main_window.show()
    sys.exit()
