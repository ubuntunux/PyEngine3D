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
from Object import MaterialInstance, Triangle, Quad, Mesh, StaticMesh
from OpenGLContext import CreateTextureFromFile, Shader, Material, Texture2D
from Utilities import Attributes, Singleton, Config, Logger
from Utilities import GetClassName, is_gz_compressed_file, check_directory_and_mkdir, get_modify_time_of_file
from . import Collada, OBJ


# -----------------------#
# CLASS : MetaData
# -----------------------#
class MetaData:
    def __init__(self, resource_version, resource_filepath):
        self.filepath = os.path.splitext(resource_filepath)[0] + ".meta"
        self.resource_version = resource_version
        self.resource_filepath = resource_filepath
        self.resource_modify_time = get_modify_time_of_file(resource_filepath)
        self.source_filepath = ""
        self.source_modify_time = ""
        self.changed = False

        self.load_meta_file()
        self.save_meta_file()

    def set_resource_meta_data(self, resource_filepath, modify_time=None):
        resource_modify_time = modify_time or get_modify_time_of_file(resource_filepath)
        self.changed |= self.resource_filepath != resource_filepath
        self.changed |= self.resource_modify_time != resource_modify_time
        self.resource_filepath = resource_filepath
        self.resource_modify_time = resource_modify_time

        if self.changed:
            self.save_meta_file()

    def set_source_meta_data(self, source_filepath, modify_time=None):
        source_modify_time = modify_time or get_modify_time_of_file(source_filepath)
        self.changed |= self.source_filepath != source_filepath
        self.changed |= self.source_modify_time != source_modify_time
        self.source_filepath = source_filepath
        self.source_modify_time = source_modify_time

        if self.changed:
            self.save_meta_file()

    def load_meta_file(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                load_data = eval(f.read())
                resource_version = load_data.get("resource_version", None)
                resource_filepath = load_data.get("resource_filepath", None)
                resource_modify_time = load_data.get("resource_modify_time", None)
                source_filepath = load_data.get("source_filepath", None)
                source_modify_time = load_data.get("source_modify_time", None)

                self.changed |= self.resource_version != resource_version
                self.changed |= self.resource_filepath != resource_filepath
                self.changed |= self.resource_modify_time != resource_modify_time
                self.changed |= self.source_filepath != source_filepath
                self.changed |= self.source_modify_time != source_modify_time

                if resource_version is not None:
                    self.resource_version = resource_version
                if source_filepath is not None:
                    self.source_filepath = source_filepath
                if source_modify_time is not None:
                    self.source_modify_time = source_modify_time

                if self.changed:
                    self.save_meta_file()

    def save_meta_file(self):
        if (self.changed or not os.path.exists(self.filepath)) and os.path.exists(self.resource_filepath):
            with open(self.filepath, 'w') as f:
                save_data = dict(
                    resource_version=self.resource_version,
                    resource_filepath=self.resource_filepath,
                    resource_modify_time=self.resource_modify_time,
                    source_filepath=self.source_filepath,
                    source_modify_time=self.source_modify_time,
                )
                pprint.pprint(save_data, f)
            self.changed = False

    def delete_meta_file(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)


# -----------------------#
# CLASS : Resource
# -----------------------#
class Resource:
    def __init__(self, resource_name, resource_type_name):
        self.name = resource_name
        self.type_name = resource_type_name
        self.is_loaded = False
        self.data = None
        self.meta_data = None

    def get_resource_info(self):
        return self.name, self.type_name, self.is_loaded

    def set_data(self, data):
        if data:
            self.data = data
            self.is_loaded = True
            ResourceManager.instance().core_manager.sendResourceInfo(self.get_resource_info())

    def clear_data(self):
        self.data = None
        self.is_loaded = False

    def get_data(self):
        if self.data is None:
            # load resource
            ResourceManager.instance().load_resource(self.name, self.type_name)
        return self.data

    def getAttribute(self):
        if self.data:
            return self.data.getAttribute()
        return None

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if self.data:
            self.data.setAttribute(attributeName, attributeValue, attribute_index)


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
    USE_FILE_COMPRESS_TO_SAVE = True

    def __init__(self, core_manager, root_path):
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.sceneManager
        self.resource_path = os.path.join(root_path, self.resource_dir_name)
        check_directory_and_mkdir(self.resource_path)

        self.externalFileList = []
        self.resources = {}
        self.metaDatas = {}

    @staticmethod
    def getResourceName(filepath, workPath, make_lower=True):
        resourceName = os.path.splitext(os.path.relpath(filepath, workPath))[0]
        resourceName = resourceName.replace(os.sep, ".")
        return resourceName if make_lower else resourceName

    def initialize(self):
        logger.info("initialize " + GetClassName(self))

        # collect resource files
        for dirname, dirnames, filenames in os.walk(self.resource_path):
            for filename in filenames:
                fileExt = os.path.splitext(filename)[1]
                if ".*" == self.fileExt or fileExt == self.fileExt:
                    filepath = os.path.join(dirname, filename)
                    resource_name = self.getResourceName(filepath, self.resource_path)
                    resource = Resource(resource_name, self.resource_type_name)
                    meta_data = MetaData(self.resource_version, filepath)
                    self.regist_resource(resource, meta_data)

        # If you use external files, convert the resources.
        if self.externalFileExt:
            # gather external source files
            for dirname, dirnames, filenames in os.walk(self.resource_path):
                for filename in filenames:
                    source_filepath = os.path.join(dirname, filename)
                    file_ext = os.path.splitext(source_filepath)[1]
                    if file_ext in self.externalFileExt.values():
                        self.externalFileList.append(source_filepath)
            # convert external file to rsource file.
            for source_filepath in self.externalFileList:
                resource_name = self.getResourceName(source_filepath, self.resource_path)
                resource = self.getResource(resource_name, noWarn=True)
                meta_data = self.getMetaData(resource_name, noWarn=True)
                # Create the new resource from exterial file.
                if resource is None:
                    logger.info("Create the new resource from %s." % source_filepath)
                    resource = self.create_resource(resource_name)
                    self.convert_resource(resource, source_filepath)
                elif meta_data:
                    # Refresh the resource from external file.
                    source_modify_time = get_modify_time_of_file(source_filepath)
                    if meta_data.resource_version != self.resource_version \
                        or (meta_data.source_filepath == source_filepath \
                            and meta_data.source_modify_time != source_modify_time):
                        self.convert_resource(resource, source_filepath)
                        logger.info("Refresh the new resource from %s." % source_filepath)
            # clear list
            self.externalFileList = []

        # clear gabage meta file
        for dirname, dirnames, filenames in os.walk(self.resource_path):
            for filename in filenames:
                file_ext = os.path.splitext(filename)[1]
                if file_ext == '.meta':
                    filepath = os.path.join(dirname, filename)
                    resource_name = self.getResourceName(filepath, self.resource_path)
                    resource = self.getResource(resource_name, noWarn=True)
                    meta_data = self.getMetaData(resource_name, noWarn=True)
                    if resource is None:
                        if meta_data:
                            meta_data.delete_meta_file()
                            self.metaDatas.pop(resource_name)
                        else:
                            logger.info("Delete the %s." % filepath)
                            os.remove(filepath)

    def get_new_resource_name(self, prefix=""):
        num = 0
        while True:
            new_name = "%s_%d" % (prefix or self.resource_type_name, num)
            if new_name not in self.resources:
                return new_name
            num += 1
        return ''

    def convert_resource(self, resource, source_filepath):
        logger.warn("convert_resource is not implemented in %s." % self.name)

    def getResource(self, resourceName, noWarn=False):
        if resourceName in self.resources:
            return self.resources[resourceName]
        if not noWarn and resourceName:
            logger.error("%s cannot found %s resource." % (self.name, resourceName))
        return None

    def getResourceData(self, resourceName, noWarn=False):
        resource = self.getResource(resourceName, noWarn)
        if resource:
            if not resource.is_loaded:
                self.load_resource(resourceName)
            return resource.data
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

    def create_resource(self, resource_name, resource_data=None):
        if resource_name in self.resources:
            logger.warn('Resource name is duplicated. %s' % resource_name)
            resource_name = self.get_new_resource_name(resource_name)
        resource = Resource(resource_name, self.resource_type_name)
        if resource_data:
            resource.set_data(resource_data)
        filepath = os.path.join(self.resource_path, resource_name) + self.fileExt
        meta_data = MetaData(self.resource_version, filepath)
        self.regist_resource(resource, meta_data)
        return resource

    def regist_resource(self, resource, meta_data=None):
        logger.info("Regist %s : %s" % (self.resource_type_name, resource.name))
        self.resources[resource.name] = resource
        if meta_data is not None:
            self.metaDatas[resource.name] = meta_data
            resource.meta_data = meta_data
        # The new resource registered.
        if resource:
            resource_info = resource.get_resource_info()
            self.core_manager.sendResourceInfo(resource_info)

    def unregist_resource(self, resource):
        if resource:
            if resource.name in self.metaDatas:
                self.metaDatas.pop(resource.name)
            if resource.name in self.resources:
                self.resources.pop(resource.name)
            self.core_manager.notifyDeleteResource(resource.name)

    def open_resource(self, resource_name):
        logger.warn("open_resource is not implemented in %s." % self.name)

    def request_save_resource(self, resource_name):
        logger.warn("request_save_resource is not implemented in %s." % self.name)

    def load_resource(self, resource_name):
        logger.warn("load_resource is not implemented in %s." % self.name)

    def save_resource(self, resource_name, resource_data):
        logger.warn("save_resource is not implemented in %s." % self.name)

    def load_resource_data(self, filePath):
        try:
            # Load data (deserialize)
            if is_gz_compressed_file(filePath):
                with gzip.open(filePath, 'rb') as f:
                    load_data = pickle.load(f)
            else:
                # human readable data
                with open(filePath, 'r') as f:
                    load_data = eval(f.read())
            return load_data
        except:
            logger.error("file open error : %s" % filePath)
        return None

    def save_resource_data(self, resource, save_data, source_filepath=""):
        save_filepath = os.path.join(self.resource_path, resource.name) + self.fileExt
        logger.info("Save : %s" % save_filepath)
        try:
            # store data, serialize
            if self.USE_FILE_COMPRESS_TO_SAVE:
                with gzip.open(save_filepath, 'wb') as f:
                    pickle.dump(save_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                # human readable data
                with open(save_filepath, 'w') as f:
                    pprint.pprint(save_data, f, width=256)
            # refresh meta data because resource file saved.
            resource.meta_data.set_resource_meta_data(save_filepath)
            resource.meta_data.set_source_meta_data(source_filepath)
        except:
            logger.error(traceback.format_exc())

    def delete_resource(self, resource_name):
        resource = self.getResource(resource_name)
        if resource:
            logger.info("Deleted the %s." % resource.name)
            if resource.name in self.metaDatas:
                resource_filepath = self.metaDatas[resource.name].resource_filepath
            else:
                resource_filepath = ""
            if os.path.exists(resource_filepath):
                os.remove(resource_filepath)
            self.unregist_resource(resource)


# ---------------------------#
# CLASS : ShaderLoader
# ---------------------------#
class ShaderLoader(ResourceLoader):
    name = "ShaderLoader"
    resource_dir_name = 'Shaders'
    resource_type_name = 'Shader'
    fileExt = '.glsl'

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        shader = Shader(resource.name, resource.meta_data.resource_filepath)
        resource.set_data(shader)


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

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        meta_data = resource.meta_data
        material_datas = self.load_resource_data(meta_data.resource_filepath)
        material = Material(resource.name, material_datas)
        resource.set_data(material)
        include_files = material_datas.get('include_files', [])
        for include_file in include_files:
            if get_modify_time_of_file(include_file) != include_files[include_file]:
                self.convert_resource(resource, meta_data.source_filepath)

    def convert_resource(self, resource, source_filepath):
        shader_name = self.getResourceName(source_filepath, ResourceManager.instance().shaderLoader.resource_path)
        shader = ResourceManager.instance().getShader(shader_name)
        if shader:
            material_datas = self.load_resource_data(resource.resource_filepath)
            if material_datas:
                macros = material_datas.get('macros', {})
                self.generate_new_material(resource, shader_name, macros)

    def generate_new_material(self, resource, shader_name, macros={}):
        material_name = self.generate_material_name(shader_name, macros)
        logger.info("Generate new material : %s" % material_name)
        shader = self.resource_manager.getShader(shader_name)
        shader_meta_data = self.resource_manager.shaderLoader.getMetaData(shader_name)
        if shader:
            vertex_shader_code = shader.get_vertex_shader_code(macros)
            fragment_shader_code = shader.get_fragment_shader_code(macros)
            uniforms = shader.parsing_uniforms(vertex_shader_code, fragment_shader_code)

            include_files = {}
            for include_file in shader.include_files:
                include_files[include_file] = get_modify_time_of_file(include_file)

            material_datas = dict(
                vertex_shader_code=vertex_shader_code,
                fragment_shader_code=fragment_shader_code,
                include_files=include_files,
                uniforms=uniforms,
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
                self.save_resource_data(resource, material_datas, source_filepath)
                # convert done
                resource.set_data(material)

    def getMaterial(self, shader_name, macros={}):
        material_name = self.generate_material_name(shader_name, macros)
        resource = self.getResource(material_name)
        if resource is None:
            resource = self.create_resource(material_name)
            self.generate_new_material(resource, shader_name, macros)
        if resource:
            return resource.get_data()
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

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        meta_data = resource.meta_data
        material_instance = MaterialInstance(resource.name, meta_data.resource_filepath)
        resource.set_data(material_instance)


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

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        meta_data = resource.meta_data
        texture_datas = self.load_resource_data(meta_data.resource_filepath)
        texture = CreateTextureFromFile(resource.name, texture_datas)
        resource.set_data(texture)

    def convert_resource(self, resource, source_filepath):
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
            resource.set_data(texture)
            self.save_resource_data(resource, texture_datas, source_filepath)
        except:
            logger.error(traceback.format_exc())


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
    USE_FILE_COMPRESS_TO_SAVE = True

    def initialize(self):
        # load and regist resource
        super(MeshLoader, self).initialize()

        # Regist basic meshs
        self.create_resource("Triangle", Triangle())
        self.create_resource("Quad", Quad())

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        mesh_data = self.load_resource_data(resource.meta_data.resource_filepath)
        mesh = Mesh(resource.name, mesh_data)
        resource.set_data(mesh)

    def convert_resource(self, resoure, source_filepath):
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
            # create mesh
            mesh = Mesh(resoure.name, geometry_datas)
            resoure.set_data(mesh)
            self.save_resource_data(resoure, geometry_datas, source_filepath)

    def open_resource(self, resource_name):
        mesh = self.getResourceData(resource_name)
        if mesh:
            self.scene_manager.addMeshHere(mesh)


# -----------------------#
# CLASS : ObjectLoader
# -----------------------#
class ObjectLoader(ResourceLoader):
    name = "ObjectLoader"
    resource_dir_name = 'Objects'
    resource_type_name = 'Object'
    fileExt = '.object'
    USE_FILE_COMPRESS_TO_SAVE = True

    def open_resource(self, resource_name):
        object = self.getResourceData(resource_name)
        if object:
            self.scene_manager.addMeshHere(object)


# -----------------------#
# CLASS : SceneLoader
# -----------------------#
class SceneLoader(ResourceLoader):
    name = "SceneLoader"
    resource_dir_name = 'Scenes'
    resource_type_name = 'Scene'
    fileExt = '.scene'
    USE_FILE_COMPRESS_TO_SAVE = False

    def request_save_resource(self, resource_name):
        if resource_name == self.scene_manager.get_current_scene_name():
            self.scene_manager.save_scene()

    def open_resource(self, resource_name):
        meta_data = self.getMetaData(resource_name)
        if meta_data and os.path.exists(meta_data.resource_filepath):
            scene_datas = self.load_resource_data(meta_data.resource_filepath)
            self.scene_manager.open_scene(resource_name, scene_datas)

    def save_resource(self, resource_name, resource_data):
        resource = self.getResource(resource_name)
        if resource:
            self.save_resource_data(resource, resource_data)


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
        self.core_manager = None
        self.scene_manager = None
        self.textureLoader = None
        self.shaderLoader = None
        self.materialLoader = None
        self.material_instanceLoader = None
        self.meshLoader = None
        self.sceneLoader = None
        self.scriptLoader = None
        self.objectLoader = None

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
        self.objectLoader = self.regist_loader(ObjectLoader)

        # initialize
        for resource_loader in self.resource_loaders:
            resource_loader.initialize()

        logger.info("Resource register done.")

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

    def getResourceData(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            return resource_loader.getResourceData(resource_name)
        return None

    def getMetaData(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            return resource_loader.getMetaData(resource_name)
        return None

    def load_resource(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            resource_loader.load_resource(resource_name)

    def open_resource(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            resource_loader.open_resource(resource_name)

    def request_save_resource(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            resource_loader.request_save_resource(resource_name)

    def delete_resource(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            resource_loader.delete_resource(resource_name)

    def find_resource_loader(self, resource_type_name):
        for resource_loader in self.resource_loaders:
            if resource_loader.resource_type_name == resource_type_name:
                return resource_loader
        logger.error("%s is a unknown resource type." % resource_type_name)
        return None

    # FUNCTIONS : Shader

    def getShader(self, shaderName):
        return self.shaderLoader.getResourceData(shaderName)

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
        return self.material_instanceLoader.getResourceData(name) or self.getDefaultMaterialInstance()

    def getDefaultMaterialInstance(self):
        return self.material_instanceLoader.getResourceData('default')

    # FUNCTIONS : Mesh

    def getMeshNameList(self):
        return self.meshLoader.getResourceNameList()

    def getMesh(self, meshName):
        return self.meshLoader.getResourceData(meshName)

    # FUNCTIONS : Texture

    def getTextureNameList(self):
        return self.textureLoader.getResourceNameList()

    def getTexture(self, textureName):
        return self.textureLoader.getResourceData(textureName)

    # FUNCTIONS : Object

    def getObjectNameList(self):
        return self.objectLoader.getResourceNameList()

    def getObject(self, meshName):
        return self.objectLoader.getResourceData(meshName)

    # FUNCTIONS : Scene

    def getSceneNameList(self):
        return self.sceneLoader.getResourceNameList()

    def getScene(self, SceneName):
        return self.sceneLoader.getResourceData(SceneName)
