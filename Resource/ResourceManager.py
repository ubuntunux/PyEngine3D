import os
import glob
import configparser
import time
import traceback
import datetime

from PIL import Image

from . import *
from Core import logger
from Utilities import Singleton, getClassName
from Render import Texture2D
from Material import *
from Object import Triangle, Quad, Mesh
from Scene import SceneManager


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
    name = "ResourceLoader"

    def __init__(self, dirName, fileExt):
        self.resources = {}
        self.metaDatas = {}
        self.dirName = dirName
        self.fileExt = fileExt.lower()

    def initialize(self):
        logger.info("initialize " + getClassName(self))

        # collect shader files
        for dirname, dirnames, filenames in os.walk(self.dirName):
            for filename in filenames:
                if self.fileExt == ".*" or self.fileExt == os.path.splitext(filename)[1].lower():
                    filepath = os.path.join(dirname, filename)
                    resource = self.loadResource(filepath)
                    if resource:
                        self.registResource(resource, filepath)
                    else:
                        logger.error("%s load failed." % filename)

    def createResource(self):
        """ TODO : create resource file and regist."""
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
        resource_name = ""
        if resource is None or not hasattr(resource, "name"):
            resource_name = self.splitResourceName(filePath, self.dirName)
        else:
            resource_name = resource.name
        newMetaData = MetaData(filePath)
        # check the file is exsits resource or not.
        if resource_name in self.resources:
            oldResource = self.resources[resource_name]
            oldMetaData = self.getMetaData(oldResource)
            if oldMetaData:
                if newMetaData.filePath == oldMetaData.filePath and newMetaData.dateTime == oldMetaData.dateTime:
                    # Same resource
                    return
        # regist new resource
        self.resources[resource_name] = resource
        self.metaDatas[resource] = newMetaData

    def releaseResource(self, resource):
        if resource:
            if resource.name in self.resources:
                self.resources.pop(resource.name)
            if resource in self.metaDatas:
                self.metaDatas.pop(resource)

    @staticmethod
    def splitResourceName(filepath, workPath):
        resourceName = os.path.splitext(os.path.relpath(filepath, workPath))[0]
        resourceName.replace(os.sep, "/")
        return resourceName.lower()

    def loadResource(self, filePath):
        raise BaseException("You must implement loadResource.")

    def getResource(self, resourceName):
        if resourceName in self.resources:
            return self.resources[resourceName]
        logger.error("%s cannot found %s resource." % (self.name, resourceName))
        return None

    def getResourceList(self):
        return list(self.resources.values())

    def getResourceNameList(self):
        return list(self.resources.keys())

    def getMetaData(self, resource):
        if resource in self.metaDatas:
            return self.metaDatas[resource]
        logger.error("Not found meta data of %s." % resource.name)
        return None


# ---------------------------#
# CLASS : VertexShaderLoader
# ---------------------------#
class VertexShaderLoader(ResourceLoader, Singleton):
    name = "VertexShaderLoader"

    def __init__(self):
        super(VertexShaderLoader, self).__init__(PathShaders, ".vert")

    def loadResource(self, filePath):
        try:
            f = open(filePath, 'r')
            shaderSource = f.read()
            f.close()
            shaderName = self.splitResourceName(filePath, PathShaders)
            return VertexShader(shaderName, shaderSource)
        except:
            logger.error(traceback.format_exc())
        return None

    def close(self):
        for shader in self.resources.values():
            shader.delete()


# ---------------------------#
# CLASS : FragmentShaderLoader
# ---------------------------#
class FragmentShaderLoader(ResourceLoader, Singleton):
    name = "FragmentShaderLoader"

    def __init__(self):
        super(FragmentShaderLoader, self).__init__(PathShaders, ".frag")

    def loadResource(self, filePath):
        try:
            f = open(filePath, 'r')
            shaderSource = f.read()
            f.close()
            shaderName = self.splitResourceName(filePath, PathShaders)
            return FragmentShader(shaderName, shaderSource)
        except:
            logger.error(traceback.format_exc())
        return None

    def close(self):
        for shader in self.resources.values():
            shader.delete()


