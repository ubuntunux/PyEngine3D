import sys

from Utilities import Singleton
from Render import renderer, shaderManager, materialManager, cameraManager
from Object import objectManager
from Configure import config

class MainFrame(Singleton):
    def run(self):
        # initialize managers
        cameraManager.initialize()
        renderer.initialize()
        objectManager.initialize()
        shaderManager.initialize()
        materialManager.initialize()

    def update(self):
        renderer.update()
        config.close()

    def keyPressed(self, *args):
        if args[0] == b'\x1b':
            renderer.close()
            self.close()

    def close(self):
        config.save()
        sys.exit()


mainFrame = MainFrame.instance()