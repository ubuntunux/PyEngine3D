import configparser
from collections import OrderedDict
import os
import traceback

from Core import logger
from OpenGLContext import CreateUniformData
from Resource import ResourceManager
from Utilities import Attributes


class MaterialInstance:
    resourceMgr = None

    def __init__(self, material_instance_name, filePath):
        self.valid = False
        logger.info("Create Material Instance : " + material_instance_name)
        resourceMgr = ResourceManager.ResourceManager.instance()
        self.name = material_instance_name
        self.material = None
        self.uniform_datas = {}
        self.linked_uniform_map = OrderedDict({})
        self.Attributes = Attributes()

        # open material instance file
        material_inst_file = configparser.ConfigParser()
        material_inst_file.optionxform = lambda option: option  # prevent the key value being lowercase
        material_inst_file.read(filePath)
        logger.info("Load Material Instance : %s" % os.path.split(filePath)[1])

        # Load data - create uniform data from config file
        shader_name = ""
        macros = OrderedDict()
        for data_type in material_inst_file.sections():
            if data_type == 'Shader':
                if material_inst_file.has_option('Shader', 'shader'):
                    shader_name = material_inst_file.get('Shader', 'shader')
            elif data_type == 'Define':
                for data_name in material_inst_file[data_type]:
                    macros[data_name] = material_inst_file.get(data_type, data_name)
            else:
                for data_name in material_inst_file[data_type]:
                    strValue = material_inst_file.get(data_type, data_name)
                    data = CreateUniformData(data_type, strValue)
                    if data is not None:
                        self.uniform_datas[data_name] = data
                    else:
                        logger.error("%s MaterialInstance, %s is None." % (self.name, data_type))
        # link uniform_buffers and uniform_data
        material = resourceMgr.getMaterial(shader_name, macros)
        self.link_uniform_buffers(material)

        if self.material is None:
            logger.error("%s material instance has no material." % self.name)
            return

        self.valid = True

    def clear(self):
        self.linked_uniform_map = OrderedDict({})
        self.Attributes.clear()

    def link_uniform_buffers(self, material):
        if material:
            self.material = material
            self.linked_uniform_map = OrderedDict({})
            uniform_names = material.uniform_buffers.keys()
            for uniform_name in uniform_names:
                uniform_buffer = material.uniform_buffers[uniform_name]
                # find uniform data
                if uniform_name in self.uniform_datas:
                    uniform_data = self.uniform_datas[uniform_name]
                else:
                    # no found uniform data. create and set default uniform data.
                    uniform_data = CreateUniformData(uniform_buffer.data_type)
                    if uniform_data is not None:
                        self.uniform_datas[uniform_name] = uniform_data

                if uniform_data is None:
                    logger.error("Material requires %s data. %s material instance has no %s." % (
                        uniform_name, self.name, uniform_name))

                # link between uniform buffer and data.
                self.linked_uniform_map[uniform_name] = [uniform_buffer, uniform_data]

    def bind_material_instance(self):
        for uniform_buffer, uniform_data in self.linked_uniform_map.values():
            uniform_buffer.bind_uniform(uniform_data)

    def set_uniform_data(self, uniform_name, uniform_data):
        self.linked_uniform_map[uniform_name][1] = uniform_data

    def get_program(self):
        return self.material.program

    def useProgram(self):
        self.material.useProgram()

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('material', self.material)
        for uniform_buffer, uniform_data in self.linked_uniform_map.values():
            self.Attributes.setAttribute(uniform_buffer.name, uniform_data)
        return self.Attributes