# -----------------------#
# CLASS : MaterialLoader
# -----------------------#
class MaterialLoader(ResourceLoader, Singleton):
    name = "MaterialLoader"

    def __init__(self):
        super(MaterialLoader, self).__init__(PathMaterials, ".mat")
        self.materials = {}

    def loadResource(self, filePath):
        logger.info("Regist %s material template filepath " % self.splitResourceName(filePath, self.dirName))
        return filePath

    def getCombinedMaterial(self, mat_name, vs_name, fs_name):
        combined_name = "_".join([mat_name, vs_name, fs_name])

        if combined_name in self.materials:
            return self.materials[combined_name]
        # create material and return
        elif mat_name in self.resources:
            try:
                material_filePath = self.resources[mat_name]
                f = open(material_filePath, 'r')
                material_template = f.read()
                f.close()
                material = Material(mat_name=mat_name, vs_name=vs_name, fs_name=fs_name,
                                    material_template=material_template)
                # regist new combined material
                self.materials[combined_name] = material
                return material if material.valid else None
            except:
                logger.error(traceback.format_exc())
        else:
            logger.error("There isn't %s material." % mat_name)
        return None


# -----------------------#
# CLASS : MaterialInstanceLoader
# -----------------------#
class MaterialInstanceLoader(ResourceLoader, Singleton):
    name = "MaterialInstanceLoader"

    def __init__(self):
        super(MaterialInstanceLoader, self).__init__(PathMaterials, ".matinst")

    def loadResource(self, filePath):
        material_instance_name = self.splitResourceName(filePath, PathMaterials)
        material_instance = MaterialInstance(material_instance_name=material_instance_name, filePath=filePath)
        return material_instance if material_instance.valid else None


# -----------------------#
# CLASS : MeshLoader
# -----------------------#
class MeshLoader(ResourceLoader, Singleton):
    name = "MeshLoader"

    def __init__(self):
        super(MeshLoader, self).__init__(PathMeshes, ".mesh")

    def initialize(self):
        super(MeshLoader, self).initialize()

        # Regist basic meshs
        self.registResource(Triangle())
        self.registResource(Quad())

        # convert resource
        for dirname, dirnames, filenames in os.walk(PathMeshes):
            for filename in filenames:
                filepath = os.path.join(dirname, filename)
                filepath = os.path.abspath(filepath)
                file_ext = os.path.splitext(filename)[1].lower()
                meshName = self.splitResourceName(filepath, PathMeshes)
                mesh = self.getResource(meshName)
                mTime = os.path.getmtime(filepath)
                mTime = str(datetime.datetime.fromtimestamp(mTime))
                if mesh is None or mTime != mesh.modifyTime:
                    self.convertResource(filepath, file_ext)

    def loadResource(self, filePath):
        try:
            # load from mesh
            f = open(filePath, 'r')
            mesh_data = eval(f.read())
            f.close()

            meshName = self.splitResourceName(filePath, PathMeshes)
            return Mesh(meshName, mesh_data)
        except:
            logger.error(traceback.format_exc())
        return None

    def convertResource(self, filepath, file_ext):
        mesh_data = None
        if file_ext == ".obj":
            obj = OBJ(filepath, 1, True)
            mesh_data = obj.get_mesh_data()
        elif file_ext == ".dae":
            obj = Collada(filepath)
            mesh_data = obj.get_mesh_data()

        if mesh_data:
            mTime = os.path.getmtime(filepath)
            modifyTime = str(datetime.datetime.fromtimestamp(mTime))
            fileSize = os.path.getsize(filepath)
            mesh_data['fileSize'] = fileSize
            mesh_data['filePath'] = filepath
            mesh_data['modifyTime'] = modifyTime

            meshName = self.splitResourceName(filepath, PathMeshes)
            mesh = Mesh(meshName, mesh_data)
            saveFilePath = mesh.saveToFile(PathMeshes)
            self.registResource(mesh, saveFilePath)


# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(ResourceLoader, Singleton):
    name = "TextureLoader"

    def __init__(self):
        super(TextureLoader, self).__init__(PathTextures, ".*")

    def get_texture_format(self, str_image_mode):
        if str_image_mode == "RGB":
            return GL_RGB
        elif str_image_mode == "RGBA":
            return GL_RGBA
        return GL_RGBA

    def loadResource(self, filePath):
        try:
            image = Image.open(filePath)
            ix, iy = image.size
            data = image.tobytes("raw", image.mode, 0, -1)
            texture_name = self.splitResourceName(filePath, PathTextures)
            internal_format = self.get_texture_format(image.mode)
            texture_format = internal_format
            return Texture2D(texture_name, internal_format, ix, iy, texture_format, GL_UNSIGNED_BYTE, data)
        except:
            logger.error(traceback.format_exc())
        return None

    def create_texture(self, textureFileName, internal_format=GL_RGBA, width=1024, height=1024, format=GL_BGRA,
                       data_type=GL_UNSIGNED_BYTE, data=None, mipmap=True):
        texture = self.getResource(textureFileName)
        if texture:
            return texture

        texture = Texture2D(textureFileName, internal_format, width, height, format, data_type, data, mipmap)
        self.registResource(texture, "")
        return texture


