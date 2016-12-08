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
        if filePath != "" and os.path.exists(filePath):
            self.filePath = filePath
            self.dateTime = os.path.getmtime(filePath)
            self.timeStamp = time.ctime(self.dateTime)
        else:
            self.filePath = ""
            self.dateTime = 0.0
            self.timeStamp = time.ctime(self.dateTime)


# -----------------------#
# CLASS : ResourceLoader
# -----------------------#
class ResourceLoader(object):
    def __init__(self, dirName, fileExt):
        self.resources = {}
        self.metaDatas = {}
        self.dirName = dirName
        self.fileExt = fileExt

    def initialize(self):
        logger.info("initialize " + getClassName(self))

        # collect shader files
        for dirname, dirnames, filenames in os.walk(self.dirName):
            for filename in filenames:
                if self.fileExt == ".*" or self.fileExt == os.path.splitext(filename)[1].lower():
                    filename = os.path.join(dirname, filename)
                    resource = self.loadResource(filename)
                    if resource:
                        self.registResource(resource, filename)
                    else:
                        logger.error("load %s error" % filename)
            
    def createResource(self):
        """ create resource file and regist."""
        pass
    
    def deleteResource(self, resource):
        """ delete resource file and release."""
        if resource:
            metaData = self.getMetaData(resource)
            self.releaseResource(resource)            
            if metaData:
                filePath = metaData.filePath
                if os.path.exists(filePath):
                    os.remove(filePath)
                    logger.info("Remove %s file" & filePath)
       
    def registResource(self, resource, filePath=""):
        if resource is None or not hasattr(resource, "name"):
            raise AttributeException("resource have to has name.")        
        newMetaData = MetaData(filePath)                
        # check the file is exsits resource or not.
        if resource.name in self.resources:
            oldResource = self.resources[resource.name]
            oldMetaData = self.getMetaData(oldResource)
            if oldMetaData:
                if newMetaData.filePath == oldMetaData.filePath and newMetaData.dateTime == oldMetaData.dateTime:
                    # Same resource
                    return
        # regist new resource
        self.resources[resource.name] = resource
        self.metaDatas[resource] = newMetaData
        
    def releaseResource(self, resource):
        if resource:
            if resource.name in self.resources:
                self.resources.pop(resource.name)
            if resource in self.metaDatas:
                self.metaDatas.pop(resource)

    @staticmethod
    def splitResourceName(filepath):
        resourceName = os.path.splitext(os.path.split(filepath)[1])[0]
        return resourceName.lower()

    def loadResource(self, filePath):
        raise BaseException("You must implement loadResource.")

    def getResource(self, resourceName):
        return self.resources[resourceName] if resourceName in self.resources else None

    def getResourceList(self):
        return list(self.resources.values())

    def getResourceNameList(self):
        return list(self.resources.keys())
    
    def getMetaData(self, resource):
        return self.metaDatas[resource] if resource in self.metaDatas else None


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
class MeshLoader(ResourceLoader, Singleton):
    def __init__(self):
        super(MeshLoader, self).__init__(PathMeshes, ".mesh")

    def initialize(self):
        super(MeshLoader, self).initialize()

        # Regist basic meshs
        self.registResource(Triangle())
        self.registResource(Quad())

    def loadResource(self, filePath):
        try:
            # load from mesh
            f = open(filePath, 'r')
            meshData = eval(f.read())
            f.close()
            
            meshName = self.splitResourceName(filePath)
            return Mesh(meshName, meshData)
        except:
            logger.error(traceback.format_exc())
        

# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(ResourceLoader, Singleton):
    def __init__(self):
        super(TextureLoader, self).__init__(PathTextures, ".*")

    def loadResource(self, filePath):
        try:
            image = Image.open(filePath)
            ix, iy = image.size
            buffer = image.tobytes("raw", "RGBX", 0, -1)
            textureName = self.splitResourceName(filePath)
            return Texture(textureName, buffer, ix, iy)
        except:
            logger.error(traceback.format_exc())


# -----------------------#
# CLASS : ResourceManager
# -----------------------#
class ResourceManager(Singleton):
    def __init__(self):
        self.textureLoad = TextureLoader.instance()
        self.shaderLoader = ShaderLoader.instance()
        self.materialLoader = MaterialLoader.instance()
        self.meshLoader = MeshLoader.instance()

    def initialize(self):
        self.textureLoad.initialize()
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
        return self.meshLoader.getResourceNameList()

    def getMesh(self, meshName):
        return self.meshLoader.getResource(meshName)

    # FUNCTIONS : Texture

    def getTextureNameList(self):
        return self.textureLoader.getResourceNameList()

    def getTexture(self, textureName):
        return self.textureLoader.getResource(textureName)
