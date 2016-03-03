from Core import coreManager
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
        # regist
        coreManager.regist("MaterialManager", self)

    def initialize(self):
        self.default_material = self.createMaterial(name='default material')

    def createMaterial(self, name='', shader=None):
        material = Material(name=name, shader=shader)
        self.materials[name] = material
        return material

#------------------------------#
# Globals
#------------------------------#
materialManager = MaterialManager.instance()