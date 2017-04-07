import os
import sys
import time
import traceback

from kivy.app import App
from kivy.uix.button import Button

from UI import logger
from Utilities import Singleton, Attribute, Attributes
from Core.Command import *


class MainWindow(App, Singleton):
    def __init__(self, cmdQueue, coreCmdQueue, cmdPipe):
        App.__init__(self)

        self.cmdQueue = cmdQueue
        self.coreCmdQueue = coreCmdQueue
        self.cmdPipe = cmdPipe

        # wait a UI_RUN message, and send success message
        if self.cmdPipe:
            self.cmdPipe.RecvAndSend(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)
        # request available mesh list
        self.coreCmdQueue.put(COMMAND.REQUEST_RESOURCE_LIST)

    def build(self):
        return Button(text='Hello World')


def run_editor(cmdQueue, coreCmdQueue, cmdPipe):
    app = MainWindow.instance(cmdQueue, coreCmdQueue, cmdPipe)
    app.run()
    sys.exit()
