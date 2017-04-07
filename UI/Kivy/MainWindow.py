import os
import sys
import time
import traceback

from .KivyUtility import *

from Core.Command import *
from Utilities import Singleton


class MainApp(Singleton):
    def __init__(self, cmdQueue, appCmdQueue, cmdPipe):
        self.app = MyApp.instance()
        self.cmdQueue = cmdQueue
        self.appCmdQueue = appCmdQueue
        self.cmdPipe = cmdPipe
        self.screen = None
        self.layout = None
        self.running = False

    def initialize(self):
        self.screen = self.app.Screen(name="main")
        self.layout = self.app.BoxLayout(orientation="vertical", size_hint=(0.8, 0.4))
        self.layout.pos = sub(self.app.cXY, (self.app.W * 0.4, self.app.H * 0.2))
        btn_exit = self.app.Button(text="Exit")
        btn_exit.bind(on_release=lambda inst:self.exit(False))
        self.layout.add_widget(btn_exit)
        self.screen.add_widget(self.layout)
        self.app.setTouchPrev(self.exit)
        self.app.current_screen(self.screen)

        # wait a UI_RUN message, and send success message
        if self.cmdPipe:
            self.cmdPipe.RecvAndSend(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)
        # request available mesh list
        self.appCmdQueue.put(COMMAND.REQUEST_RESOURCE_LIST)

    def exit(self, isForce=False):
        if isForce:
            self.app.exit()
        else:
            self.app.popup("Exit?", "", self.app.exit, None)

    def update_message(self):
        # Process recieved queues
        if not self.cmdQueue.empty():
            # receive value must be tuple type
            cmd, value = self.cmdQueue.get()
            cmdName = get_command_name(cmd)
            # recieved queues
            if cmd == COMMAND.CLOSE_UI:
                self.exit(True)

    def update(self, dt):
        self.update_message()


def run_editor(cmdQueue, appCmdQueue, cmdPipe):
    try:
        root_app = MyApp.instance()
        root_app.run(MainApp.instance(cmdQueue, appCmdQueue, cmdPipe))
    except:
        logger.error(traceback.format_exc())
    appCmdQueue.put(COMMAND.CLOSE_APP)
    sys.exit()
