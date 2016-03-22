from __main__ import logger
from Render import shaderManager
from Utilities import Singleton

#------------------------------#
# CLASS : Material
#------------------------------#
class Material:
    def __init__(self, name='', shader=None):
        self.name = name
        self.shader = shader or shaderManager.default_shader

    def getShader(self):
        return self.shader

#------------------------------#
# CLASS : MaterialManager
#------------------------------#
class MaterialManager(Singleton):
    def __init__(self):
        self.materials = {}
        self.default_material = None
        self.coreManager = None

    def initialize(self, coreManager):
        logger.info("initialize " + self.__class__.__name__)
        self.coreManager = coreManager
        self.default_material = self.createMaterial(name='default material')

    def createMaterial(self, name='', shader=None):
        material = Material(name=name, shader=shader)
        self.materials[name] = material
        return material

#------------------------------#
# Globals
#------------------------------#
materialManager = MaterialManager.instance()