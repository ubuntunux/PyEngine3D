import os
import configparser
from collections import OrderedDict
import re
import traceback

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader

import Resource
from Core import logger
from Utilities import Attributes
from Material import *

reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")

TODO : 이거 UniformBuffer로 옮기자.
def get_uniform_class(uniform_type):
    if uniform_type == "float":
        return UniformFloat
    elif uniform_type == "vec2":
        return UniformVector2
    elif uniform_type == "vec3":
        return UniformVector3
    elif uniform_type == "vec4":
        return UniformVector4
    elif uniform_type == "sampler2D":
        return UniformTexture2D
    return None

TODO : 이거 UniformBuffer로 옮기자.
def str_to_uniform_data(value_type, strValue):
    try:
        if value_type == 'Float':
            return np.float32(strValue)
        elif value_type == 'Int':
            return np.int32(strValue)
        elif value_type in ('Vector2', 'Vector3', 'Vector4'):
            vecValue = eval(strValue)
            componentCount = int(value_type[-1])
            if len(vecValue) == componentCount:
                return np.array(vecValue, dtype=np.float32)
            else:
                logger.error(ValueError("%s need %d float numbers." % (value_type, componentCount)))
                raise ValueError
        elif value_type == 'Texture2D':
            return Resource.ResourceManager.instance().getTexture(strValue)
    except ValueError:
        logger.error(traceback.format_exc())
    return None


class Material:
    def __init__(self, material_name, material_template):
        self.loaded = False
        logger.info("Create Material : " + material_name)
        resourceMgr = Resource.ResourceManager.instance()
        self.name = material_name
        self.program = -1
        self.material_template = material_template
        self.uniform_buffers = OrderedDict({})  # Declaration order is important.
        self.Attributes = Attributes()

        # build and link the program
        vs = resourceMgr.getVertexShader("default")
        fs = resourceMgr.getFragmentShader("default")
        self.vertexShader = vs.compile(self.material_template)
        self.fragmentShader = fs.compile(self.material_template)

        if self.vertexShader is None or self.fragmentShader is None:
            logger.error("%s material compile error." % material_name)
            return

        # create program
        self.program = glCreateProgram()
        glAttachShader(self.program, self.vertexShader)
        glAttachShader(self.program, self.fragmentShader)
        glLinkProgram(self.program)
        glDetachShader(self.program, self.vertexShader)
        glDetachShader(self.program, self.fragmentShader)

        # build uniform buffer variable
        uniform_contents = re.findall(reFindUniform, self.material_template)
        for uniform_type, uniform_name in uniform_contents:
            UniformClass = get_uniform_class(uniform_type)
            if UniformClass:
                self.uniform_buffers[uniform_name] = UniformClass(self.program, uniform_name)
        self.loaded = True

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDeleteProgram(self.program)
        glDeleteShader(self.vertexShader)
        glDeleteShader(self.fragmentShader)

    def useProgram(self):
        glUseProgram(self.program)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        return self.Attributes


class MaterialInstance:
    resourceMgr = None

    def __init__(self, material_instance_name, filePath):
        self.loaded = False
        logger.info("Create Material Instance : " + material_instance_name)
        resourceMgr = Resource.ResourceManager.instance()
        self.name = material_instance_name
        self.program = None
        self.material = None
        self.uniform_datas = {}
        self.linked_uniform_list = []  #
        self.activateTextureIndex = GL_TEXTURE0
        self.textureIndex = 0
        self.Attributes = Attributes()

        # open material instance file
        material_inst_file = configparser.ConfigParser()
        material_inst_file.read(filePath)
        logger.info("Load Material Instance : %s" % os.path.split(filePath)[1])

        # get material
        try:
            material_name = material_inst_file.get('Material', 'name')
            self.material = resourceMgr.getMaterial(material_name)
        except:
            logger.error(traceback.format_exc())
            return

        self.program = self.material.program

        # conversion string to uniform variable
        for value_type in material_inst_file.sections():
            if value_type == 'Material':
                continue
            for value_name in material_inst_file[value_type]:
                strValue = material_inst_file.get(value_type, value_name)
                value = str_to_uniform_data(value_type, strValue)
                if value is not None:
                    self.uniform_datas[value_name] = value
                else:
                    logger.error("%s MaterialInstance, %s %s is none." % (self.name, value_type, value_name))

        # link uniform_buffers and uniform_data
        self.link_uniform_buffers()

        self.loaded = True

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        pass

    def link_uniform_buffers(self):
        # Link between uniform_buffer and uniform_datas.
        activateTextureIndex = GL_TEXTURE0
        textureIndex = 0
        self.linked_uniform_list = []
        if self.material:
            buffer_names = self.material.uniform_buffers.keys()
            for buffer_name in buffer_names:
                if buffer_name in self.uniform_datas:
                    uniform_buffer = self.material.uniform_buffers[buffer_name]
                    uniform_data = self.uniform_datas[buffer_name]
                    # Important : set texture binding index
                    if uniform_buffer.__class__ == UniformTexture2D:
                        uniform_buffer.set_texture_index(activateTextureIndex, textureIndex)
                        activateTextureIndex += 1
                        textureIndex += 1
                    # linking
                    self.linked_uniform_list.append((uniform_buffer, uniform_data))
                else:
                    logger.error("%s isn't in material instance.")

    def bind(self):
        for uniform_buffer, uniform_data in self.linked_uniform_list:
            uniform_buffer.bind(uniform_data)

    def getProgram(self):
        return self.material.program

    def useProgram(self):
        glUseProgram(self.material.program)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('material', self.material.name, type(self.material))
        return self.Attributes
