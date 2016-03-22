from multiprocessing import Queue
import platform
import sys

from __main__ import logger
from Render import renderer, shaderManager, materialManager, cameraManager
from Object import objectManager
from Utilities import Singleton

#-----------
# VARIABLES
#-----------
CMD_EXIT = 0


#------------------------------#
# CLASS : CoreManager
#------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """
    def __init__(self):
        super(CoreManager, self).__init__()
        self.running = False
        self.cmdQueue = Queue() # empty

        # timer
        self.fpsLimit = 1.0 / 60.0
        self.fps = 0.0
        self.delta = 0.0
        self.currentTime = 0.0

    def initialize(self):
        # process start
        logger.info('Platform : %s' % platform.platform())
        logger.info("Process Start : %s" % self.__class__.__name__)

        # initalize managers
        renderer.initialize(self)
        cameraManager.initialize(self)
        objectManager.initialize(self)
        shaderManager.initialize(self)
        materialManager.initialize(self)

        renderer.update()
        # process stop
        logger.info("Process Stop : %s" % self.__class__.__name__)

    def keyboardFunc(self, keyPressed, x, y):
        if keyPressed == b'\x1b':
            self.running = False
            self.cmdQueue.put([CMD_EXIT, 0])
            print("exit")
            sys.exit(0)

    def keyboardUp(self, *args):
        print("keyboardUp", args)

    def passiveMotionFunc(self, *args):
        print("PassiveMotionFunc", args)

    def mouseFunc(self, *args):
        print("MouseFunc", args)

    def motionFunc(self, *args):
        print("MotionFunc", args)

    def update(self):
        self.running = True
        while self.running:
            continue
        print("end")


#------------------------------#
# Globals
#------------------------------#
coreManager = CoreManager.instance()