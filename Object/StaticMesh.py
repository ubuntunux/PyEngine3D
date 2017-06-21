import time, math

import numpy as np

from Common import logger
from Object import TransformObject, GeometryInstance, Model
from Utilities import GetClassName, Attributes, Matrix4
from App import CoreManager


class StaticMeshActor:
    def __init__(self, name, **object_data):
        self.name = name
        self.selected = False
        self.attributes = Attributes()
        self.model = None
        self.geometry_instances = []
        self.set_model(object_data.get('model'))

        self.transform = TransformObject()
        self.transform.setPos(object_data.get('pos', [0, 0, 0]))
        self.transform.setRot(object_data.get('rot', [0, 0, 0]))
        self.transform.setScale(object_data.get('scale', [1, 1, 1]))

        material_instances = object_data.get('material_instances', [])
        for i, material_instance in enumerate(material_instances):
            self.set_material_instance(i, material_instance)

    def set_model(self, model):
        if model and model.mesh:
            self.model = model
            self.geometry_instances = []
            default_material_instance = CoreManager.instance().resource_manager.getDefaultMaterialInstance()
            for i, geometry in enumerate(model.mesh.geometries):
                material_instance = model.get_material_instance(i) or default_material_instance
                geometry_instance = GeometryInstance(parent_actor=self, geometry=geometry,
                                                     material_instance=material_instance)
                self.geometry_instances.append(geometry_instance)

    def get_save_data(self):
        save_data = dict(
            model=self.model.name if self.model else '',
            pos=self.transform.pos.tolist(),
            rot=self.transform.rot.tolist(),
            scale=self.transform.scale.tolist(),
            material_instances=self.get_material_instance_names(),
        )
        return save_data

    def get_material_count(self):
        return len(self.geometry_instances)

    def get_material_instance(self, index):
        return self.geometry_instances[index].get_material_instance()

    def get_material_instance_name(self, index):
        return self.geometry_instances[index].get_material_instance_name()

    def get_material_instance_names(self):
        return [self.geometry_instances[i].get_material_instance_name() for i in range(self.get_material_count())]

    def set_material_instance(self, material_instance, index):
        if index < len(self.geometry_instances):
            self.geometry_instances[index].set_material_instance(material_instance)

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        self.attributes.setAttribute('pos', self.transform.pos)
        self.attributes.setAttribute('rot', self.transform.rot)
        self.attributes.setAttribute('scale', self.transform.scale)
        self.attributes.setAttribute('model', self.model.name if self.model else '')
        self.attributes.setAttribute('material_instances', self.get_material_instance_names())
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if attributeName == 'pos':
            self.transform.setPos(attributeValue)
        elif attributeName == 'rot':
            self.transform.setRot(attributeValue)
        elif attributeName == 'scale':
            self.transform.setScale(attributeValue)
        elif attributeName == 'material_instances':
            material_instance = CoreManager.instance().resource_manager.getMaterialInstance(
                attributeValue[attribute_index])
            self.set_material_instance(material_instance, attribute_index)

    def setSelected(self, selected):
        self.selected = selected

    def update(self):
        # TEST_CODE
        # self.transform.setPitch((time.time() * 0.3) % (math.pi * 2.0))
        # self.transform.setYaw((time.time() * 0.4) % (math.pi * 2.0))
        # self.transform.setRoll((time.time() * 0.5) % (math.pi * 2.0))

        # update transform
        self.transform.updateTransform()