# -----------------------#
# CLASS : ResourceManager
# -----------------------#
class ResourceManager(Singleton):
    name = "ResourceManager"

    def __init__(self):
        self.sceneManager = None
        self.textureLoader = TextureLoader.instance()
        self.vertexShaderLoader = VertexShaderLoader.instance()
        self.fragmentShaderLoader = FragmentShaderLoader.instance()
        self.materialLoader = MaterialLoader.instance()
        self.material_instanceLoader = MaterialInstanceLoader.instance()
        self.meshLoader = MeshLoader.instance()

    def initialize(self):
        self.textureLoader.initialize()
        self.vertexShaderLoader.initialize()
        self.fragmentShaderLoader.initialize()
        self.materialLoader.initialize()
        self.material_instanceLoader.initialize()
        self.meshLoader.initialize()
        self.sceneManager = SceneManager.instance()

    def close(self):
        pass

    def getResourceList(self):
        """
        :return [(resource name, resource type)]:
        """
        result = []
        for resName in self.getVertexShaderNameList():
            result.append((resName, getClassName(self.getVertexShader(resName))))
        for resName in self.getFragmentShaderNameList():
            result.append((resName, getClassName(self.getFragmentShader(resName))))
        for resName in self.getMaterialTemplateNameList():
            result.append((resName, getClassName(self.getMaterialTemplate(resName))))
        for resName in self.getMaterialInstanceNameList():
            result.append((resName, getClassName(self.getMaterialInstance(resName))))
        for resName in self.getMeshNameList():
            result.append((resName, getClassName(self.getMesh(resName))))
        for resName in self.getTextureNameList():
            result.append((resName, getClassName(self.getTexture(resName))))
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
        if type(resType) == str:
            resType = eval(resType)

        if resType == FragmentShader:
            resource = self.getFragmentShader(resName)
        elif resType == VertexShader:
            resource = self.getVertexShader(resName)
        elif resType == Material:
            resource = self.getMaterialTemplate(resName)
        elif resType == MaterialInstance:
            resource = self.getMaterialInstance(resName)
        elif issubclass(resType, Mesh):
            resource = self.getMesh(resName)
        elif resType == Texture2D:
            resource = self.getTexture(resName)
        else:
            logger.error("%s(%s) is a unknown type resource." % (resName, resType))
        return resource

    def createResource(self, resName, resType):
        resource = self.getResource(resName, resType)
        resType = type(resource)
        if resource:
            if resType == FragmentShader:
                pass
            elif resType == VertexShader:
                pass
            elif resType == Material:
                pass
            elif resType == MaterialInstance:
                pass
            elif issubclass(resType, Mesh):
                return self.sceneManager.createMeshHere(resource)
            elif resType == Texture2D:
                pass
        return None
        logger.error("Can't create %s(%s)." % (resName, resType))

    # FUNCTIONS : Shader

    def getVertexShader(self, shaderName):
        return self.vertexShaderLoader.getResource(shaderName)

    def getFragmentShader(self, shaderName):
        return self.fragmentShaderLoader.getResource(shaderName)

    def getVertexShaderNameList(self):
        return self.vertexShaderLoader.getResourceNameList()

    def getFragmentShaderNameList(self):
        return self.fragmentShaderLoader.getResourceNameList()

    # FUNCTIONS : Material

    def getMaterialTemplateNameList(self):
        return self.materialLoader.getResourceNameList()

    def getMaterialTemplate(self, mat_name):
        return self.materialLoader.getResource(mat_name)

    def getCombinedMaterial(self, mat_name, vs_name, fs_name):
        return self.materialLoader.getCombinedMaterial(mat_name, vs_name, fs_name)

    # FUNCTIONS : MaterialInstance

    def getMaterialInstanceNameList(self):
        return self.material_instanceLoader.getResourceNameList()

    def getMaterialInstance(self, name):
        return self.material_instanceLoader.getResource(name)

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
