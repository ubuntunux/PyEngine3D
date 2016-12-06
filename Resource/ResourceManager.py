import os
import glob
import configparser
import time
import traceback

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader
from PIL import Image

from Render import *
from Core import logger
from Utilities import Singleton, getClassName
from Render import Shader, Material, Texture
from Object import Triangle, Quad, Mesh, Primitive


# -----------------------#
# CLASS : MetaData
# -----------------------#
class MetaData:
    def __init__(self, filePath):
        if os.path.exists(filePath):
            self.filePath = filePath
            self.dateTime = os.path.getmtime(filePath)
            self.timeStamp = time.ctime(self.dateTime)


# -----------------------#
# CLASS : ResourceLoader
# -----------------------#
class ResourceLoader(object):
    def __init__(self, fileExt):
        self.resources = {}
        self.metaDatas = {}
        self.fileExt = fileExt

    def initialize(self):
        logger.info("initialize " + getClassName(self))

        # collect shader files
        for filename in glob.glob(os.path.join(PathShaders, '*.' + self.fileExt)):
            self.loadResource(filename)
            # set meta data
            self.metaDatas[shader] = MetaData(filename)

    @staticmethod
    def getResourceName(filepath):
        resourceName = os.path.splitext(os.path.split(filepath)[1])[0]
        return resourceName.lower()

    def loadResource(self, filePath):
        raise BaseException("You must implement loadResource.")

    def getMetaData(self, resourceName):
        resource = self.getResource(resourceName)
        return self.metaDatas[resource] if resource in self.metaDatas else None

    def getResource(self, resourceName):
        return self.resources[resourceName] if resourceName in self.resources else None

    def getResourceList(self):
        return list(self.resources.values())

    def getResourceNameList(self):
        return list(self.resources.keys())


# -----------------------#
# CLASS : ShaderLoader
# -----------------------#
class ShaderLoader(Singleton):
    def __init__(self):
        self.vertexShaders = {}
        self.fragmentShader = {}
        self.metaDatas = {}

    def initialize(self):
        logger.info("initialize " + getClassName(self))

        # collect shader files
        for filename in glob.glob(os.path.join(PathShaders, '*.*')):
            try:
                shaderName, ext = os.path.splitext(os.path.split(filename)[1])
                shaderName = shaderName.lower()
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
                    logger.warn("Shader error : %s is invalid shader.Shader file extension must be one of '.vs', '.ps', '.cs'..." % filename)
                    continue
                # set meta data
                self.metaDatas[shader] = MetaData(filename)
            except:
                logger.error(traceback.format_exc())

    def close(self):
        for shader in self.vertexShaders.values():
            shader.delete()

        for shader in self.fragmentShader.values():
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
        self.default_material = None
        self.materials = {}
        self.metaDatas = {}

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
                materialName = materialName.lower()
                material = Material(materialName=materialName, vs=vs, fs=fs)
                self.materials[materialName] = material
                # set meta data
                self.metaDatas[material] = MetaData(filename)
        self.default_material = self.getMaterial('default')

    def getDefaultMaterial(self):
        return self.default_material

    def getMaterial(self, materialName):
        return self.materials[materialName] if materialName in self.materials else None

    def getMaterialNameList(self):
        return list(self.materials.keys())


# -----------------------#
# CLASS : MeshLoader
# -----------------------#
class MeshLoader(Singleton):
    def __init__(self):
        self.meshes = {}
        self.metaDatas = {}

    def initialize(self):
        logger.info("initialize " + getClassName(self))

        # Regist meshs
        self.meshes['triangle'] = Triangle()
        self.meshes['quad'] = Quad()
        # regist mesh files
        for filename in glob.glob(os.path.join(PathMeshes, '*.mesh')):
            try:
                meshName = os.path.splitext(os.path.split(filename)[1])[0]
                meshName = meshName.lower()
                # load from mesh
                f = open(filename, 'r')
                meshData = eval(f.read())
                f.close()
                mesh = Mesh(meshName, meshData)
                self.meshes[meshName] = mesh
                # set meta data
                self.metaDatas[mesh] = MetaData(filename)
            except:
                logger.error(traceback.format_exc())

    def getMeshNameList(self):
        return list(self.meshes.keys())

    def getMesh(self, meshName):
        return self.meshes[meshName] if meshName in self.meshes else None


# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(ResourceLoader, Singleton):
    def __init__(self):
        super(TextureLoader, self).__init__("*")

    def loadResource(self, filePath):
        try:
            image = Image.open(filePath)
            ix, iy = image.size
            buffer = image.tobytes("raw", "RGBX", 0, -1)

            textureName = self.getResourceName(filePath)

            texture = Texture(textureName, buffer, ix, iy)
            self.textures[textureName] = texture
            # set meta data
            self.metaDatas[texture] = MetaData(filename)
        except:
            logger.error(traceback.format_exc())


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
        elif resType == Texture:
            resource = self.getTexture(resName)
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

    # FUNCTIONS : Texture

    def getTextureNameList(self):
        return self.textureLoader.getResourceNameList()

    def getTexture(self, textureName):
        return self.textureLoader.getResource(textureName)