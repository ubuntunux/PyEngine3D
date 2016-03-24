from multiprocessing import Queue, Process
import platform
import sys

from Core import logger
from Utilities import Singleton
from Render import Renderer, ShaderManager, MaterialManager, CameraManager
from Object import ObjectManager


#-----------
# VARIABLES
#-----------
# CMD_EXIT = 0


#------------------------------#
# CLASS : CoreManager
#------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """
    def __init__(self, queueCreateObject):
        super(CoreManager, self).__init__()
        self.running = False
        self.queueCreateObject = queueCreateObject
        self.renderProcess = None

        # timer
        self.fpsLimit = 1.0 / 60.0
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
        
        # run
        self.running = True

        # initalize managers
        self.renderer.initialize(self)
        self.cameraManager.initialize(self)
        self.objectManager.initialize(self)
        self.shaderManager.initialize(self)
        self.materialManager.initialize(self)
        self.renderer.update()

        # process stop
        logger.info("Process Stop : %s" % self.__class__.__name__)

    def keyboardFunc(self, keyPressed, x, y):
        if keyPressed == b'\x1b':
            self.running = False

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

def run(queueCreateObject):
    coreManager = CoreManager.instance(queueCreateObject)
    coreManager.initialize()

if __name__ == '__main__':
    run(Queue())