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


def get_modify_time_of_file(filepath):
    timeStamp = 0.0
    if filepath != "" and os.path.exists(filepath):
        timeStamp = os.path.getmtime(filepath)
    return str(datetime.datetime.fromtimestamp(timeStamp))


# -----------------------#
# CLASS : MetaData
# -----------------------#
class MetaData:
    def __init__(self, resource, filePath, source_filepath):
        self.resource_name = resource.name
        self.resource_class = GetClassName(resource)
        self.filePath = ""
        self.modifyTime = get_modify_time_of_file("")
        self.source_filepath = ""
        self.source_modifyTime = get_modify_time_of_file("")

        self.set_meta_data(filePath)
        self.set_source_meta_data(source_filepath)

    def set_meta_data(self, filepath, modify_time=None):
        self.filePath = filepath
        self.modifyTime = get_modify_time_of_file(filepath) if modify_time is None else modify_time

    def set_source_meta_data(self, source_filepath, modify_time=None):
        self.source_filepath = source_filepath
        self.source_modifyTime = get_modify_time_of_file(source_filepath) if modify_time is None else modify_time

    def save(self, filepath):
        pass

    def load(self, filepath):
        pass


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
        """
         Do load_resource and regist_resource.
        """
        logger.info("initialize " + GetClassName(self))

        # collect resource files
        for dirname, dirnames, filenames in os.walk(self.dirName):
            for filename in filenames:
                if self.fileExt == ".*" or self.fileExt == os.path.splitext(filename)[1].lower():
                    filepath = os.path.join(dirname, filename)
                    resource = self.load_resource(filepath)
                    if resource:
                        self.regist_resource(resource, filepath)
                    else:
                        logger.error("%s load failed." % filename)

    def createResource(self):
        """ TODO : create resource file and regist."""
        pass

    def deleteResource(self, resource):
        """ delete resource file and release."""
        if resource:
            metaData = self.getMetaData(resource.name)
            self.releaseResource(resource)
            if metaData:
                filePath = metaData.filePath
                if os.path.exists(filePath):
                    os.remove(filePath)
                    logger.info("Remove %s file" & filePath)

    def regist_resource(self, resource, meta_data=None):
        """
        :param resource: resource object ( Texture2D, Mesh, Material ... )
        :param meta_dat: MetaData
        """
        self.resources[resource.name] = resource
        if meta_data:
            self.metaDatas[resource.name] = meta_data

    def release_resource(self, resource):
        if resource:
            if resource.name in self.resources:
                self.resources.pop(resource.name)
            if resource.name in self.metaDatas:
                self.metaDatas.pop(resource.name)

    @staticmethod
    def getResourceName(filepath, workPath):
        resourceName = os.path.splitext(os.path.relpath(filepath, workPath))[0]
        resourceName = resourceName.replace(os.sep, ".")
        return resourceName.lower()

    def load_resource(self, filePath):
        """
        :return: Resource object
        """
        raise BaseException("You must implement load_resource.")

    def load_meta_data(self, resource, filepath, source_filepath):
        pass

    def save_meta_data(self, resource, filepath, source_filepath):
        pass

    def save_resource(self, resource):
        meta_data = self.getMetaData(resource.name)
        if meta_data:
            savefilepath = meta_data.filePath
            logger.info("Save %s : %s" % (GetClassName(resource), savefilepath))
            try:
                f = open(savefilepath, 'w')
                save_data = resource.get_save_data()
                pprint.pprint(save_data, f, compact=True)
                f.close()
            except:
                logger.error(traceback.format_exc())
        else:
            logger.info("Failed to save %s %s. The resource has no meta data." % (GetClassName(resource), resource.name))

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

    def getMetaData(self, resource_name):
        if resource_name in self.metaDatas:
            return self.metaDatas[resource_name]
        logger.error("Not found meta data of %s." % resource_name)
        return None


# ---------------------------#
# CLASS : ShaderLoader
# ---------------------------#
class ShaderLoader(ResourceLoader, Singleton):
    name = "ShaderLoader"

    def __init__(self):
        super(ShaderLoader, self).__init__(PathShaders, ".glsl")

    def load_resource(self, filePath):
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

    def load_resource(self, filePath):
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

    def load_resource(self, filePath):
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
        # load and regist resource
        super(MeshLoader, self).initialize()

        # Regist basic meshs
        self.regist_resource(Triangle())
        self.regist_resource(Quad())

        # convert resource
        for dirname, dirnames, filenames in os.walk(PathMeshes):
            for filename in filenames:
                source_filepath = os.path.join(dirname, filename)
                file_ext = os.path.splitext(source_filepath)[1].lower()
                if file_ext != self.fileExt:
                    # source_filepath = os.path.abspath(source_filepath)
                    meshName = self.getResourceName(source_filepath, PathMeshes)
                    mesh = self.getResource(meshName, True)
                    convert_resource = False
                    if mesh is None:
                        convert_resource = True
                    else:
                        meta_data = self.getMetaData(mesh.name)
                        source_modifyTime = get_modify_time_of_file(source_filepath)
                        if meta_data.source_modifyTime != source_modifyTime:
                            convert_resource = True
                    if convert_resource:
                        self.convert_resource(source_filepath)

    def load_resource(self, filePath):
        try:
            # load from mesh
            f = open(filePath, 'r')
            geometry_datas = eval(f.read())
            f.close()
            meshName = self.getResourceName(filePath, PathMeshes)
            return Mesh(meshName, geometry_datas)
        except:
            logger.error(traceback.format_exc())
        return None

    def convert_resource(self, source_filepath):
        """
        If the resource is newer, save and register the resource.
        """
        file_ext = os.path.splitext(source_filepath)[1].lower()
        if file_ext == ".obj":
            obj = OBJ(source_filepath, 1, True)
            geometry_datas = obj.get_geometry_data()
        elif file_ext == ".dae":
            obj = Collada(source_filepath)
            geometry_datas = obj.get_geometry_data()
        else:
            return

        logger.info("Convert Resource : %s" % source_filepath)

        if geometry_datas:
            meshName = self.getResourceName(source_filepath, PathMeshes)
            # create mesh
            mesh = Mesh(meshName, geometry_datas)
            saveFilePath = os.path.join(PathMeshes, meshName) + ".mesh"
            self.regist_resource(mesh, saveFilePath, source_filepath)
            self.save_resource(mesh)


# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(ResourceLoader, Singleton):
    name = "TextureLoader"

    def __init__(self):
        super(TextureLoader, self).__init__(PathTextures, ".*")

    def load_resource(self, filePath):
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

    def load_resource(self, filePath):
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
