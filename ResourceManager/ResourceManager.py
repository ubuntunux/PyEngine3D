import copy
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
import shutil

from PIL import Image
from numpy import array, float32

from Common import logger, log_level
from Object import MaterialInstance, Triangle, Quad, Cube, Mesh, Model
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
        self.old_resource_version = -1
        self.resource_filepath = resource_filepath
        self.resource_modify_time = get_modify_time_of_file(resource_filepath)
        self.source_filepath = ""
        self.source_modify_time = ""
        self.version_updated = False
        self.changed = False

        self.load_meta_file()

    def is_resource_file_changed(self):
        return self.resource_modify_time != get_modify_time_of_file(self.resource_filepath)

    def is_source_file_changed(self):
        return self.source_modify_time != get_modify_time_of_file(self.source_filepath)

    def set_resource_version(self, resource_version, save=True):
        self.changed |= self.resource_version != resource_version
        self.resource_version = resource_version
        if self.changed and save:
            self.save_meta_file()

    def set_resource_meta_data(self, resource_filepath, save=True):
        resource_modify_time = get_modify_time_of_file(resource_filepath)
        self.changed |= self.resource_filepath != resource_filepath
        self.changed |= self.resource_modify_time != resource_modify_time
        self.resource_filepath = resource_filepath
        self.resource_modify_time = resource_modify_time

        if self.changed and save:
            self.save_meta_file()

    def set_source_meta_data(self, source_filepath, save=True):
        source_modify_time = get_modify_time_of_file(source_filepath)
        self.changed |= self.source_filepath != source_filepath
        self.changed |= self.source_modify_time != source_modify_time
        self.source_filepath = source_filepath
        self.source_modify_time = source_modify_time

        if self.changed and save:
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
        else:
            # save meta file
            self.changed = True

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
        self.data = None
        self.meta_data = None

    def get_resource_info(self):
        return self.name, self.type_name, self.data is not None

    def copy_data(self, data):
        if data and self.data:
            if type(self.data) is dict:
                self.data = copy.deepcopy(data)
            else:
                for key in data.__dict__:
                    self.data.__dict__[key] = data.__dict__[key]

    def set_data(self, data):
        if data:
            if self.data is None:
                self.data = data
                ResourceManager.instance().core_manager.sendResourceInfo(self.get_resource_info())
            else:
                self.copy_data(data)

    def clear_data(self):
        self.data = None

    def get_data(self):
        if self.data is None or self.meta_data.is_resource_file_changed():
            ResourceManager.instance().load_resource(self.name, self.type_name)
        return self.data

    def getAttribute(self):
        if self.data and hasattr(self.data, 'getAttribute'):
            return self.data.getAttribute()
        return None

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if self.data and hasattr(self.data, 'setAttribute'):
            self.data.setAttribute(attributeName, attributeValue, attribute_index)


