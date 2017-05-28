import time, math

import numpy as np

from Common import logger
from Object import TransformObject, Geometry
from Utilities import GetClassName, Attributes
from App import CoreManager


class BaseObject:
    def __init__(self, objName, pos, mesh):
        self.name = objName
        self.selected = False
        self.transform = TransformObject(pos)
        self.geometries = []
        self.mesh = None
        self.set_mesh(mesh)
        self.attributes = Attributes()

    def set_mesh(self, mesh):
        if mesh:
            self.mesh = mesh
            for vertex_buffer in mesh.vertex_buffers:
                material_instance = CoreManager.instance().resource_manager.getDefaultMaterialInstance()
                geometry = Geometry(self, vertex_buffer, material_instance)
                self.geometries.append(geometry)

    def set_material_instance(self, material_instance, index=0):
        if index < len(self.geometries):
            self.geometries[index].set_material_instance(material_instance)

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        self.attributes.setAttribute('pos', self.transform.pos)
        self.attributes.setAttribute('rot', self.transform.rot)
        self.attributes.setAttribute('scale', self.transform.scale)
        self.attributes.setAttribute('mesh', self.mesh)
        material_instances = [geometries.material_instance.name if geometries.material_instance else '' for geometries in
                              self.geometries]
        self.attributes.setAttribute('material_instances', material_instances)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if attributeName == 'pos':
            self.transform.setPos(attributeValue)
        elif attributeName == 'rot':
            self.transform.setRot(attributeValue)
        elif attributeName == 'scale':
            self.transform.setScale(attributeValue)
        elif attributeName == 'mesh':
            mesh = CoreManager.instance().resource_manager.getMesh(attributeValue)
            if mesh and self.mesh != mesh:
                self.set_mesh(mesh)
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

    def bind_object(self):
        pass
