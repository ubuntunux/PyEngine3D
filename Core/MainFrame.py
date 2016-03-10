from Utilities import Singleton
from Render import renderer, shaderManager, materialManager, cameraManager
from Object import objectManager


class MainFrame(Singleton):
    def run(self):
        # initialize managers
        cameraManager.initialize()
        renderer.initialize()
        objectManager.initialize()
        shaderManager.initialize()
        materialManager.initialize()

mainFrame = MainFrame.instance()