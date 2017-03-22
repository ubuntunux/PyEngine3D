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
import Render
from Material import *

reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")


class Material:
    def __init__(self, mat_name, vs_name, fs_name, material_template):
        self.valid = False
        logger.info("%s material is combined : vs(%s), fs(%s)" % (mat_name, vs_name, fs_name))
        resourceMgr = Resource.ResourceManager.instance()
        self.name = mat_name
        self.program = -1
        self.material_template = material_template
        self.uniform_buffers = OrderedDict({})  # Declaration order is important.
        self.Attributes = Attributes()

        # build and link the program
        vs = resourceMgr.getVertexShader(vs_name)
        fs = resourceMgr.getFragmentShader(fs_name)
        self.vertexShader = vs.compile(self.material_template) if vs else None
        self.fragmentShader = fs.compile(self.material_template) if fs else None

        if self.vertexShader is None or self.fragmentShader is None:
            logger.error("%s material compile error." % mat_name)
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
            self.uniform_buffers[uniform_name] = create_uniform_buffer(uniform_type, self.program, uniform_name)
        self.valid = True

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
        self.Attributes.setAttribute('type', type(self))
        return self.Attributes


class MaterialInstance:
    resourceMgr = None

    def __init__(self, material_instance_name, filePath):
        self.valid = False
        logger.info("Create Material Instance : " + material_instance_name)
        resourceMgr = Resource.ResourceManager.instance()
        self.name = material_instance_name
        self.program = None
        self.material = -1
        self.uniform_datas = {}
        self.linked_uniform_map = OrderedDict({})
        self.Attributes = Attributes()

        # open material instance file
        material_inst_file = configparser.ConfigParser()
        material_inst_file.read(filePath)
        logger.info("Load Material Instance : %s" % os.path.split(filePath)[1])

        # Load data - conversion string to uniform variable
        for data_type in material_inst_file.sections():
            # pass [Shader] section
            if data_type == 'Shader':
                continue
            for data_name in material_inst_file[data_type]:
                strValue = material_inst_file.get(data_type, data_name)
                data = create_uniform_data(data_type, strValue)
                # append uniform data
                if data is not None:
                    self.uniform_datas[data_name] = data
                else:
                    logger.error("%s MaterialInstance, %s %s is None." % (self.name, data_type, data_name))

        # get material
        material = None
        if material_inst_file.has_option('Shader', 'material'):
            try:
                mat_name = material_inst_file.get('Shader', 'material')
                vs_name = material_inst_file.get('Shader', 'vertex_shader')
                fs_name = material_inst_file.get('Shader', 'fragment_shader')
                material = resourceMgr.getCombinedMaterial(mat_name, vs_name, fs_name)
                # link uniform_buffers and uniform_data
                self.link_uniform_buffers(material)
            except:
                logger.error(traceback.format_exc())

        # load failed.
        if material is None:
            logger.error("%s material instance has no material." % self.name)
            return

        self.valid = True

    def clear(self):
        self.program = None
        self.material = None
        self.linked_uniform_map = OrderedDict({})
        self.Attributes.clear()

    def link_uniform_buffers(self, material):
        if material:
            self.material = material
            self.program = material.program
            activateTextureIndex = GL_TEXTURE0
            textureIndex = 0
            self.linked_uniform_map = OrderedDict({})
            if self.material:
                uniform_names = self.material.uniform_buffers.keys()
                for uniform_name in uniform_names:
                    uniform_buffer = self.material.uniform_buffers[uniform_name]
                    # find uniform data
                    if uniform_name in self.uniform_datas:
                        uniform_data = self.uniform_datas[uniform_name]
                    else:
                        # no found uniform data. create and set default uniform data.
                        data_type = uniform_buffer.__class__
                        uniform_data = create_uniform_data(data_type)
                        if uniform_data:
                            self.uniform_datas[uniform_name] = uniform_data

                    if uniform_data is None:
                        logger.error("Material requires %s data. %s material instance has no %s." % (
                            uniform_name, self.name, uniform_name))

                    # Important : set texture binding index
                    if uniform_buffer.__class__ == UniformTexture2D:
                        uniform_buffer.set_texture_index(activateTextureIndex, textureIndex)
                        activateTextureIndex += 1
                        textureIndex += 1

                    # link between uniform buffer and data.
                    self.linked_uniform_map[uniform_name] = [uniform_buffer, uniform_data]

    def bind(self):
        for uniform_buffer, uniform_data in self.linked_uniform_map.values():
            uniform_buffer.bind(uniform_data)

    def set_uniform_data(self, uniform_name, uniform_data):
        self.linked_uniform_map[uniform_name][1] = uniform_data

    def getProgram(self):
        return self.program

    def useProgram(self):
        glUseProgram(self.program)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('material', self.material)
        for uniform_buffer, uniform_data in self.linked_uniform_map.values():
            self.Attributes.setAttribute(uniform_buffer.name, uniform_data)

        return self.Attributes
