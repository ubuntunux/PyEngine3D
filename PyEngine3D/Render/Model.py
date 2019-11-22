import time
import math

import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.Utilities import GetClassName, Attributes
from PyEngine3D.App import CoreManager


class Model:
    def __init__(self, name, **data):
        self.name = name
        self.mesh = None
        self.material_instances = []
        self.set_mesh(data.get('mesh'))

        for i, material_instance in enumerate(data.get('material_instances', [])):
            self.set_material_instance(material_instance, i)

        self.attributes = Attributes()

    def set_mesh(self, mesh):
        if mesh:
            self.mesh = mesh
            default_material_instance = CoreManager.instance().resource_manager.get_default_material_instance(
                skeletal=mesh.has_bone())
            material_instances = [default_material_instance, ] * len(mesh.geometries)
            for i in range(min(len(self.material_instances), len(material_instances))):
                material_instances[i] = self.material_instances[i]
            self.material_instances = material_instances

    def get_save_data(self):
        save_data = dict(
            object_type=GetClassName(self),
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instances=[material_instance.name if material_instance is not None else '' for material_instance in self.material_instances]
        )
        return save_data

    def get_material_count(self):
        return len(self.material_instances)

    def get_material_instance(self, index):
        return self.material_instances[index]

    def get_material_instance_name(self, index):
        material_instance = self.get_material_instance(index)
        return material_instance.name if material_instance else ''

    def get_material_instance_names(self):
        return [self.get_material_instance_name(i) for i in range(self.get_material_count())]

    def set_material_instance(self, material_instance, attribute_index):
        if attribute_index < len(self.material_instances):
            self.material_instances[attribute_index] = material_instance

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        self.attributes.set_attribute('mesh', self.mesh)
        self.attributes.set_attribute('material_instances', self.get_material_instance_names())
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if attribute_name == 'mesh':
            mesh = CoreManager.instance().resource_manager.get_mesh(attribute_value)
            if mesh and self.mesh != mesh:
                self.set_mesh(mesh)
        elif attribute_name == 'material_instances':
            material_instance = CoreManager.instance().resource_manager.get_material_instance(
                attribute_value[attribute_index])
            self.set_material_instance(material_instance, attribute_index)
