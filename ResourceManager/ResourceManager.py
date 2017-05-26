import os
import glob
import configparser
import time
import traceback
import datetime
import pprint
import re
import pickle
import gzip
from collections import OrderedDict
from distutils.dir_util import copy_tree

from PIL import Image

from Common import logger, log_level
from App import CoreManager
from Object import Triangle, Quad, Mesh, MaterialInstance
from OpenGLContext import CreateTextureFromFile, Shader, Material, Texture2D
from Utilities import Attributes, Singleton, Config, Logger
from Utilities import GetClassName, is_gz_compressed_file, check_directory_and_mkdir, get_modify_time_of_file
from . import Collada, OBJ


# -----------------------#
# CLASS : MetaData
# -----------------------#
class MetaData:
    def __init__(self, resource_version, resource_filepath):
        self.resource_version = resource_version
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
    def __init__(self, resource_name):
        logger.info("Create Resource : %s" % resource_name)
        self.name = resource_name
        self.attributes = Attributes()

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        pass


# -----------------------#
# CLASS : ResourceLoader
# -----------------------#
class ResourceLoader(object):
    name = "ResourceLoader"
    resource_dir_name = 'Fonts'
    resource_version = 0
    resource_type_name = 'None'
    fileExt = '.*'
    externalFileExt = {}  # example, { 'WaveFront': '.obj' }
    USE_EXTERNAL_RESOURCE = False
    USE_FILE_COMPRESS_TO_SAVE = True

    def __init__(self, core_manager, root_path):
        self.core_manager = core_manager
        self.scene_manager = core_manager.sceneManager
        self.resource_path = os.path.join(root_path, self.resource_dir_name)
        check_directory_and_mkdir(self.resource_path)

        self.gabage_resources = []
        self.need_to_convert_resources = []
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
                fileExt = os.path.splitext(filename)[1]
                if fileExt == '.meta':
                    continue

                if ".*" == self.fileExt or fileExt == self.fileExt:
                    filepath = os.path.join(dirname, filename)
                    # get Resource and MetaData
                    resource, meta_data = self.load_resource(filepath)
                    self.regist_resource(resource, meta_data)
                    convert_resource = True if resource is None else self.is_need_to_convert(resource)
                    if meta_data and os.path.exists(meta_data.source_filepath):
                        if not convert_resource:
                            # check source file is newer or same.
                            source_modify_time = get_modify_time_of_file(meta_data.source_filepath)
                            if meta_data.resource_version != self.resource_version:
                                convert_resource = True
                                logger.log(Logger.MINOR_INFO, "Resource version changed. %d => %d" %
                                           (meta_data.resource_version, self.resource_version))
                            elif meta_data.source_modify_time != source_modify_time:
                                convert_resource = True
                                logger.log(Logger.MINOR_INFO, "Resource was modified.")
                        if convert_resource:
                            self.convert_resource(filepath, meta_data.source_filepath)
                    if not convert_resource and (resource is None or meta_data is None):
                        logger.error("%s load failed." % filename)

        # If you use external files, convert the resources.
        if self.USE_EXTERNAL_RESOURCE:
            for dirname, dirnames, filenames in os.walk(self.resource_path):
                for filename in filenames:
                    source_filepath = os.path.join(dirname, filename)
                    file_ext = os.path.splitext(source_filepath)[1]
                    if file_ext in self.externalFileExt.values():
                        # source_filepath = os.path.abspath(source_filepath)
                        resource_name = self.getResourceName(source_filepath, self.resource_path)
                        resource_filepath = os.path.join(self.resource_path, resource_name + self.fileExt)
                        if self.getResource(resource_name, noWarn=True) is None:
                            logger.log(Logger.MINOR_INFO, "Find new resource. %s" % source_filepath)
                            self.convert_resource(resource_filepath, source_filepath)
                        else:
                            meta_data = self.getMetaData(resource_name)
                            if meta_data.source_filepath != source_filepath:
                                self.convert_resource(resource_filepath, source_filepath)
                                logger.warn(
                                    "There is another source file.\nOriginal source file : %s\nAnother source file : %s" %
                                    (meta_data.source_filepath, source_filepath))
        # clear
        self.need_to_convert_resources = []

    def get_new_resource_name(self):
        num = 0
        while True:
            new_name = "%s_%d" % (self.resource_type_name, num)
            if new_name not in self.resources:
                return new_name
            num += 1
        return ''

    def add_resource_to_scene(self, resource_name):
        """
        desc: add resource to scene.
        return resource
        """
        logger.warn("add_resource_to_scene is not implemented.")
        return None

    def open_resource(self, resource_name):
        '''
        Actually open a resource file.
        '''
        pass

    def create_resource(self, resource_name):
        if resource_name in self.resources:
            return self.getResource(resource_name)
        return Resource(resource_name)

    def create_resource_and_save(self, resource_name, resource_data):
        resource = self.create_resource(resource_name)
        self.save_simple_format_and_register(resource, resource_data)

    def delete_resource(self, resource):
        """ delete resource file and release."""
        if resource:
            resource_filepath = self.metaDatas[resource.name] if resource.name in self.metaDatas else ""
            if os.path.exists(resource_filepath):
                os.remove(resource_filepath)
            self.releaseResource(resource)

    def regist_resource(self, resource, meta_data=None):
        """
        :param resource: resource object ( Texture2D, Mesh, Material ... )
        """
        logger.debug("Register %s." % resource.name)
        notify_new_resource = resource.name not in self.resources
        self.resources[resource.name] = resource
        if meta_data is not None:
            self.metaDatas[resource.name] = meta_data
        if notify_new_resource:
            resource_info = (resource.name, self.resource_type_name)
            self.core_manager.sendResourceInfo(resource_info)

    def release_resource(self, resource):
        if resource:
            if resource.name in self.resources:
                self.resources.pop(resource.name)
            if resource.name in self.metaDatas:
                self.metaDatas.pop(resource.name)

    def is_need_to_convert(self, resource):
        return resource in self.need_to_convert_resources

    def convert_resource(self, resource_filepath, source_filepath):
        """
        Desc : do resource convert, save_simple_format_and_regist resource.
        :param source_filepath:
        """
        pass

    @staticmethod
    def getResourceName(filepath, workPath, make_lower=True):
        resourceName = os.path.splitext(os.path.relpath(filepath, workPath))[0]
        resourceName = resourceName.replace(os.sep, ".")
        return resourceName if make_lower else resourceName

    def load_resource(self, filePath):
        """
        :return: tuple(Resource object, MetaData)
        """
        resource_name = self.getResourceName(filePath, self.resource_path)
        resource = Resource(resource_name)
        meta_data = MetaData(self.resource_version, filePath)
        return resource, meta_data

    def load_simple_format(self, filePath):
        try:
            # Load data (deserialize)
            if is_gz_compressed_file(filePath):
                with gzip.open(filePath, 'rb') as f:
                    load_data = pickle.load(f)
            else:
                # human readable data
                with open(filePath, 'r') as f:
                    load_data = eval(f.read())

            meta_data = MetaData(load_data.get('resource_version'), filePath)
            meta_data.set_source_meta_data(load_data.get('source_filepath', ''), load_data.get('source_modify_time'))
            return load_data.get('resource_data'), meta_data
        except:
            logger.error("file open error : %s" % filePath)
            logger.error(traceback.format_exc())
        return None, None

    def save_simple_format_and_register(self, resource, resource_data, source_filepath=""):
        """
        save to file and register.
        """
        save_filepath = os.path.join(self.resource_path, resource.name) + self.fileExt
        meta_data = self.getMetaData(resource.name, noWarn=True) or MetaData(self.resource_version, save_filepath)
        meta_data.set_source_meta_data(source_filepath)
        logger.info("Save : %s" % save_filepath)
        try:
            # save resource
            save_data = dict(
                resource_version=self.resource_version,
                source_filepath=meta_data.source_filepath,
                source_modify_time=meta_data.source_modify_time,
                resource_data=resource_data
            )
            # store data, serialize
            if self.USE_FILE_COMPRESS_TO_SAVE:
                with gzip.open(save_filepath, 'wb') as f:
                    pickle.dump(save_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                # human readable data
                with open(save_filepath, 'w') as f:
                    pprint.pprint(save_data, f, width=256)
            # refresh meta data because resource file saved.
            meta_data.set_resource_meta_data(save_filepath)
            # register
            self.regist_resource(resource, meta_data)
        except:
            logger.error(traceback.format_exc())

    def getResource(self, resourceName, noWarn=False):
        if resourceName in self.resources:
            return self.resources[resourceName]
        if not noWarn and resourceName:
            logger.error("%s cannot found %s resource." % (self.name, resourceName))
        return None

    def getResourceList(self):
        return list(self.resources.values())

    def getResourceNameList(self):
        return list(self.resources.keys())

    def getResourceAttribute(self, resource_name):
        resource = self.getResource(resource_name)
        if resource:
            return resource.getAttribute()
        return None

    def setResourceAttribute(self, resource_name, attribute_name, attribute_value, attribute_index):
        resource = self.getResource(resource_name)
        if resource:
            resource.setAttribute(attribute_name, attribute_value, attribute_index)

    def getMetaData(self, resource_name, noWarn=False):
        if resource_name in self.metaDatas:
            return self.metaDatas[resource_name]
        if not noWarn:
            logger.error("Not found meta data of %s." % resource_name)
        return None


# ---------------------------#
# CLASS : ShaderLoader
# ---------------------------#
class ShaderLoader(ResourceLoader):
    name = "ShaderLoader"
    resource_dir_name = 'Shaders'
    resource_type_name = 'Shader'
    fileExt = '.glsl'

    def load_resource(self, filePath):
        try:
            shaderName = self.getResourceName(filePath, self.resource_path)
            return Shader(shaderName, filePath), MetaData(self.resource_version, filePath)
        except:
            logger.error(traceback.format_exc())
        return None, None


# -----------------------#
# CLASS : MaterialLoader
# -----------------------#
class MaterialLoader(ResourceLoader):
    name = "MaterialLoader"
    resource_dir_name = 'Materials'
    resource_type_name = 'Material'
    fileExt = '.mat'
    resource_version = 0
    USE_FILE_COMPRESS_TO_SAVE = False

    def generate_material_name(self, shader_name, macros=None):
        if macros:
            keys = sorted(macros.keys())
            add_name = [key + "_" + str(macros[key]) for key in keys]
            return shader_name + "_" + "_".join(add_name)
        return shader_name

    def load_resource(self, filePath):
        material_datas, meta_data = self.load_simple_format(filePath)
        material_name = self.getResourceName(filePath, self.resource_path, make_lower=False)
        material = Material(material_name, material_datas)
        if 'include_files' in material_datas:
            for include_file in material_datas['include_files']:
                if get_modify_time_of_file(include_file) != material_datas['include_files'][include_file]:
                    # will be convert
                    self.need_to_convert_resources.append(material)
        return material, meta_data

    def convert_resource(self, resource_filepath, source_filepath):
        shader_name = self.getResourceName(source_filepath, ResourceManager.instance().shaderLoader.resource_path)
        shader = ResourceManager.instance().getShader(shader_name)
        if shader:
            material_datas, meta_data = self.load_simple_format(resource_filepath)
            if material_datas and meta_data:
                macros = material_datas.get('macros', {})
                # It's will be generate material.
                self.generate_new_material(shader_name, macros)

    def generate_new_material(self, shader_name, macros={}):
        material_name = self.generate_material_name(shader_name, macros)
        logger.info("Generate new material : %s" % material_name)
        shader = ResourceManager.instance().shaderLoader.getResource(shader_name)
        shader_meta_data = ResourceManager.instance().shaderLoader.getMetaData(shader_name)
        if shader:
            vertex_shader_code = shader.get_vertex_shader_code(macros)
            fragment_shader_code = shader.get_fragment_shader_code(macros)
            material_components = shader.parsing_material_components(vertex_shader_code, fragment_shader_code)

            include_files = {}
            for include_file in shader.include_files:
                include_files[include_file] = get_modify_time_of_file(include_file)

            material_datas = dict(
                vertex_shader_code=vertex_shader_code,
                fragment_shader_code=fragment_shader_code,
                include_files=include_files,
                material_components=material_components,
                macros=macros
            )
            # create material
            material = Material(material_name, material_datas)
            if material and material.valid:
                # write material to file, and regist to resource manager
                if hasattr(shader_meta_data, "resource_filepath"):
                    source_filepath = shader_meta_data.resource_filepath
                else:
                    source_filepath = ""
                self.save_simple_format_and_register(material, material_datas, source_filepath)
            return material
        return None

    def getMaterial(self, shader_name, macros={}):
        material_name = self.generate_material_name(shader_name, macros)
        material = self.getResource(material_name, noWarn=True)
        if material:
            return material
        else:
            material = self.generate_new_material(shader_name, macros)
            if material:
                return material
        logger.error("%s cannot found %s resource." % (self.name, material_name))
        return None


# -----------------------#
# CLASS : MaterialInstanceLoader
# -----------------------#
class MaterialInstanceLoader(ResourceLoader):
    name = "MaterialInstanceLoader"
    resource_dir_name = 'MaterialInstances'
    resource_type_name = 'MaterialInstance'
    fileExt = '.matinst'

    def load_resource(self, filePath):
        material_instance_name = self.getResourceName(filePath, self.resource_path)
        material_instance = MaterialInstance(material_instance_name, filePath)
        meta_data = MetaData(self.resource_version, filePath)
        if material_instance and material_instance.valid:
            return material_instance, meta_data
        return None, None


# -----------------------#
# CLASS : MeshLoader
# -----------------------#
class MeshLoader(ResourceLoader):
    name = "MeshLoader"
    resource_version = 0
    resource_dir_name = 'Meshes'
    resource_type_name = 'Mesh'
    fileExt = '.mesh'
    externalFileExt = dict(WaveFront='.obj', Collada='.dae')
    USE_EXTERNAL_RESOURCE = True
    USE_FILE_COMPRESS_TO_SAVE = False

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

    def convert_resource(self, resource_filepath, source_filepath):
        """
        If the resource is newer, save and register the resource.
        """
        file_ext = os.path.splitext(source_filepath)[1]
        if file_ext == self.externalFileExt.get('WaveFront'):
            geometry = OBJ(source_filepath, 1, True)
            geometry_datas = geometry.get_geometry_data()
        elif file_ext == self.externalFileExt.get('Collada'):
            geometry = Collada(source_filepath)
            geometry_datas = geometry.get_geometry_data()
        else:
            return

        logger.info("Convert Resource : %s" % source_filepath)
        if geometry_datas:
            meshName = self.getResourceName(resource_filepath, self.resource_path)
            # create mesh
            mesh = Mesh(meshName, geometry_datas)
            self.save_simple_format_and_register(mesh, geometry_datas, source_filepath)

    def add_resource_to_scene(self, resource_name):
        resource = self.getResource(resource_name)
        if resource:
            return self.scene_manager.createMeshHere(resource)
        return None


# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(ResourceLoader):
    name = "TextureLoader"
    resource_dir_name = 'Textures'
    resource_type_name = 'Texture'
    fileExt = '.texture'
    externalFileExt = dict(GIF=".gif", JPG=".jpg", JPEG=".jpeg", PNG=".png", BMP=".bmp", TGA=".tga", TIF=".tif",
                           TIFF=".tiff", DXT=".dds", KTX=".ktx")
    USE_EXTERNAL_RESOURCE = True

    def load_resource(self, filePath):
        texture_datas, meta_data = self.load_simple_format(filePath)
        texture_name = self.getResourceName(filePath, self.resource_path)
        return CreateTextureFromFile(texture_name, texture_datas), meta_data

    def convert_resource(self, resource_filepath, source_filepath):
        file_ext = os.path.splitext(source_filepath)[1]
        if file_ext not in self.externalFileExt.values():
            return
        try:
            logger.info("Convert Resource : %s" % source_filepath)
            texture_name = self.getResourceName(source_filepath, self.resource_path)
            # create texture
            texture_type = 'Tex2D'
            image = Image.open(source_filepath)
            image_mode = image.mode
            width, height = image.size
            data = image.tobytes("raw", image.mode, 0, -1)
            texture_datas = dict(
                texture_type=texture_type,
                image_mode=image_mode,
                width=width,
                height=height,
                data=data
            )
            texture = CreateTextureFromFile(texture_name, texture_datas)
            self.save_simple_format_and_register(texture, texture_datas, source_filepath)
        except:
            logger.error(traceback.format_exc())


# -----------------------#
# CLASS : SceneLoader
# -----------------------#
class SceneLoader(ResourceLoader):
    name = "SceneLoader"
    resource_dir_name = 'Scenes'
    resource_type_name = 'Scene'
    fileExt = '.scene'
    USE_FILE_COMPRESS_TO_SAVE = False

    def add_resource_to_scene(self, resource_name):
        self.open_resource(resource_name)

    def open_resource(self, resource_name):
        meta_data = self.getMetaData(resource_name)
        if os.path.exists(meta_data.resource_filepath):
            scene_datas, meta_data = self.load_simple_format(meta_data.resource_filepath)
            self.scene_manager.open_scene(resource_name, scene_datas)


# -----------------------#
# CLASS : ScriptLoader
# -----------------------#
class ScriptLoader(ResourceLoader):
    name = "ScriptLoader"
    resource_dir_name = 'Scripts'
    fileExt = '.py'


# -----------------------#
# CLASS : ResourceManager
# -----------------------#
class ResourceManager(Singleton):
    name = "ResourceManager"
    PathResources = 'Resource'
    DefaultFontFile = os.path.join(PathResources, 'Fonts', 'UbuntuFont.ttf')
    DefaultProjectFile = os.path.join(PathResources, "default.project")

    def __init__(self):
        self.root_path = ""
        self.resource_loaders = []
        self.core_manager= None
        self.scene_manager = None
        self.textureLoader = None
        self.shaderLoader = None
        self.materialLoader = None
        self.material_instanceLoader = None
        self.meshLoader = None
        self.sceneLoader = None
        self.scriptLoader = None

    def regist_loader(self, resource_loader_class):
        resource_loader = resource_loader_class(self.core_manager, self.root_path)
        self.resource_loaders.append(resource_loader)
        return resource_loader

    def initialize(self, core_manager, root_path=""):
        self.core_manager = core_manager
        self.scene_manager = core_manager.sceneManager

        self.root_path = root_path or PathResources
        check_directory_and_mkdir(self.root_path)

        # Be careful with the initialization order.
        self.textureLoader = self.regist_loader(TextureLoader)
        self.shaderLoader = self.regist_loader(ShaderLoader)
        self.materialLoader = self.regist_loader(MaterialLoader)
        self.material_instanceLoader = self.regist_loader(MaterialInstanceLoader)
        self.meshLoader = self.regist_loader(MeshLoader)
        self.sceneLoader = self.regist_loader(SceneLoader)
        self.scriptLoader = self.regist_loader(ScriptLoader)

        # initialize
        for resource_loader in self.resource_loaders:
            resource_loader.initialize()

    def close(self):
        pass

    def prepare_project_directory(self, new_project_dir):
        check_directory_and_mkdir(new_project_dir)
        copy_tree(self.PathResources, new_project_dir)

    def get_default_font_file(self):
        return os.path.join(self.root_path, 'Fonts', 'UbuntuFont.ttf')

    def getResourceNameAndTypeList(self):
        """
        :return [(resource name, resource type)]:
        """
        result = []
        for resource_loader in self.resource_loaders:
            result += [(resName, resource_loader.resource_type_name) for resName in
                       resource_loader.getResourceNameList()]
        return

    def setResourceAttribute(self, resource_name, resource_type_name, attribute_name, attribute_value, attribute_index):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            return resource_loader.setResourceAttribute(resource_name, attribute_name, attribute_value, attribute_index)
        return None

    def getResourceAttribute(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            return resource_loader.getResourceAttribute(resource_name)
        return None

    def getResource(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            return resource_loader.getResource(resource_name)
        return None

    def add_resource_to_scene(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            return resource_loader.add_resource_to_scene(resource_name)
        return None

    def find_resource_loader(self, resource_type_name):
        for resource_loader in self.resource_loaders:
            if resource_loader.resource_type_name == resource_type_name:
                return resource_loader
        logger.error("%s is a unknown resource type." % resource_type_name)
        return None

    # FUNCTIONS : Shader

    def getShader(self, shaderName):
        return self.shaderLoader.getResource(shaderName)

    def getShaderNameList(self):
        return self.shaderLoader.getResourceNameList()

    # FUNCTIONS : Material

    def getMaterialNameList(self):
        return self.materialLoader.getResourceNameList()

    def getMaterial(self, shader_name, macros=None):
        return self.materialLoader.getMaterial(shader_name, macros)

    # FUNCTIONS : MaterialInstance

    def getMaterialInstanceNameList(self):
        return self.material_instanceLoader.getResourceNameList()

    def getMaterialInstance(self, name):
        return self.material_instanceLoader.getResource(name)

    def getDefaultMaterialInstance(self):
        return self.material_instanceLoader.getResource('default')

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
