import os, glob, configparser

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader

from Render import *
from Core import logger
from Utilities import Singleton, getClassName
from Render import Shader, Material
from Object import Triangle, Quad, Mesh, Primitive


# -----------------------#
# CLASS : ShaderLoader
# -----------------------#
class ShaderLoader(Singleton):
    def __init__(self):
        self.vertexShaders = {}
        self.fragmentShader = {}
        self.shaders = []

    def initialize(self):
        logger.info("initialize " + getClassName(self))

        # collect shader files
        for filename in glob.glob(os.path.join(PathShaders, '*.*')):
            try:
                shaderFile = os.path.split(filename)[1]
                shaderName, ext = os.path.splitext(shaderFile)
                # open shader file
                f = open(filename, 'r')
                shaderSource = f.read()
                f.close()
                # create shader
                if ext == '.vs':
                    shader = VertexShader(shaderName, shaderSource)
                    self.vertexShaders[shaderName] = shader
                elif ext == '.fs':
                    shader = FragmentShader(shaderName, shaderSource)
                    self.fragmentShader[shaderName] = shader
                else:
                    logger.warn("Shader error : %s is invalid shader. Shader file extension must be one of '.vs', '.ps', '.cs'..." % filename)
                    continue
                # regist shader
                self.shaders.append(shader)
            except:
                logger.error(traceback.format_exc())

    def close(self):
        for shader in self.shaders:
            shader.delete()

    def getVertexShader(self, shaderName):
        return self.vertexShaders[shaderName] if shaderName in self.vertexShaders else None

    def getFragmentShader(self, shaderName):
        return self.fragmentShader[shaderName] if shaderName in self.fragmentShader else None

    def getVertexShaderNameList(self):
        return list(self.vertexShaders.keys())

    def getFragmentShaderNameList(self):
        return list(self.fragmentShader.keys())


# -----------------------#
# CLASS : MaterialLoader
# -----------------------#
class MaterialLoader(Singleton):
    def __init__(self):
        self.materials = {}
        self.default_material = None

    def initialize(self):
        logger.info("initialize " + getClassName(self))
        shaderLoader = ShaderLoader.instance()

        # create materials
        for filename in glob.glob(os.path.join(PathMaterials, "*.*")):
            if os.path.splitext(filename)[1].lower() == ".material":
                materialFile = configparser.ConfigParser()
                materialFile.read(filename)
                vs = shaderLoader.getVertexShader(materialFile.get("VertexShader", "shaderName"))
                fs = shaderLoader.getFragmentShader(materialFile.get("FragmentShader", "shaderName"))
                materialName = os.path.splitext(os.path.split(filename)[1])[0]
                material = self.createMaterial(name=materialName, vs=vs, fs=fs)
                self.materials[materialName] = material
        self.default_material = self.getMaterial('default')

    def createMaterial(self, name, vs, fs):
        if name in self.materials:
            raise BaseException("There is same material.")
        material = Material(name=name, vs=vs, fs=fs)
        self.materials[name] = material
        return material

    def getDefaultMaterial(self):
        return self.default_material

    def getMaterial(self, name):
        return self.materials[name] if name in self.materials else None

    def getMaterialNameList(self):
        return list(self.materials.keys())


# -----------------------#
# CLASS : MeshLoader
# -----------------------#
class MeshLoader(Singleton):
    def __init__(self):
        self.meshes = {}

    def initialize(self):
        logger.info("initialize " + getClassName(self))

        # Regist meshs
        self.meshes['Triangle'] = Triangle()
        self.meshes['Quad'] = Quad()
        # regist mesh files
        for filename in glob.glob(os.path.join(PathMeshes, '*.mesh')):
            name = os.path.splitext(os.path.split(filename)[1])[0]
            name = name[0].upper() + name[1:]
            self.meshes[name] = Mesh(name, filename)

    def getMeshNameList(self):
        return list(self.meshes.keys())

    def getMesh(self, meshName):
        return self.meshes[meshName] if meshName in self.meshes else None


# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(Singleton):
    def __init__(self):
        self.textures = {}

    def initialize(self):
        logger.info("Initialize " + getClassName(self))


# -----------------------#
# CLASS : ResourceManager
# -----------------------#
class ResourceManager(Singleton):
    def __init__(self):
        self.shaderLoader = ShaderLoader.instance()
        self.materialLoader = MaterialLoader.instance()
        self.meshLoader = MeshLoader.instance()
        self.textureLoad = TextureLoader.instance()

    def initialize(self):
        self.shaderLoader.initialize()
        self.materialLoader.initialize()
        self.meshLoader.initialize()

    def close(self):
        self.shaderLoader.close()

    def getResourceList(self):
        """
        :return [(resource name, resource type)]:
        """
        result = []
        for resName in self.getVertexShaderNameList():
            result.append((resName, getClassName(self.getVertexShader(resName))))
        for resName in self.getFragmentShaderNameList():
            result.append((resName, getClassName(self.getFragmentShader(resName))))
        for resName in self.getMaterialNameList():
            result.append((resName, getClassName(self.getMaterial(resName))))
        for resName in self.getMeshNameList():
            result.append((resName, getClassName(self.getMesh(resName))))
        return result

    def getResourceAttribute(self, resName, resTypeName):
        try:
            resType = eval(resTypeName)
            resource = self.getResource(resName, resType)
            if resource:
                return resource.getAttribute()
            return None
        except:
            logger.error(traceback.format_exc())

    def getResource(self, resName, resType):
        resource = None
        if resType == FragmentShader:
            resource = self.getFragmentShader(resName)
        elif resType == VertexShader:
            resource = self.getVertexShader(resName)
        elif resType == Material:
            resource = self.getMaterial(resName)
        elif issubclass(resType, Primitive):
            resource = self.getMesh(resName)
        return resource

    # FUNCTIONS : Shader

    def getVertexShader(self, name):
        return self.shaderLoader.getVertexShader(name)

    def getFragmentShader(self, name):
        return self.shaderLoader.getFragmentShader(name)

    def getVertexShaderNameList(self):
        return self.shaderLoader.getVertexShaderNameList()

    def getFragmentShaderNameList(self):
        return self.shaderLoader.getFragmentShaderNameList()

    # FUNCTIONS : Material

    def getMaterial(self, name):
        return self.materialLoader.getMaterial(name)

    def getDefaultMaterial(self):
        return self.materialLoader.getDefaultMaterial()

    def getMaterialNameList(self):
        return self.materialLoader.getMaterialNameList()

    # FUNCTIONS : Mesh

    def getMeshNameList(self):
        return self.meshLoader.getMeshNameList()

    def getMesh(self, meshName):
        return self.meshLoader.getMesh(meshName)