from Render import ShaderManager
from Utilities import Singleton

class Material:
    def __init__(self, name='', shader=None):
        self.name = name
        self.shader = shader or ShaderManager().default_shader

    def getShader(self):
        return self.shader

class MaterialManager(Singleton):
    materials = {}

    def __init__(self):
        self.default_material = self.createMaterial(name='default material')

    def createMaterial(self, name='', shader=None):
        material = Material(name=name, shader=shader)
        self.materials[name] = material
        return material