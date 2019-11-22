import configparser
from collections import OrderedDict
import os
import re
import traceback
import copy

import numpy as np
from numpy import array, float32
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import CreateUniformBuffer, CreateUniformDataFromString
from PyEngine3D.Utilities import Attributes


class MaterialInstance:
    def __init__(self, material_instance_name, **data):
        self.valid = False
        self.isNeedToSave = False
        logger.info("Load Material Instance : " + material_instance_name)
        self.name = material_instance_name
        self.shader_name = data.get('shader_name', 'default')
        self.material = None
        self.material_name = data.get('material_name', 'default')
        self.macros = copy.copy(data.get('macros', OrderedDict()))
        self.linked_uniform_map = dict()
        self.linked_material_component_map = dict()
        self.show_message = {}
        self.Attributes = Attributes()

        material = data.get('material')

        # link uniform_buffers and uniform_data
        self.set_material(material)

        if self.material:
            # and set the loaded uniform data.
            uniform_datas = data.get('uniform_datas', {})
            for data_name, data_value in uniform_datas.items():
                self.set_uniform_data_from_string(data_name, data_value)
        else:
            logger.error("%s material instance has no material." % self.name)
            return

        self.valid = True

    def clear(self):
        self.linked_uniform_map = OrderedDict({})
        self.Attributes.clear()

    def is_translucent(self):
        return self.material.is_translucent

    def get_save_data(self):
        uniform_datas = {}
        for uniform_name in self.linked_uniform_map:
            uniform_buffer, uniform_data = self.linked_uniform_map[uniform_name]
            if hasattr(uniform_data, 'name'):
                uniform_datas[uniform_name] = uniform_data.name
            else:
                uniform_datas[uniform_name] = uniform_data

        save_data = dict(
            shader_name=self.material.shader_name if self.material else 'default',
            material_name=self.material.name if self.material else 'default',
            macros=self.macros,
            uniform_datas=uniform_datas,
        )
        return save_data

    def set_material(self, material):
        if material and self.material != material:
            self.isNeedToSave = self.material_name != material.name

            self.material = material
            self.material_name = material.name
            self.macros = copy.copy(material.macros)

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
                    if uniform_buffer.default_value is not None:
                        uniform_data = uniform_buffer.default_value
                    else:
                        uniform_data = CreateUniformDataFromString(uniform_buffer.uniform_type)

                    if uniform_data is not None:
                        # link between uniform buffer and data.
                        self.linked_uniform_map[uniform_name] = [uniform_buffer, uniform_data]
                    else:
                        logger.error("%s material instance failed to create %s uniform data %s." % (self.name, uniform_name, uniform_data))
                        continue

                if uniform_name in material_component_names:
                    self.linked_material_component_map[uniform_name] = self.linked_uniform_map[uniform_name]
            # Remove the uniform data that is not in Material and Shader.
            for uniform_name in old_uniform_names:
                self.linked_uniform_map.pop(uniform_name)

    def bind_material_instance(self):
        for uniform_buffer, uniform_data in self.linked_material_component_map.values():
            uniform_buffer.bind_uniform(uniform_data)

    def bind_uniform_data(self, uniform_name, uniform_data, **kwargs):
        uniform = self.linked_uniform_map.get(uniform_name)
        if uniform:
            uniform[0].bind_uniform(uniform_data, **kwargs)
        elif uniform_name not in self.show_message or self.show_message[uniform_name]:
            self.show_message[uniform_name] = False
            logger.warn('%s material instance has no %s uniform variable.' % (self.name, uniform_name))

    def get_uniform_data(self, uniform_name):
        uniform = self.linked_uniform_map.get(uniform_name)
        return uniform[1] if uniform else None

    def set_uniform_data(self, uniform_name, uniform_data):
        uniform = self.linked_uniform_map.get(uniform_name)
        if uniform:
            uniform[1] = uniform_data

    def set_uniform_data_from_string(self, uniform_name, str_uniform_data):
        uniform = self.linked_uniform_map.get(uniform_name)
        if uniform:
            uniform_buffer = uniform[0]
            if uniform_buffer:
                uniform_data = CreateUniformDataFromString(uniform_buffer.uniform_type, str_uniform_data)
                if uniform_data is not None:
                    uniform[1] = uniform_data
                    return True
        logger.warn("%s material instance has no %s uniform variable. It may have been optimized by the compiler..)" % (self.name, uniform_name))

    def get_program(self):
        return self.material.program

    def use_program(self):
        self.material.use_program()

    def get_attribute(self):
        self.Attributes.set_attribute('name', self.name)
        self.Attributes.set_attribute('shader_name', self.shader_name)
        self.Attributes.set_attribute('material_name', self.material_name)
        for uniform_buffer, uniform_data in self.linked_material_component_map.values():
            self.Attributes.set_attribute(uniform_buffer.name, uniform_data)
        for key in self.macros:
            self.Attributes.set_attribute(key, self.macros[key])
        return self.Attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if attribute_name == 'shader_name':
            if attribute_value != self.shader_name:
                material = CoreManager.instance().resource_manager.get_material(attribute_value, self.macros)
                self.set_material(material)
        elif attribute_name in 'material_name':
            if self.material:
                material = CoreManager.instance().resource_manager.get_material(self.material.shader_name)
                self.set_material(material)
        elif attribute_name in self.linked_material_component_map:
            self.set_uniform_data_from_string(attribute_name, attribute_value)
        elif attribute_name in self.macros:
            if self.macros[attribute_name] != attribute_value:
                self.macros[attribute_name] = attribute_value
                material = CoreManager.instance().resource_manager.get_material(self.material.shader_name, self.macros)
                self.set_material(material)
        return self.Attributes
