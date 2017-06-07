import time, math

import numpy as np

from Common import logger
from Object import TransformObject, Geometry
from Utilities import GetClassName, Attributes
from App import CoreManager


class StaticMesh:
    def __init__(self, name, object_data):
        self.name = name
        self.mesh = None
        self.instances = []
        self.geometries = []
        self.attributes = Attributes()
        self.set_mesh(object_data.get('mesh'))

        material_instances = object_data.get('material_instances', [])
        for i, material_instance in enumerate(material_instances):
            self.set_material_instance(material_instance, i)

    def regist(self, instance_obj):
        if instance_obj not in self.instances:
            self.instances.append(instance_obj)

    def unregist(self, instance_obj):
        if instance_obj in self.instances:
            self.instances.remove(instance_obj)

    def set_mesh(self, mesh):
        self.mesh = mesh
        if mesh:
            material_instance = CoreManager.instance().resource_manager.getDefaultMaterialInstance()
            self.geometries = mesh.get_geometries(self, material_instance)
        else:
            self.geometries = []

    def set_material_instance(self, material_instance, index=0):
        if index < len(self.geometries):
            self.geometries[index].set_material_instance(material_instance)

    def get_material_instances(self):
        return [geometry.material_instance for geometry in self.geometries]

    def get_save_data(self):
        save_data = dict(
            object_type=GetClassName(self),
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instances=[material_instance.name for material_instance in self.get_material_instances()]
        )
        return save_data

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        self.attributes.setAttribute('mesh', self.mesh)
        material_instances = [geometries.material_instance.name if geometries.material_instance else '' for geometries in
                              self.geometries]
        self.attributes.setAttribute('material_instances', material_instances)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if attributeName == 'mesh':
            mesh = CoreManager.instance().resource_manager.getMesh(attributeValue)
            if mesh and self.mesh != mesh:
                self.set_mesh(mesh)
        elif attributeName == 'material_instances':
            material_instance = CoreManager.instance().resource_manager.getMaterialInstance(
                attributeValue[attribute_index])
            self.set_material_instance(material_instance, attribute_index)


class StaticMeshInst:
    def __init__(self, name, object_data):
        self.name = name
        self.selected = False
        self.source_object = object_data.get('source_object')
        self.transform = TransformObject(object_data.get('pos', [0, 0, 0]))
        self.transform.setRot(object_data.get('rot', [0, 0, 0]))
        self.transform.setScale(object_data.get('scale', [1, 1, 1]))

        self.mesh = None
        self.geometries = []
        self.attributes = Attributes()

        # replace data from source object
        if self.source_object:
            self.source_object.regist(self)
            self.mesh = self.source_object.mesh
            self.geometries = [Geometry.get_instance(geometry, self) for geometry in self.source_object.geometries]

    def get_source_name(self):
        return self.source_object.name if self.source_object else ''

    def get_save_data(self):
        save_data = dict(
            object_type=GetClassName(self),
            source_object=self.get_source_name(),
            pos=self.transform.pos.tolist(),
            rot=self.transform.rot.tolist(),
            scale=self.transform.scale.tolist()
        )
        return save_data

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        self.attributes.setAttribute('pos', self.transform.pos)
        self.attributes.setAttribute('rot', self.transform.rot)
        self.attributes.setAttribute('scale', self.transform.scale)
        if self.source_object:
            self.attributes.setAttribute('source_object', self.get_source_name())
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

    def setSelected(self, selected):
        self.selected = selected

    def update(self):
        # TEST_CODE
        # self.transform.setPitch((time.time() * 0.3) % (math.pi * 2.0))
        # self.transform.setYaw((time.time() * 0.4) % (math.pi * 2.0))
        # self.transform.setRoll((time.time() * 0.5) % (math.pi * 2.0))

        # update transform
        self.transform.updateTransform()
