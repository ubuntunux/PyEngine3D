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
def gen_index():
        i = 0
        while True:
            yield i
            i += 1

class CMD:
    cmd_index = gen_index()
    # arguments
    # CMD_NAME = (next(cmd_index), any datas)
    UI_RUN      = (next(cmd_index), None)
    UI_RUN_OK   = (next(cmd_index), None)
    APP_EXIT    = (next(cmd_index), None)




#------------------------------#
# CLASS : CoreManager
#------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """
    def __init__(self, cmdQueue):
        super(CoreManager, self).__init__()
        self.running = False
        self.cmdQueue = cmdQueue
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

        # initalize managers
        self.renderer.initialize(self)
        self.cameraManager.initialize(self)
        self.objectManager.initialize(self)
        self.shaderManager.initialize(self)
        self.materialManager.initialize(self)

        # ready to launch - send message to ui
        self.cmdQueue.put(CMD.UI_RUN)

        # main loop
        self.renderer.update()

        # process stop
        logger.info("Process Stop : %s" % self.__class__.__name__)

    def keyboardFunc(self, keyPressed, x, y):
        if keyPressed == b'\x1b':
            self.running = False
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

def run(cmdQueue):
    coreManager = CoreManager.instance(cmdQueue)
    coreManager.initialize()

if __name__ == '__main__':
    run(Queue())