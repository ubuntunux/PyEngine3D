import os
import glob
import configparser
import time
import traceback
import datetime
import pprint

from PIL import Image

from Core import logger, SceneManager, log_level
from Object import Triangle, Quad, Mesh
from OpenGLContext import CreateTextureFromFile, Shader, Material, Texture2D
from Render import MaterialInstance
from Utilities import Singleton, GetClassName, Config
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
    def __init__(self, resource_filepath):
        self.resource_filepath = ""
        self.resource_modify_time = ""
        self.source_filepath = ""
        self.source_modify_time = ""

        self.set_resource_meta_data(resource_filepath)

    def set_resource_meta_data(self, resource_filepath, modify_time=None):
        self.resource_filepath = resource_filepath
        self.resource_modify_time = modify_time if modify_time else get_modify_time_of_file(resource_filepath)

    def set_source_meta_data(self, source_filepath, modify_time=None):
        self.source_filepath = source_filepath
        self.source_modify_time = modify_time if modify_time else get_modify_time_of_file(source_filepath)


# -----------------------#
# CLASS : Resource
# -----------------------#
class Resource:
    def __init__(self, resource_name, data=None):
        self.name = resource_name
        self.data = data


# -----------------------#
# CLASS : ResourceLoader
# -----------------------#
class ResourceLoader(object):
    name = "ResourceLoader"
    resource_path = PathResources
    fileExt = ['.*',]
    NEED_TO_CONVERT_RESOUCE = False

    def __init__(self):
        self.resources = {}
        self.metaDatas = {}

    def initialize(self):
        """
         Do load_resource and regist_resource.
        """
        logger.info("initialize " + GetClassName(self))

        # collect resource files
        for dirname, dirnames, filenames in os.walk(self.resource_path):
            for filename in filenames:
                fileExt = os.path.splitext(filename)[1].lower()
                if fileExt == '.meta':
                    continue

                if ".*" in self.fileExt or fileExt in self.fileExt:
                    filepath = os.path.abspath(os.path.join(dirname, filename))
                    # get Resource and MetaData
                    resource, meta_data = self.load_resource(filepath)
                    if resource:
                        self.regist_resource(resource, meta_data)
                    else:
                        logger.error("%s load failed." % filename)

        # If you use external files, convert the resources.
        if self.NEED_TO_CONVERT_RESOUCE:
            self.find_convert_resources(self.resource_path)

    def createResource(self):
        """ TODO : create resource file and regist."""
        pass

    def find_convert_resources(self, resource_path):
        """
        Desc : If you use external files, convert the resources.
        """
        for dirname, dirnames, filenames in os.walk(resource_path):
            for filename in filenames:
                source_filepath = os.path.join(dirname, filename)
                file_ext = os.path.splitext(source_filepath)[1].lower()
                if file_ext not in self.fileExt:
                    source_filepath = os.path.abspath(source_filepath)
                    resource_name = self.getResourceName(source_filepath, resource_path)
                    resource = self.getResource(resource_name, noWarn=True)
                    convert_resource = resource is None
                    if not convert_resource:
                        meta_data = self.getMetaData(resource_name, noWarn=True)
                        if meta_data:
                            source_modify_time = get_modify_time_of_file(source_filepath)
                            if meta_data.source_filepath != source_filepath \
                                    or meta_data.source_modify_time != source_modify_time:
                                convert_resource = True
                    if convert_resource:
                        self.convert_resource(source_filepath)

    def convert_resource(self, source_filepath):
        """
        Desc : do resource convert, save_simple_format and regist_resource.
        :param source_filepath:
        """
        pass

    def deleteResource(self, resource):
        """ delete resource file and release."""
        if resource:
            self.releaseResource(resource)

    def regist_resource(self, resource, meta_data=None):
        """
        :param resource: resource object ( Texture2D, Mesh, Material ... )
        """
        self.resources[resource.name] = resource
        if meta_data is not None:
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
        :return: tuple(Resource object, MetaData)
        """
        raise BaseException("You must implement load_resource.")

    def load_simple_format(self, filePath):
        try:
            # load from mesh
            f = open(filePath, 'r')
            load_data = eval(f.read())
            f.close()
            meta_data = MetaData(filePath)
            meta_data.set_source_meta_data(load_data['source_filepath'], load_data['source_modify_time'])
            return load_data['resource_data'], meta_data
        except:
            logger.error(traceback.format_exc())
        return None

    def save_simple_format(self, save_filepath, resource_data, meta_data):
        logger.info("Save : %s" % save_filepath)
        try:
            # save resource
            f = open(save_filepath, 'w')
            save_data = dict(
                source_filepath=meta_data.source_filepath,
                source_modify_time=meta_data.source_modify_time,
                resource_data=resource_data
            )
            pprint.pprint(save_data, f, compact=True)
            f.close()
            # refresh meta data
            meta_data.set_resource_meta_data(save_filepath)
        except:
            logger.error(traceback.format_exc())

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

    def getMetaData(self, resource_name, noWarn=False):
        if resource_name in self.metaDatas:
            return self.metaDatas[resource_name]
        if not noWarn:
            logger.error("Not found meta data of %s." % resource_name)
        return None


# ---------------------------#
# CLASS : ShaderLoader
# ---------------------------#
class ShaderLoader(ResourceLoader, Singleton):
    name = "ShaderLoader"
    resource_path = PathShaders
    fileExt = ['.glsl', ]

    def load_resource(self, filePath):
        try:
            shaderName = self.getResourceName(filePath, self.resource_path)
            return Shader(shaderName, filePath), MetaData(filePath)
        except:
            logger.error(traceback.format_exc())
        return None, None

    def close(self):
        for shader in self.resources.values():
            shader.delete()


# -----------------------#
# CLASS : MaterialLoader
# -----------------------#
class MaterialLoader(ResourceLoader, Singleton):
    name = "MaterialLoader"
    resource_path = PathMaterials
    fileExt = ['.mat', ]

    def __init__(self):
        super(MaterialLoader, self).__init__()
        self.materials = {}

    def load_resource(self, filePath):
        logger.info("Regist %s material template filepath " % self.getResourceName(filePath, self.resource_path))
        return filePath, MetaData(filePath)

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
    resource_path = PathMaterials
    fileExt = ['.matinst', ]

    def load_resource(self, filePath):
        material_instance_name = self.getResourceName(filePath, self.resource_path)
        material_instance = MaterialInstance(material_instance_name=material_instance_name, filePath=filePath)
        return material_instance if material_instance.valid else None, MetaData(filePath)


# -----------------------#
# CLASS : MeshLoader
# -----------------------#
class MeshLoader(ResourceLoader, Singleton):
    name = "MeshLoader"
    resource_path = PathMeshes
    fileExt = ['.mesh', ]
    NEED_TO_CONVERT_RESOUCE = True

    def initialize(self):
        # load and regist resource
        super(MeshLoader, self).initialize()

        # Regist basic meshs
        self.regist_resource(Triangle())
        self.regist_resource(Quad())

    def load_resource(self, filePath):
        resource_data, meta_data = self.load_simple_format(filePath)
        mesh_name = self.getResourceName(filePath, self.resource_path)
        mesh = Mesh(mesh_name, resource_data)
        return mesh, meta_data

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
            meshName = self.getResourceName(source_filepath, self.resource_path)
            # create mesh
            mesh = Mesh(meshName, geometry_datas)
            save_filepath = os.path.join(self.resource_path, meshName) + ".mesh"

            meta_data = self.getMetaData(meshName, noWarn=True) or MetaData(save_filepath)
            meta_data.set_source_meta_data(source_filepath)
            self.save_simple_format(save_filepath, geometry_datas, meta_data)
            self.regist_resource(mesh, meta_data)


# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(ResourceLoader, Singleton):
    name = "TextureLoader"
    resource_path = PathTextures
    fileExt = ['.tex2d', ]
    NEED_TO_CONVERT_RESOUCE = True

    def load_resource(self, filePath):
        resource_data, meta_data = self.load_simple_format(filePath)
        texture_name = self.getResourceName(filePath, self.resource_path)
        image_mode = resource_data['image_mode']
        width = resource_data['width']
        height = resource_data['height']
        data = resource_data['data']
        return CreateTextureFromFile(texture_name, image_mode, width, height, data), meta_data

    def convert_resource(self, source_filepath):
        print("convert_resource", source_filepath)
        file_ext = os.path.splitext(source_filepath)[1].lower()
        if file_ext not in [".gif", ".jpg", ".jpeg", ".png", ".bmp", ".tga", ".tif", ".tiff", ".dds", ".ktx"]:
            return

        try:
            logger.info("Convert Resource : %s" % source_filepath)
            texture_name = self.getResourceName(source_filepath, self.resource_path)
            # create texture
            image = Image.open(source_filepath)
            image_mode = image.mode
            width, height = image.size
            data = image.tobytes("raw", image.mode, 0, -1)
            texture = CreateTextureFromFile(texture_name, image_mode, width, height, data)

            save_filepath = os.path.join(self.resource_path, texture_name) + ".tex2d"

            meta_data = self.getMetaData(texture_name, noWarn=True) or MetaData(save_filepath)
            meta_data.set_source_meta_data(source_filepath)
            save_data = dict(image_mode=image_mode, width=width, height=height, data=data)
            self.save_simple_format(save_filepath, save_data, meta_data)
            self.regist_resource(texture, meta_data)
        except:
            logger.error(traceback.format_exc())
        return None, None


# -----------------------#
# CLASS : SceneLoader
# -----------------------#
class SceneLoader(ResourceLoader, Singleton):
    name = "ShaderLoader"
    resource_path = PathScenes
    fileExt = ['.scene', ]

    def load_resource(self, filePath):
        try:
            scene_name = self.getResourceName(filePath, self.resource_path)
            scene = Resource(scene_name, filePath)
            meta_data = MetaData(filePath)
            return scene, meta_data
        except:
            logger.error(traceback.format_exc())
        return None, None

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
        result += [(resName, GetClassName(self.getScene(resName))) for resName in self.getSceneNameList()]
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
