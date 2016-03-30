import platform
import sys
import threading

from OpenGL.GLUT import glutGetModifiers

from Core import *
from Utilities import Singleton
from Render import Renderer, ShaderManager, MaterialManager, CameraManager
from Object import ObjectManager

#------------------------------#
# CLASS : CoreManager
#------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """
    def __init__(self, cmdQueue, uiCmdQueue, cmdPipe):
        super(CoreManager, self).__init__()
        self.running = False
        self.cmdQueue = cmdQueue
        self.uiCmdQueue = uiCmdQueue
        self.cmdPipe = cmdPipe
        self.renderThread = None
        self.mainThread = None

        # keyboard
        self.keyUp = {}
        self.keyDown = {}
        self.keyPress = {}

        # timer
        self.fps = 0.0
        self.delta = 0.0
        self.currentTime = 0.0

        # managers
        self.renderer = Renderer.instance()
        self.cameraManager = CameraManager.instance()
        self.objectManager = ObjectManager.instance()
        self.shaderManager = ShaderManager.instance()
        self.materialManager = MaterialManager.instance()

    def initialize(self):
        # process start
        logger.info('Platform : %s' % platform.platform())
        logger.info("Process Start : %s" % self.__class__.__name__)

        # initalize managers
        self.renderer.initialize(self)
        self.cameraManager.initialize(self)
        self.objectManager.initialize(self)
        self.shaderManager.initialize(self)
        self.materialManager.initialize(self)

        # ready to launch - send message to ui
        PipeSendRecv(self.cmdPipe, CMD.UI_RUN, CMD.UI_RUN_OK)

        # run thread
        self.renderer.update()

    def close(self):
        # close ui
        self.uiCmdQueue.put(CMD.CLOSE_UI)
        # close renderer
        self.renderer.close()
        # process stop
        logger.info("Process Stop : %s" % self.__class__.__name__)
        sys.exit(0)

    def updateInput(self):
        # first apply keyup
        for key in self.keyUp.keys():
            # keyup
            if self.keyUp[key]:
                #self.keyUp[key] = False
                if key in self.keyDown:
                    self.keyDown.pop(key)
                if key in self.keyPress:
                    self.keyPress.pop(key)
        # remove all key up events
        self.keyUp = {}

        # key down
        for key in self.keyDown.keys():
            # key pressed
            if key in self.keyPress and self.keyPress[key]:
                if key == b'\x1b':
                    self.close()
            # key down
            if self.keyDown[key]:
                pass
        self.keyPress = {}

    def update(self, currentTime, delta, fps):
        # set timer
        self.currentTime = currentTime
        self.delta = delta
        self.fps = fps

        # update keyboard and mouse events
        self.updateInput()

        if not self.cmdQueue.empty():
            if self.cmdQueue.get() == CMD.CLOSE_APP:
                self.close()

    def keyboardFunc(self, keyPressed, x, y):
        # keyup cancle
        if keyPressed in self.keyUp and self.keyUp[keyPressed]:
            self.keyUp[keyPressed] = False

        # key pressed
        if keyPressed not in self.keyDown or not self.keyDown[keyPressed]:
            self.keyDown[keyPressed] = True
            self.keyPress[keyPressed] = True

    def keyboardUp(self, keyPressed, x, y):
        self.keyUp[keyPressed] = True

    def passiveMotionFunc(self, *args):
        pass #print("PassiveMotionFunc", args)

    def mouseFunc(self, *args):
        pass #print("MouseFunc", args)

    def motionFunc(self, *args):
        pass #print("MotionFunc", args)


def run(cmdQueue, uiCmdQueue, cmdPipe):
    coreManager = CoreManager.instance(cmdQueue, uiCmdQueue, cmdPipe)
    coreManager.initialize()