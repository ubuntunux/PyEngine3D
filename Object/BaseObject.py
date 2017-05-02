import time, math

import numpy as np

import ResourceManager
from Object import TransformObject
from Utilities import GetClassName, Attributes
from Core import logger


class BaseObject:
    def __init__(self, objName, pos, mesh):
        self.name = objName
        self.class_name = GetClassName(self)
        self.selected = False
        self.transform = TransformObject(pos)
        self.mesh = mesh
        self.geometry_instances = mesh.get_geometry_instances(self) if mesh else None
        self.material_instance = None
        self.attributes = Attributes()

    def set_material_instance(self, material_instance):
        # Test Code : set geometry material instance
        if material_instance:
            self.material_instance = material_instance
        for geometry_instance in self.geometry_instances:
            geometry_instance.set_material_instance(material_instance)

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        self.attributes.setAttribute('pos', self.transform.pos)
        self.attributes.setAttribute('matrix', self.transform.matrix)
        self.attributes.setAttribute('rot', self.transform.rot)
        self.attributes.setAttribute('scale', self.transform.scale)
        self.attributes.setAttribute('mesh', self.mesh)
        self.attributes.setAttribute('material_instance', self.material_instance)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue):
        if attributeName == 'pos':
            self.transform.setPos(attributeValue)
        elif attributeName == 'rot':
            self.transform.setRot(attributeValue)
        elif attributeName == 'scale':
            self.transform.setScale(attributeValue)
        elif attributeName == 'mesh':
            self.mesh = ResourceManager.ResourceManager.instance().getMesh(attributeValue)
        elif attributeName == 'material_instance':
            material_instance = ResourceManager.ResourceManager.instance().getMaterialInstance(attributeValue)
            self.set_material_instance(material_instance)

    def setSelected(self, selected):
        self.selected = selected

    def update(self):
        # TEST_CODE
        self.transform.setPitch((time.time() * 0.3) % (math.pi * 2.0))
        self.transform.setYaw((time.time() * 0.4) % (math.pi * 2.0))
        self.transform.setRoll((time.time() * 0.5) % (math.pi * 2.0))

        # update transform
        self.transform.updateTransform()

    def bind_object(self):
        pass