# -----------------------#
# CLASS : ResourceLoader
# -----------------------#
class ResourceLoader(object):
    name = "ResourceLoader"
    resource_dir_name = ''  # example : Fonts, Shaders, Meshes
    resource_version = 0
    resource_type_name = 'None'
    fileExt = '.*'
    external_dir_name = ''  # example : Fonts, Shaders, Meshes
    externalFileExt = {}  # example, { 'WaveFront': '.obj' }
    USE_FILE_COMPRESS_TO_SAVE = True

    def __init__(self, core_manager, root_path):
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.sceneManager
        self.resource_path = os.path.join(root_path, self.resource_dir_name)
        check_directory_and_mkdir(self.resource_path)

        if self.external_dir_name == '':
            self.external_path = self.resource_path
        else:
            self.external_path = os.path.join(root_path, self.external_dir_name)
            check_directory_and_mkdir(self.external_path)

        self.externalFileList = []
        self.resources = {}
        self.metaDatas = {}

    @staticmethod
    def getResourceName(resource_path, filepath, make_lower=True):
        resourceName = os.path.splitext(os.path.relpath(filepath, resource_path))[0]
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
                    resource_name = self.getResourceName(self.resource_path, filepath)
                    resource = Resource(resource_name, self.resource_type_name)
                    meta_data = MetaData(self.resource_version, filepath)
                    self.regist_resource(resource, meta_data)

        # If you use external files, convert the resources.
        if self.externalFileExt:
            # gather external source files
            for dirname, dirnames, filenames in os.walk(self.external_path):
                for filename in filenames:
                    source_filepath = os.path.join(dirname, filename)
                    self.add_convert_source_file(source_filepath)

            # convert external file to rsource file.
            for source_filepath in self.externalFileList:
                resource_name = self.getResourceName(self.external_path, source_filepath)
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
                    resource_name = self.getResourceName(self.resource_path, filepath)
                    resource = self.getResource(resource_name, noWarn=True)
                    meta_data = self.getMetaData(resource_name, noWarn=True)
                    if resource is None:
                        if meta_data:
                            meta_data.delete_meta_file()
                            self.metaDatas.pop(resource_name)
                        else:
                            logger.info("Delete the %s." % filepath)
                            os.remove(filepath)

    def add_convert_source_file(self, source_filepath):
        file_ext = os.path.splitext(source_filepath)[1]
        if file_ext in self.externalFileExt.values() and source_filepath not in self.externalFileList:
            self.externalFileList.append(source_filepath)

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
        return resource.get_data() if resource else None

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
        # rename resource
        if attribute_name == 'name':
            self.rename_resource(resource_name, attribute_value)
        else:
            # set other attributes
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
            # logger.warn('Resource name is duplicated. %s' % resource_name)
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
            self.core_manager.sendResourceInfo(resource.get_resource_info())

    def unregist_resource(self, resource):
        if resource:
            if resource.name in self.metaDatas:
                self.metaDatas.pop(resource.name)
            if resource.name in self.resources:
                self.resources.pop(resource.name)
            self.core_manager.notifyDeleteResource(resource.get_resource_info())

    def rename_resource(self, resource_name, new_name):
        if new_name and resource_name != new_name:
            resource_data = self.getResourceData(resource_name)
            resource = self.create_resource(new_name, resource_data)
            if resource:
                if resource_data and hasattr(resource_data, 'name'):
                    resource_data.name = resource.name
                self.save_resource(resource.name)
                self.delete_resource(resource_name)
                logger.info("rename_resource : %s to %s" % (resource_name, new_name))

    def load_resource(self, resource_name):
        logger.warn("load_resource is not implemented in %s." % self.name)

    def open_resource(self, resource_name):
        logger.warn("open_resource is not implemented in %s." % self.name)

    def duplicate_resource(self, resource_name):
        logger.warn("duplicate_resource is not implemented in %s." % self.name)
        # meta_data = self.getMetaData(resource_name)
        # new_resource = self.create_resource(resource_name)
        # new_meta_data = self.getMetaData(new_resource.name)
        #
        # if os.path.exists(meta_data.source_filepath) and not os.path.exists(new_meta_data.source_filepath):
        #     shutil.copy(meta_data.source_filepath, new_meta_data.source_filepath)
        #     self.load_resource(new_resource.name)
        #     logger.info("duplicate_resource : %s to %s" % (resource_name, new_resource_name))

    def save_resource(self, resource_name):
        resource = self.getResource(resource_name)
        resource_data = self.getResourceData(resource_name)
        if resource and resource_data:
            if hasattr(resource_data, 'get_save_data'):
                save_data = resource_data.get_save_data()
                self.save_resource_data(resource, save_data)
                return
        logger.warn("save_resource is not implemented in %s." % self.name)

    def load_resource_data(self, filePath):
        try:
            if os.path.exists(filePath):
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
            logger.error(traceback.format_exc())
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
            resource.meta_data.set_resource_meta_data(save_filepath, save=False)
            resource.meta_data.set_source_meta_data(source_filepath, save=False)
            resource.meta_data.set_resource_version(self.resource_version, save=False)
            resource.meta_data.save_meta_file()
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
        if resource:
            shader = Shader(resource.name, resource.meta_data.resource_filepath)
            resource.set_data(shader)
            return True
        logger.error('%s failed to load %s' % (self.name, resource_name))
        return False

    def open_resource(self, resource_name):
        shader = self.getResourceData(resource_name)
        if shader:
            self.resource_manager.material_instanceLoader.create_material_instance(resource_name)


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

    def open_resource(self, resource_name):
        material = self.getResourceData(resource_name)
        if material:
            self.resource_manager.material_instanceLoader.create_material_instance(material.shader_name,
                                                                                   material.macros)

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        if resource:
            material_datas = self.load_resource_data(resource.meta_data.resource_filepath)
            if material_datas:
                generate_new_material = False
                if resource.meta_data.source_modify_time != get_modify_time_of_file(resource.meta_data.source_filepath):
                    generate_new_material = True
                include_files = material_datas.get('include_files', [])
                for include_file in include_files:
                    if get_modify_time_of_file(include_file) != include_files[include_file]:
                        generate_new_material = True
                        break
                if generate_new_material:
                    shader_name = material_datas.get('shader_name')
                    macros = material_datas.get('macros', {})
                    self.generate_new_material(resource.name, shader_name, macros)
                else:
                    material = Material(resource.name, material_datas)
                    resource.set_data(material)
                return True
        logger.error('%s failed to load %s' % (self.name, resource_name))
        return False

    def generate_material_name(self, shader_name, macros=None):
        if macros:
            keys = sorted(macros.keys())
            add_name = [key + "_" + str(macros[key]) for key in keys]
            return shader_name + "_" + "_".join(add_name)
        return shader_name

    def generate_new_material(self, material_name, shader_name, macros={}):
        logger.info("Generate new material : %s" % material_name)
        shader = self.resource_manager.getShader(shader_name)
        if shader:
            vertex_shader_code = shader.get_vertex_shader_code(macros)
            fragment_shader_code = shader.get_fragment_shader_code(macros)
            final_macros = shader.parsing_macros(vertex_shader_code, fragment_shader_code)
            uniforms = shader.parsing_uniforms(vertex_shader_code, fragment_shader_code)
            material_components = shader.parsing_material_components(vertex_shader_code, fragment_shader_code)

            include_files = {}
            for include_file in shader.include_files:
                include_files[include_file] = get_modify_time_of_file(include_file)

            material_datas = dict(
                shader_name=shader_name,
                vertex_shader_code=vertex_shader_code,
                fragment_shader_code=fragment_shader_code,
                include_files=include_files,
                uniforms=uniforms,
                material_components=material_components,
                macros=final_macros
            )
            # create material
            material = Material(material_name, material_datas)
            if material and material.valid:
                resource = self.getResource(material_name, noWarn=True)
                if resource is None:
                    resource = self.create_resource(material_name)

                # write material to file, and regist to resource manager
                shader_meta_data = self.resource_manager.shaderLoader.getMetaData(shader_name)
                if shader_meta_data:
                    source_filepath = shader_meta_data.resource_filepath
                else:
                    source_filepath = ""
                self.save_resource_data(resource, material_datas, source_filepath)
                # convert done
                resource.set_data(material)
                return True
        logger.error("Failed to generate_new_material %s." % material_name)
        return False

    def getMaterial(self, shader_name, macros={}):
        if shader_name == '':
            logger.error("Error : Cannot create material. Because material name is empty.")
            return None

        material_name = self.generate_material_name(shader_name, macros)
        material = self.getResourceData(material_name)
        if material is None:
            if self.generate_new_material(material_name, shader_name, macros):
                material = self.getResourceData(material_name, noWarn=True)
        return material


