import platform
import sys
import threading

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

    def update(self, currentTime, delta, fps):
        # set timer
        self.currentTime = currentTime
        self.delta = delta
        self.fps = fps

        if not self.cmdQueue.empty():
            if self.cmdQueue.get() == CMD.CLOSE_APP:
                self.close()

    def keyboardFunc(self, keyPressed, x, y):
        if keyPressed == b'\x1b':
            self.close()

    def keyboardUp(self, *args):
        pass #print("keyboardUp", args)

    def passiveMotionFunc(self, *args):
        pass #print("PassiveMotionFunc", args)

    def mouseFunc(self, *args):
        pass #print("MouseFunc", args)

    def motionFunc(self, *args):
        pass #print("MotionFunc", args)


def run(cmdQueue, uiCmdQueue, cmdPipe):
    coreManager = CoreManager.instance(cmdQueue, uiCmdQueue, cmdPipe)
    coreManager.initialize()