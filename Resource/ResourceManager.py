import os
import glob
import configparser
import time
import traceback
import datetime
import pprint

from PIL import Image

from Core import logger, SceneManager
from Object import Triangle, Quad, Mesh
from OpenGLContext import CreateTextureFromFile, Shader, Material, Texture2D
from Render import MaterialInstance
from Utilities import Singleton, GetClassName
from . import *


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
        logger.info("initialize " + GetClassName(self))

        # collect shader files
        for dirname, dirnames, filenames in os.walk(self.dirName):
            for filename in filenames:
                if self.fileExt == ".*" or self.fileExt == os.path.splitext(filename)[1].lower():
                    filepath = os.path.join(dirname, filename)
                    resource = self.call_load_resource(filepath)
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
        if resource is None or not hasattr(resource, "name"):
            resource_name = self.getResourceName(filePath, self.dirName)
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
    def getResourceName(filepath, workPath):
        resourceName = os.path.splitext(os.path.relpath(filepath, workPath))[0]
        resourceName = resourceName.replace(os.sep, ".")
        return resourceName.lower()

    def call_load_resource(self, filePath):
        raise BaseException("You must implement call_load_resource.")

    def getResource(self, resourceName, noWarn=False):
        if resourceName in self.resources:
            return self.resources[resourceName]
        if not noWarn:
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
# CLASS : ShaderLoader
# ---------------------------#
class ShaderLoader(ResourceLoader, Singleton):
    name = "ShaderLoader"

    def __init__(self):
        super(ShaderLoader, self).__init__(PathShaders, ".glsl")

    def call_load_resource(self, filePath):
        try:
            shaderName = self.getResourceName(filePath, PathShaders)
            return Shader(shaderName, filePath)
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

    def call_load_resource(self, filePath):
        logger.info("Regist %s material template filepath " % self.getResourceName(filePath, self.dirName))
        return filePath

    def generate_material_name(self, shader_name, macros=None):
        if macros:
            keys = sorted(macros.keys())
            add_name = [key + "_" + str(macros[key]) for key in keys]
            return shader_name + "_" + "_".join(add_name)
        return shader_name

    def getMaterial(self, shader_name, macros=None):
        material_name = self.generate_material_name(shader_name, macros)
        if material_name in self.materials:
            return self.materials[material_name]
        # create new material and return
        else:
            try:
                shader = ResourceManager.instance().getShader(shader_name)
                if shader:
                    material = Material(material_name, shader, macros)
                    if material.valid:
                        self.materials[material_name] = material
                        return material
            except:
                logger.error(traceback.format_exc())
        logger.error("There isn't %s material. (Shader : %s)" % (material_name, shader_name))
        return None


# -----------------------#
# CLASS : MaterialInstanceLoader
# -----------------------#
class MaterialInstanceLoader(ResourceLoader, Singleton):
    name = "MaterialInstanceLoader"

    def __init__(self):
        super(MaterialInstanceLoader, self).__init__(PathMaterials, ".matinst")

    def call_load_resource(self, filePath):
        material_instance_name = self.getResourceName(filePath, PathMaterials)
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
                meshName = self.getResourceName(filepath, PathMeshes)
                mesh = self.getResource(meshName, True)
                mTime = os.path.getmtime(filepath)
                mTime = str(datetime.datetime.fromtimestamp(mTime))
                if mesh is None or mTime != mesh.modify_time:
                    self.convertResource(filepath, file_ext)

    def call_load_resource(self, filePath):
        try:
            # load from mesh
            f = open(filePath, 'r')
            datas = eval(f.read())
            f.close()

            file_path = datas['file_path'] if 'file_path' in datas else ""
            modify_time = datas['modify_time'] if 'modify_time' in datas else ""
            geometry_datas = datas['geometry_datas'] if 'geometry_datas' in datas else []
            meshName = self.getResourceName(filePath, PathMeshes)
            return Mesh(meshName, geometry_datas, file_path, modify_time)
        except:
            logger.error(traceback.format_exc())
        return None

    def saveResource(self, mesh, savefilepath):
        logger.info("Save %s : %s" % (GetClassName(mesh), savefilepath))
        try:
            f = open(savefilepath, 'w')
            datas = dict(file_path=mesh.file_path,
                         modify_time=mesh.modify_time,
                         geometry_datas=mesh.geometry_datas)
            pprint.pprint(datas, f, compact=True)
            f.close()
        except:
            logger.error(traceback.format_exc())
        return savefilepath

    def convertResource(self, filepath, file_ext):
        geometry_datas = None
        if file_ext == ".obj":
            obj = OBJ(filepath, 1, True)
            geometry_datas = obj.get_geometry_data()
        elif file_ext == ".dae":
            obj = Collada(filepath)
            geometry_datas = obj.get_geometry_data()

        # Test Code - Support only 1 geometry!!
        if geometry_datas:
            mTime = os.path.getmtime(filepath)
            modifyTime = str(datetime.datetime.fromtimestamp(mTime))
            meshName = self.getResourceName(filepath, PathMeshes)
            mesh = Mesh(meshName, geometry_datas, filepath, modifyTime)
            saveFilePath = os.path.join(PathMeshes, meshName) + ".mesh"
            self.saveResource(mesh, saveFilePath)
            self.registResource(mesh, saveFilePath)


# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(ResourceLoader, Singleton):
    name = "TextureLoader"

    def __init__(self):
        super(TextureLoader, self).__init__(PathTextures, ".*")

    def call_load_resource(self, filePath):
        try:
            image = Image.open(filePath)
            ix, iy = image.size
            data = image.tobytes("raw", image.mode, 0, -1)
            texture_name = self.getResourceName(filePath, PathTextures)
            return CreateTextureFromFile(texture_name, image.mode, ix, iy, data)
        except:
            logger.error(traceback.format_exc())
        return None


# -----------------------#
# CLASS : SceneLoader
# -----------------------#
class SceneLoader(ResourceLoader, Singleton):
    name = "ShaderLoader"

    def __init__(self):
        super(SceneLoader, self).__init__(PathScenes, ".scene")

    def call_load_resource(self, filePath):
        try:
            shaderName = self.getResourceName(filePath, PathShaders)
            return Shader(shaderName, filePath)
        except:
            logger.error(traceback.format_exc())
        return None

    def close(self):
        for shader in self.resources.values():
            shader.delete()


# -----------------------#
# CLASS : ResourceManager
# -----------------------#
class ResourceManager(Singleton):
    name = "ResourceManager"

    def __init__(self):
        self.textureLoader = TextureLoader.instance()
        self.shaderLoader = ShaderLoader.instance()
        self.materialLoader = MaterialLoader.instance()
        self.material_instanceLoader = MaterialInstanceLoader.instance()
        self.meshLoader = MeshLoader.instance()
        self.sceneLoader = SceneLoader.instance()

        self.sceneManager = None

    def initialize(self):
        # initialize
        self.textureLoader.initialize()
        self.shaderLoader.initialize()
        self.materialLoader.initialize()
        self.material_instanceLoader.initialize()
        self.meshLoader.initialize()
        self.sceneLoader.initialize()

        # get scene manager
        self.sceneManager = SceneManager.SceneManager.instance()

    def close(self):
        pass

    def getResourceList(self):
        """
        :return [(resource name, resource type)]:
        """
        result = []
        result += [(resName, GetClassName(self.getShader(resName))) for resName in self.getShaderNameList()]
        result += [(resName, GetClassName(self.getMaterialTemplate(resName))) for resName in
                   self.getMaterialTemplateNameList()]
        result += [(resName, GetClassName(self.getMaterialInstance(resName))) for resName in
                   self.getMaterialInstanceNameList()]
        result += [(resName, GetClassName(self.getMesh(resName))) for resName in self.getMeshNameList()]
        result += [(resName, GetClassName(self.getTexture(resName))) for resName in self.getTextureNameList()]
        result += [(resName, GetClassName(self.getTexture(resName))) for resName in self.getTextureNameList()]
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

        if resType == Shader:
            resource = self.getShader(resName)
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
            if resType == Shader:
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

    def getShader(self, shaderName):
        return self.shaderLoader.getResource(shaderName)

    def getShaderNameList(self):
        return self.shaderLoader.getResourceNameList()

    # FUNCTIONS : Material

    def getMaterialTemplateNameList(self):
        return self.materialLoader.getResourceNameList()

    def getMaterialTemplate(self, mat_name):
        return self.materialLoader.getResource(mat_name)

    def getMaterial(self, shader_name, macros=None):
        return self.materialLoader.getMaterial(shader_name, macros)

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

    # FUNCTIONS : Scene

    def getSceneNameList(self):
        return self.sceneLoader.getResourceNameList()

    def getScene(self, SceneName):
        return self.sceneLoader.getResource(SceneName)
