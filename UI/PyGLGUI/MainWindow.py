import sys
import traceback
import os
import time
from threading import Thread
from collections import OrderedDict
from enum import Enum

from UI import logger
from Common.Command import *
from Utilities import Attributes


from . import PyGLGUI


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
        self.lastTime = time.perf_counter()
        while self.running:
            # Timer
            self.delta = time.perf_counter() - self.lastTime
            if self.delta < self.limitDelta:
                time.sleep(self.limitDelta - self.delta)
            # print(1.0/(time.perf_counter() - self.lastTime))
            self.lastTime = time.perf_counter()

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
    def __init__(self, project_filename, cmdQueue, appCmdQueue, cmdPipe):
        logger.info("Create MainWindow.")

        self.project_filename = project_filename
        self.cmdQueue = cmdQueue
        self.appCmdQueue = appCmdQueue
        self.cmdPipe = cmdPipe

        self.limitDelta = 1.0 / 60.0  # 60fps
        self.delta = 0.0
        self.lastTime = 0.0
        self.running = True

        if project_filename is "" or project_filename is None:
            project_filename = "Default Project"

        # MessageThread
        self.message_thread = MessageThread(self.cmdQueue)
        self.message_thread.start()
        # self.message_thread.connect(get_command_name(COMMAND.SHOW_UI), self.show)
        # self.message_thread.connect(get_command_name(COMMAND.HIDE_UI), self.hide)

        # self.message_thread.connect(get_command_name(COMMAND.TRANS_SCREEN_INFO), self.set_screen_info)
        # self.message_thread.connect(get_command_name(COMMAND.CLEAR_RENDERTARGET_LIST), self.clear_render_target_list)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_RENDERTARGET_INFO), self.add_render_target)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_RENDERING_TYPE_LIST), self.add_rendering_type)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_ANTIALIASING_LIST), self.add_anti_aliasing)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_GAME_BACKEND_LIST), self.add_game_backend)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_GAME_BACKEND_INDEX), self.set_game_backend_index)
        #
        self.message_thread.connect(get_command_name(COMMAND.CLOSE_UI), self.exit)
        # self.message_thread.connect(get_command_name(COMMAND.SORT_UI_ITEMS), self.sort_items)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_LIST), self.add_resource_list)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_INFO), self.set_resource_info)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_RESOURCE_ATTRIBUTE), self.fill_resource_attribute)
        # self.message_thread.connect(get_command_name(COMMAND.DELETE_RESOURCE_INFO), self.delete_resource_info)
        #
        # self.message_thread.connect(get_command_name(COMMAND.DELETE_OBJECT_INFO), self.delete_object_info)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_OBJECT_INFO), self.add_object_info)
        # self.message_thread.connect(get_command_name(COMMAND.TRANS_OBJECT_ATTRIBUTE), self.fill_object_attribute)
        # self.message_thread.connect(get_command_name(COMMAND.CLEAR_OBJECT_LIST), self.clear_object_list)

        # wait a UI_RUN message, and send success message
        if self.cmdPipe:
            self.cmdPipe.RecvAndSend(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)

        self.coreManager = PyGLGUI.App.CoreManager.instance()
        self.coreManager.initialize()

    def run(self):
        self.coreManager.run()
        self.lastTime = time.perf_counter()
        while self.running:
            self.delta = time.perf_counter() - self.lastTime
            if self.delta < self.limitDelta:
                time.sleep(self.limitDelta - self.delta)
            self.lastTime = time.perf_counter()

    def exit(self, *args):
        logger.info("Bye")
        self.running = False
        self.appCmdQueue.put(COMMAND.CLOSE_APP)


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    window = MainWindow(project_filename, cmdQueue, appCmdQueue, cmdPipe)
    window.run()
    sys.exit()
