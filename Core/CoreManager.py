import ctypes
import platform as libPlatform
import sys
import time

from sdl2 import *

from Core import *
from Utilities import Singleton
from Render import Renderer, ShaderManager, MaterialManager, CameraManager
from Object import ObjectManager, Triangle, Quad


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
        self.event = None
        self.keystatus = None
        self.cmdQueue = cmdQueue
        self.uiCmdQueue = uiCmdQueue
        self.cmdPipe = cmdPipe
        self.renderThread = None
        self.mainThread = None

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
        logger.info('Platform : %s' % libPlatform.platform())
        logger.info("Process Start : %s" % self.__class__.__name__)

        if SDL_Init(SDL_INIT_EVERYTHING) != 0:
            logger.info(SDL_GetError())

        # get sdl event handle
        self.event = SDL_Event()
        # keyboard state
        self.keystatus = SDL_GetKeyboardState(None)

        # initalize managers
        self.renderer = Renderer.instance()
        self.renderer.initialize(self)

        # ready to launch - send message to ui
        #PipeSendRecv(self.cmdPipe, CMD_UI_RUN, CMD_UI_RUN_OK)
        self.cmdPipe.send(CMD_UI_RUN)


    def run(self):
        # main loop
        self.update()

        # send a message to close ui
        self.uiCmdQueue.put(CMD_CLOSE_UI)

        # close renderer
        self.renderer.close()

        # save config
        config.save()
        logger.info("Save renderer config file - " + config.getFilename())

        # process stop
        logger.info("Process Stop : %s" % self.__class__.__name__)

        # quit
        SDL_Quit()

    def error(self, msg):
        logger.error(msg)
        self.close()

    def close(self):
        self.running = False

    def updateCommand(self):
        while not self.cmdQueue.empty():
            cmd = self.cmdQueue.get()
            if cmd == CMD_CLOSE_APP:
                self.close()


    def updateEvent(self):
        while SDL_PollEvent(ctypes.byref(self.event)) != 0:
            eventType = self.event.type
            if eventType == SDL_QUIT:
                self.close()
            elif eventType == SDL_WINDOWEVENT:
                if self.event.window.event == SDL_WINDOWEVENT_RESIZED:
                    self.renderer.resizeScene()
            elif eventType == SDL_KEYDOWN:
                keydown = self.event.key.keysym.sym
                if keydown == SDLK_ESCAPE:
                    self.close()
                elif keydown == SDLK_q:
                    self.renderer.objectManager.addPrimitive(Quad, name="quad", pos=(0,0,0))
                elif keydown == SDLK_t:
                    self.renderer.objectManager.addPrimitive(Triangle, name="quad", pos=(0,0,0))
                # another keydown check
                if self.keystatus[SDL_SCANCODE_LCTRL]:
                    print("key down LCTRL")
                print("key down", keydown)
            elif eventType == SDL_KEYUP:
                keyup = self.event.key.keysym.sym
                print("key up", keyup)
            elif eventType == SDL_MOUSEMOTION:
                pass
            elif eventType == SDL_MOUSEBUTTONDOWN:
                pass
            elif eventType == SDL_MOUSEBUTTONUP:
                pass
            elif eventType == SDL_MOUSEWHEEL:
                pass


    def update(self):
        self.running = True
        while self.running:
            currentTime = time.time()
            delta = currentTime - self.currentTime

            if delta < self.fpsLimit:
                continue

            # set timer
            self.currentTime = currentTime
            self.delta = delta
            self.fps = 1.0 / delta

            # update command queue
            self.updateCommand()

            # update keyboard and mouse events
            self.updateEvent()

            # render scene
            self.renderer.renderScene()