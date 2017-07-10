import configparser
from collections import OrderedDict
import os
import re
import traceback
import copy

import numpy as np

from Common import logger
from App import CoreManager
from OpenGLContext import CreateUniformBuffer, CreateUniformDataFromString
from Utilities import Attributes


class MaterialInstance:
    def __init__(self, material_instance_name, **data):
        self.valid = False
        logger.info("Load Material Instance : " + material_instance_name)
        self.name = material_instance_name
        self.material = None
        self.macros = OrderedDict()
        self.linked_uniform_map = dict()
        self.linked_material_component_map = dict()
        self.Attributes = Attributes()

        material = data.get('material')

        # get source macro data from material
        if material:
            self.macros = copy.copy(material.macros)
        # overwrite loaded macro data
        macros = data.get('macros', OrderedDict())
        for define_name, define_value in macros.items():
            self.macros[define_name] = define_value
            try:
                self.macros[define_name] = eval(define_value)
            except:
                pass

        # if macro was changed then get a new material.
        if material:
            shader_name = material.shader_name
        else:
            shader_name = data.get('shader_name', 'default')
        material = CoreManager.instance().resource_manager.getMaterial(shader_name, self.macros)

        # link uniform_buffers and uniform_data
        self.set_material(material)

        if self.material:
            # and set the loaded uniform data.
            uniform_datas = data.get('uniform_datas', {})
            for data_name, data_value in uniform_datas.items():
                self.set_uniform_data(data_name, data_value)
        else:
            logger.error("%s material instance has no material." % self.name)
            return

        self.valid = True

    def clear(self):
        self.linked_uniform_map = OrderedDict({})
        self.Attributes.clear()

    def get_save_data(self):
        uniform_datas = {}
        for uniform_name in self.linked_uniform_map:
            uniform_buffer, uniform_data = self.linked_uniform_map[uniform_name]
            if hasattr(uniform_data, 'tolist'):
                uniform_datas[uniform_name] = uniform_data.tolist()
            elif hasattr(uniform_data, 'name'):
                uniform_datas[uniform_name] = uniform_data.name
            else:
                uniform_datas[uniform_name] = uniform_data

        save_data = dict(
            shader_name=self.material.shader_name if self.material else 'default',
            material=self.material.name if self.material else 'default',
            macros=self.macros,
            uniform_datas=uniform_datas,
        )
        return save_data

    def set_material(self, material):
        if material and self.material != material:
            self.material = material

            # link_uniform_buffers
            old_uniform_names = list(self.linked_uniform_map.keys())
            self.linked_material_component_map = dict()
            material_uniform_names = material.uniform_buffers.keys()
            material_component_names = material.material_component_names
            for uniform_name in material_uniform_names:
                if uniform_name in old_uniform_names:
                    old_uniform_names.remove(uniform_name)
                uniform_buffer = material.uniform_buffers[uniform_name]
                if uniform_name not in self.linked_uniform_map:
                    # cannot found uniform data. just set default uniform data.
                    uniform_data = CreateUniformDataFromString(uniform_buffer.uniform_type)
                    if uniform_data is not None:
                        # link between uniform buffer and data.
                        self.linked_uniform_map[uniform_name] = [uniform_buffer, uniform_data]
                    else:
                        logger.error("%s material instance failed to create %s uniform data %s." % (
                            self.name, uniform_name, uniform_data))
                        continue

                if uniform_name in material_component_names:
                    self.linked_material_component_map[uniform_name] = self.linked_uniform_map[uniform_name]
            # Remove the uniform data that is not in Material and Shader.
            for uniform_name in old_uniform_names:
                self.linked_uniform_map.pop(uniform_name)

    def bind(self):
        for uniform_buffer, uniform_data in self.linked_material_component_map.values():
            uniform_buffer.bind_uniform(uniform_data)

    def bind_uniform_data(self, uniform_name, uniform_data, num=1):
        if uniform_name in self.linked_uniform_map:
            self.linked_uniform_map[uniform_name][0].bind_uniform(uniform_data, num)
        else:
            logger.error('%s material instance has no %s uniform variable.' % (self.name, uniform_name))

    def set_uniform_data(self, uniform_name, uniform_data):
        if uniform_name in self.linked_uniform_map:
            uniform_buffer = self.linked_uniform_map[uniform_name][0]
            if uniform_buffer:
                uniform_data = CreateUniformDataFromString(uniform_buffer.uniform_type, uniform_data)
                if uniform_data is not None:
                    self.linked_uniform_map[uniform_name][1] = uniform_data
        else:
            logger.error('%s material instance has no %s uniform variable %s.' % (self.name, uniform_name, uniform_data))

    def get_program(self):
        return self.material.program

    def useProgram(self):
        self.material.useProgram()

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('material', self.material)
        for uniform_buffer, uniform_data in self.linked_material_component_map.values():
            self.Attributes.setAttribute(uniform_buffer.name, uniform_data)
        for key in self.macros:
            self.Attributes.setAttribute(key, self.macros[key])
        return self.Attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if attributeName in self.linked_material_component_map:
            self.set_uniform_data(attributeName, attributeValue)
        elif attributeName in self.macros:
            if self.macros[attributeName] != attributeValue:
                self.macros[attributeName] = attributeValue
                # if macro was changed then get a new material.
                if self.material:
                    material = CoreManager.instance().resource_manager.getMaterial(self.material.shader_name,
                                                                                   self.macros)
                    self.set_material(material)
        return self.Attributes