# -----------------------#
# CLASS : MaterialInstanceLoader
# -----------------------#
class MaterialInstanceLoader(ResourceLoader):
    name = "MaterialInstanceLoader"
    resource_dir_name = 'MaterialInstances'
    resource_type_name = 'MaterialInstance'
    fileExt = '.matinst'
    USE_FILE_COMPRESS_TO_SAVE = False

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        if resource:
            meta_data = resource.meta_data
            material_instance_data = self.load_resource_data(meta_data.resource_filepath)
            if material_instance_data:
                material_instance = MaterialInstance(resource.name, **material_instance_data)
                if material_instance.valid:
                    resource.set_data(material_instance)
                return material_instance.valid
        logger.error('%s failed to load %s' % (self.name, resource_name))
        return False

    def create_material_instance(self, shader_name, macros=None):
        if shader_name:
            resource_name = self.get_new_resource_name(shader_name)
            material_instance = MaterialInstance(resource_name, shader_name=shader_name, macros=macros)
            if material_instance.valid:
                resource = self.create_resource(shader_name)
                resource.set_data(material_instance)
                self.save_resource(resource.name)
                return True
        logger.error('Failed to %s material instance.' % shader_name)
        return False

    def getMaterialInstance(self, material_instance_name, macros=None):
        material_instance = self.getResourceData(material_instance_name)
        if material_instance is None:
            if self.create_material_instance(shader_name=material_instance_name, macros=macros):
                material_instance = self.getResourceData(material_instance_name)
            else:
                material_instance = self.getResourceData('default')
        return material_instance


# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(ResourceLoader):
    name = "TextureLoader"
    resource_dir_name = 'Textures'
    resource_type_name = 'Texture'
    external_dir_name = os.path.join('Externals', 'Textures')
    fileExt = '.texture'
    externalFileExt = dict(GIF=".gif", JPG=".jpg", JPEG=".jpeg", PNG=".png", BMP=".bmp", TGA=".tga", TIF=".tif",
                           TIFF=".tiff", DXT=".dds", KTX=".ktx")

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        if resource:
            meta_data = resource.meta_data
            texture_datas = self.load_resource_data(meta_data.resource_filepath)
            if texture_datas:
                texture = CreateTextureFromFile(resource.name, texture_datas)
                resource.set_data(texture)
                return True
        logger.error('%s failed to load %s' % (self.name, resource_name))
        return False

    def convert_resource(self, resource, source_filepath):
        file_ext = os.path.splitext(source_filepath)[1]
        if file_ext not in self.externalFileExt.values():
            return
        try:
            logger.info("Convert Resource : %s" % source_filepath)
            texture_name = self.getResourceName(self.resource_path, source_filepath)
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
    external_dir_name = os.path.join('Externals', 'Meshes')
    USE_FILE_COMPRESS_TO_SAVE = True

    def initialize(self):
        # load and regist resource
        super(MeshLoader, self).initialize()

        # Regist basic meshs
        self.create_resource("Triangle", Triangle())
        self.create_resource("Quad", Quad())
        self.create_resource("Cube", Cube())

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        if resource:
            mesh_data = self.load_resource_data(resource.meta_data.resource_filepath)
            if mesh_data:
                mesh = Mesh(resource.name, **mesh_data)
                resource.set_data(mesh)
                return True
        logger.error('%s failed to load %s' % (self.name, resource_name))
        return False

    def convert_resource(self, resoure, source_filepath):
        file_ext = os.path.splitext(source_filepath)[1]
        if file_ext == self.externalFileExt.get('WaveFront'):
            mesh = OBJ(source_filepath, 1, True)
            mesh_data = mesh.get_mesh_data()
        elif file_ext == self.externalFileExt.get('Collada'):
            mesh = Collada(source_filepath)
            mesh_data = mesh.get_mesh_data()
        else:
            return

        logger.info("Convert Resource : %s" % source_filepath)
        if mesh_data:
            # create mesh
            mesh = Mesh(resoure.name, **mesh_data)
            resoure.set_data(mesh)
            self.save_resource_data(resoure, mesh_data, source_filepath)

    def open_resource(self, resource_name):
        mesh = self.getResourceData(resource_name)
        if mesh:
            self.resource_manager.modelLoader.create_model(mesh)


