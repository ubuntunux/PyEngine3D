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

from Core import logger, SceneManager, log_level
from Object import Triangle, Quad, Mesh
from OpenGLContext import CreateTextureFromFile, Shader, Material, Texture2D
from Render import MaterialInstance
from Utilities import Singleton, Config, Logger
from Utilities import GetClassName, is_gz_compressed_file, check_directory_and_mkdir, get_modify_time_of_file
from . import *

reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")  # [Variable Type, Variable Name]
reMacro = re.compile('\#(ifdef|ifndef|if|elif|else|endif)\s*(.*)')  # [macro type, expression]


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
    def __init__(self, resource_name, data=None):
        self.name = resource_name
        self.data = data


# -----------------------#
# CLASS : ResourceLoader
# -----------------------#
class ResourceLoader(object):
    name = "ResourceLoader"
    resource_dir_name = 'Fonts'
    resource_version = 0
    fileExt = '.*'
    externalFileExt = {}  # example, { 'WaveFront': '.obj' }
    USE_EXTERNAL_RESOURCE = False
    USE_FILE_COMPRESS_TO_SAVE = False

    def __init__(self, root_path):
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
                fileExt = os.path.splitext(filename)[1].lower()
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
                    file_ext = os.path.splitext(source_filepath)[1].lower()
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

    def create_resource(self):
        """ TODO : create resource file and regist."""
        pass

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
        self.resources[resource.name] = resource
        if meta_data is not None:
            self.metaDatas[resource.name] = meta_data

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
        return resourceName.lower() if make_lower else resourceName

    def load_resource(self, filePath):
        """
        :return: tuple(Resource object, MetaData)
        """
        raise BaseException("You must implement load_resource.")

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
            meta_data.set_source_meta_data(load_data.get('source_filepath'), load_data.get('source_modify_time'))
            return load_data.get('resource_data'), meta_data
        except:
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
class ShaderLoader(ResourceLoader):
    name = "ShaderLoader"
    resource_dir_name = 'Shaders'
    fileExt = '.glsl'

    def load_resource(self, filePath):
        try:
            shaderName = self.getResourceName(filePath, self.resource_path)
            return Shader(shaderName, filePath), MetaData(self.resource_version, filePath)
        except:
            logger.error(traceback.format_exc())
        return None, None

    def close(self):
        for shader in self.resources.values():
            shader.delete()


# -----------------------#
# CLASS : MaterialLoader
# -----------------------#
class MaterialLoader(ResourceLoader):
    name = "MaterialLoader"
    resource_dir_name = 'Materials'
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
            material_components = self.parsing_material_components(vertex_shader_code, fragment_shader_code)

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

    def parsing_material_components(self, vertexShaderCode, fragmentShaderCode):
        material_components = []
        code_list = [vertexShaderCode, fragmentShaderCode]
        for code in code_list:
            depth = 0
            is_in_material_block = False
            code_lines = code.splitlines()
            for code_line in code_lines:
                m = re.search(reMacro, code_line)
                # find macro
                if m is not None:
                    macro_type, macro_value = [group.strip() for group in m.groups()]
                    if macro_type in ('ifdef', 'ifndef', 'if'):
                        # increase depth
                        if is_in_material_block:
                            depth += 1
                        # start material block
                        elif macro_type == 'ifdef' and 'MATERIAL_COMPONENTS' == macro_value.split(" ")[0]:
                            is_in_material_block = True
                            depth = 1
                    elif macro_type == 'endif' and is_in_material_block:
                        depth -= 1
                        if depth == 0:
                            # exit material block
                            is_in_material_block = False
                # gather common code in material component
                elif is_in_material_block:
                    material_components.append(code_line)
        return re.findall(reFindUniform, "\n".join(material_components))


# -----------------------#
# CLASS : MaterialInstanceLoader
# -----------------------#
class MaterialInstanceLoader(ResourceLoader):
    name = "MaterialInstanceLoader"
    resource_dir_name = 'MaterialInstances'
    fileExt = '.matinst'

    def load_resource(self, filePath):
        material_instance_name = self.getResourceName(filePath, self.resource_path)
        material_instance = MaterialInstance(material_instance_name=material_instance_name, filePath=filePath)
        meta_data = MetaData(self.resource_version, filePath)
        if material_instance and material_instance.valid:
            return material_instance, meta_data
        return None, None


# -----------------------#
# CLASS : MeshLoader
# -----------------------#
class MeshLoader(ResourceLoader):
    name = "MeshLoader"
    resource_dir_name = 'Meshes'
    fileExt = '.mesh'
    externalFileExt = dict(WaveFront='.obj', Collada='.dae')
    USE_EXTERNAL_RESOURCE = True

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
        file_ext = os.path.splitext(source_filepath)[1].lower()
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


# -----------------------#
# CLASS : TextureLoader
# -----------------------#
class TextureLoader(ResourceLoader):
    name = "TextureLoader"
    resource_dir_name = 'Textures'
    fileExt = '.texture'
    externalFileExt = dict(GIF=".gif", JPG=".jpg", JPEG=".jpeg", PNG=".png", BMP=".bmp", TGA=".tga", TIF=".tif",
                           TIFF=".tiff", DXT=".dds", KTX=".ktx")
    USE_EXTERNAL_RESOURCE = True

    def load_resource(self, filePath):
        texture_datas, meta_data = self.load_simple_format(filePath)
        texture_name = self.getResourceName(filePath, self.resource_path)
        return CreateTextureFromFile(texture_name, texture_datas), meta_data

    def convert_resource(self, resource_filepath, source_filepath):
        file_ext = os.path.splitext(source_filepath)[1].lower()
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
    fileExt = ['.scene', ]

    def load_resource(self, filePath):
        try:
            scene_name = self.getResourceName(filePath, self.resource_path)
            scene = Resource(scene_name, filePath)
            meta_data = MetaData(self.resource_version, filePath)
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
        self.root_path = ""
        self.textureLoader = None
        self.shaderLoader = None
        self.materialLoader = None
        self.material_instanceLoader = None
        self.meshLoader = None
        self.sceneLoader = None

        self.sceneManager = None

    def initialize(self, root_path=""):
        check_directory_and_mkdir(root_path)

        self.root_path = root_path if root_path else PathResources
        self.textureLoader = TextureLoader(self.root_path)
        self.shaderLoader = ShaderLoader(self.root_path)
        self.materialLoader = MaterialLoader(self.root_path)
        self.material_instanceLoader = MaterialInstanceLoader(self.root_path)
        self.meshLoader = MeshLoader(self.root_path)
        self.sceneLoader = SceneLoader(self.root_path)

        self.sceneManager = None

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

    def new_project(self, new_project_dir):
        check_directory_and_mkdir(new_project_dir)
        copy_tree(PathResources, new_project_dir)

    def get_default_font_file(self):
        return os.path.join(self.root_path, 'Fonts', 'UbuntuFont.ttf')

    def getResourceList(self):
        """
        :return [(resource name, resource type)]:
        """
        result = []
        result += [(resName, GetClassName(self.getShader(resName))) for resName in self.getShaderNameList()]
        result += [(resName, GetClassName(self.getMaterial(resName))) for resName in self.getMaterialNameList()]
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
            resource = self.getMaterial(resName)
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

    def getMaterialNameList(self):
        return self.materialLoader.getResourceNameList()

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
