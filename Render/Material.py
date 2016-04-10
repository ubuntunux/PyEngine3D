from Core import logger
from Render import ShaderManager
from Utilities import Singleton


#------------------------------#
# FUNCTION : CreateMaterial
#------------------------------#
def CreateMaterial(name='', shader=None):
    MaterialManager.instance().createMaterial(name, shader)


#------------------------------#
# CLASS : Material
#------------------------------#
class Material:
    def __init__(self, name, shader):
        self.name = name
        self.shader = shader

    def getShader(self):
        return self.shader

#------------------------------#
# CLASS : MaterialManager
#------------------------------#
class MaterialManager(Singleton):
    def __init__(self):
        self.materials = {}
        self.default_material = None
        self.shaderManager = None
        self.coreManager = None

    def initialize(self, coreManager):
        logger.info("initialize " + self.__class__.__name__)
        self.coreManager = coreManager
        self.shaderManager = ShaderManager.instance()
        self.default_material = self.createMaterial(name='default material')

    def createMaterial(self, name='', shader=None):
        if shader is None:
            shader = self.shaderManager.default_shader
        material = Material(name=name, shader=shader)
        if name in self.materials:
            raise BaseException("There is same material.")
        self.materials[name] = material
        return material

    def getDefaultMaterial(self):
        return self.default_material