# -----------------------#
# CLASS : ModelLoader
# -----------------------#
class ModelLoader(ResourceLoader):
    name = "ModelLoader"
    resource_dir_name = 'Models'
    resource_type_name = 'Model'
    fileExt = '.model'
    externalFileExt = dict(Mesh='.mesh')
    USE_FILE_COMPRESS_TO_SAVE = False

    def initialize(self):
        # load and regist resource
        super(ModelLoader, self).initialize()

        # Regist basic meshs
        self.create_resource("Triangle", Model("Triangle", mesh=self.resource_manager.getMesh('Triangle')))
        self.create_resource("Quad", Model("Quad", mesh=self.resource_manager.getMesh('Quad')))

    def create_model(self, mesh):
        resource = self.create_resource(mesh.name)
        model = Model(resource.name, mesh=mesh)
        resource.set_data(model)
        self.save_resource(resource.name)

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        if resource:
            object_data = self.load_resource_data(resource.meta_data.resource_filepath)
            if object_data:
                mesh = self.resource_manager.getMesh(object_data.get('mesh'))
                material_instances = [self.resource_manager.getMaterialInstance(material_instance_name)
                                      for material_instance_name in object_data.get('material_instances', [])]
                obj = Model(resource.name, mesh=mesh, material_instances=material_instances)
                resource.set_data(obj)
                return True
        logger.error('%s failed to load %s' % (self.name, resource_name))
        return False

    def open_resource(self, resource_name):
        model = self.getResourceData(resource_name)
        if model:
            self.scene_manager.addObjectHere(model)


# -----------------------#
# CLASS : SceneLoader
# -----------------------#
class SceneLoader(ResourceLoader):
    name = "SceneLoader"
    resource_dir_name = 'Scenes'
    resource_type_name = 'Scene'
    fileExt = '.scene'
    USE_FILE_COMPRESS_TO_SAVE = False

    def save_resource(self, resource_name):
        resource = self.getResource(resource_name)
        if resource and resource_name == self.scene_manager.get_current_scene_name():
            scene_data = self.scene_manager.get_save_data()
            self.save_resource_data(resource, scene_data)
            # resource.set_data(scene_data)

    def load_resource(self, resource_name):
        resource = self.getResource(resource_name)
        if resource:
            meta_data = self.getMetaData(resource_name)
            if resource and meta_data and os.path.exists(meta_data.resource_filepath):
                scene_datas = self.load_resource_data(meta_data.resource_filepath)
                for object_data in scene_datas.get('static_actors', []):
                    object_data['model'] = self.resource_manager.getModel(object_data.get('model'))
                    for i, material_instance in enumerate(object_data['material_instances']):
                        object_data['material_instances'][i] = self.resource_manager.getMaterialInstance(material_instance)

                self.scene_manager.open_scene(resource_name, scene_datas)
                # resource.set_data(scene_datas)
                return True
        logger.error('%s failed to load %s' % (self.name, resource_name))
        return False

    def open_resource(self, resource_name):
        scene_data = self.getResourceData(resource_name)
        if scene_data:
            self.scene_manager.open_scene(resource_name, scene_data)


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
        self.modelLoader = None

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
        self.modelLoader = self.regist_loader(ModelLoader)

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

    def duplicate_resource(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            resource_loader.duplicate_resource(resource_name)

    def save_resource(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            resource_loader.save_resource(resource_name)

    def rename_resource(self, resource_name, resource_type_name):
        resource_loader = self.find_resource_loader(resource_type_name)
        if resource_loader:
            resource_loader.rename_resource(resource_name)

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

    def getMaterial(self, shader_name, macros={}):
        return self.materialLoader.getMaterial(shader_name, macros)

    # FUNCTIONS : MaterialInstance

    def getMaterialInstanceNameList(self):
        return self.material_instanceLoader.getResourceNameList()

    def getMaterialInstance(self, name):
        return self.material_instanceLoader.getMaterialInstance(name)

    def getDefaultMaterialInstance(self):
        return self.material_instanceLoader.getMaterialInstance('default')

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

    def getModelNameList(self):
        return self.modelLoader.getResourceNameList()

    def getModel(self, modelName):
        return self.modelLoader.getResourceData(modelName)

    # FUNCTIONS : Scene

    def getSceneNameList(self):
        return self.sceneLoader.getResourceNameList()

    def getScene(self, SceneName):
        return self.sceneLoader.getResourceData(SceneName)
