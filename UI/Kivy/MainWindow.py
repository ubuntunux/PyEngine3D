import os
import sys
import time
import traceback

from .KivyUtility import *

from Common.Command import *
from Utilities import Singleton


class MainApp(Singleton):
    def __init__(self, cmdQueue, appCmdQueue, cmdPipe):
        self.running = False
        self.app = MyApp.instance()
        self.cmdQueue = cmdQueue
        self.appCmdQueue = appCmdQueue
        self.cmdPipe = cmdPipe

        self.default_height = 0.0
        self.default_font_size = "15sp"

        self.layout = None
        self.header_layout = None
        self.body_layout = None
        self.view_mode_dropdown = None
        self.resource_layout = None
        self.resource_scrollview = None
        self.object_layout = None
        self.object_scrollview = None

    def initialize(self):
        self.layout = self.app.BoxLayout(orientation="vertical", size_hint=(1, 1), pos_hint=pos_hint_center)
        self.app.setTouchPrev(self.exit)
        self.app.add_widget(self.layout)

        self.default_height = self.app.H * 0.025
        self.default_font_size = "15sp"

        # Header
        self.header_layout = self.app.BoxLayout(orientation="horizontal", size_hint=(1, None),
                                                height=self.default_height)
        self.layout.add_widget(self.header_layout)

        # Menu - Exit
        btn = self.app.Button(text="Exit", font_size=self.default_font_size)
        btn.bind(on_release=lambda inst: self.exit(False))
        self.header_layout.add_widget(btn)

        # Menu - Viewmode
        self.view_mode_dropdown = self.app.DropDown()

        def set_view_mode(view_mode):
            self.set_view_mode(view_mode)
            self.view_mode_dropdown.dismiss()

        btn = self.app.Button(text='Wireframe', size_hint_y=None, height=self.default_height,
                              font_size=self.default_font_size)
        btn.bind(on_release=lambda btn: set_view_mode(COMMAND.VIEWMODE_WIREFRAME))
        self.view_mode_dropdown.add_widget(btn)
        btn = self.app.Button(text='Shading', size_hint_y=None, height=self.default_height,
                              font_size=self.default_font_size)
        btn.bind(on_release=lambda btn: set_view_mode(COMMAND.VIEWMODE_SHADING))
        self.view_mode_dropdown.add_widget(btn)

        btn = self.app.Button(text='View Mode', size_hint=(1, 1), font_size=self.default_font_size)
        btn.bind(on_release=self.view_mode_dropdown.open)
        self.header_layout.add_widget(btn)

        # Body Layout
        self.body_layout = self.app.BoxLayout(orientation="horizontal", size_hint=(1, 0.975))
        self.layout.add_widget(self.body_layout)

        # Resource Layout
        self.resource_layout = self.app.BoxLayout(orientation="vertical", size_hint=(1, None), height=0.0)
        self.resource_scrollview = self.app.ScrollView(size_hint=(1, 1))
        self.resource_scrollview.add_widget(self.resource_layout)
        self.body_layout.add_widget(self.resource_scrollview)

        # Object Layout
        self.object_layout = self.app.BoxLayout(orientation="vertical", size_hint=(1, None), height=0.0)
        self.object_scrollview = self.app.ScrollView(size_hint=(1, 1))
        self.object_scrollview.add_widget(self.object_layout)
        self.body_layout.add_widget(self.object_scrollview)

        # # Resource list
        # self.resourceListWidget = self.findChild(QtGui.QTreeWidget, "resourceListWidget")
        # self.resourceListWidget.itemDoubleClicked.connect(self.addResource)
        # self.resourceListWidget.itemClicked.connect(self.select_resource)
        # self.connect(self.uiThread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_RESOURCE_ATTRIBUTE)),
        #              self.fill_attribute)
        #
        # # Object list
        # self.objectList = self.findChild(QtGui.QListWidget, "objectList")
        # self.objectList.itemClicked.connect(self.select_object)
        # self.objectList.itemActivated.connect(self.select_object)
        # self.objectList.itemDoubleClicked.connect(self.focus_object)
        # self.connect(self.uiThread, QtCore.SIGNAL(get_command_name(COMMAND.DELETE_OBJECT_NAME)), self.deleteObjectName)
        # self.connect(self.uiThread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_OBJECT_NAME)), self.addObjectName)
        # self.connect(self.uiThread, QtCore.SIGNAL(get_command_name(COMMAND.TRANS_OBJECT_ATTRIBUTE)), self.fill_attribute)

        # wait a UI_RUN message, and send success message
        if self.cmdPipe:
            self.cmdPipe.RecvAndSend(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)
        # request available mesh list
        self.appCmdQueue.put(COMMAND.REQUEST_RESOURCE_LIST)

    # ----------------- #
    # Commands
    # ----------------- #
    def exit(self, isForce=False):
        if isForce:
            self.app.exit()
        else:
            self.app.popup("Exit?", "", self.app.exit, None)

    def set_view_mode(self, mode):
        self.appCmdQueue.put(mode)

    def add_resource_list(self, resourceList):
        for resName, resType in resourceList:
            btn = self.app.Button(text='%s [ %s ]' % (resName, resType), size_hint_y=None, height=self.default_height,
                                  font_size = self.default_font_size)
            # btn.bind(on_release=lambda btn: set_view_mode(COMMAND.VIEWMODE_SHADING))
            self.resource_layout.add_widget(btn)
            self.resource_layout.height = len(self.resource_layout.children) * self.default_height

    def addObjectName(self, object_name):
        btn = self.app.Button(text=object_name, size_hint_y=None, height=self.default_height,
                              font_size=self.default_font_size)
        self.object_layout.add_widget(btn)
        self.object_layout.height = len(self.object_layout.children) * self.default_height

    # ----------------- #
    # Update
    # ----------------- #
    def update_message(self):
        # Process recieved queues
        if not self.cmdQueue.empty():
            # receive value must be tuple type
            cmd, value = self.cmdQueue.get()
            cmdName = get_command_name(cmd)
            # recieved queues
            if cmd == COMMAND.CLOSE_UI:
                self.exit(True)
            elif cmd == COMMAND.TRANS_RESOURCE_LIST:
                self.add_resource_list(value)
            elif cmd == COMMAND.TRANS_OBJECT_NAME:
                self.addObjectName(value)

    def update(self, dt):
        self.update_message()


def run_editor(project_filename, cmdQueue, appCmdQueue, cmdPipe):
    try:
        root_app = MyApp.instance()
        root_app.run('GuineaPig Editor', MainApp.instance(cmdQueue, appCmdQueue, cmdPipe))
    except:
        logger.error(traceback.format_exc())
    appCmdQueue.put(COMMAND.CLOSE_APP)
    sys.exit()
