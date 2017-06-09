import time, math

import numpy as np

from Common import logger
from Object import TransformObject, GeometryInstance
from Utilities import GetClassName, Attributes
from App import CoreManager


class StaticMesh:
    def __init__(self, name, **data):
        self.name = name
        self.mesh = data.get('mesh')
        default_material_instance = CoreManager.instance().resource_manager.getDefaultMaterialInstance()
        self.material_instances = [default_material_instance, ] * self.mesh.get_geometry_count() if self.mesh else 0
        for i, material_instance in enumerate(data.get('material_instances', [])):
            self.material_instances[i] = material_instance
        self.attributes = Attributes()

    def get_save_data(self):
        save_data = dict(
            object_type=GetClassName(self),
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instances=[material_instance.name for material_instance in self.material_instances]
        )
        return save_data

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        self.attributes.setAttribute('mesh', self.mesh)
        material_instances = [material_instance.name for material_instance in self.material_instances]
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


class StaticMeshActor:
    def __init__(self, name, **object_data):
        self.name = name
        self.selected = False
        self.staticmesh = object_data.get('source_object')
        # material instances
        self.material_instances = object_data.get('material_instances', [])
        if self.staticmesh and self.staticmesh.mesh:
            geometry_count = self.staticmesh.mesh.get_geometry_count()
            if len(self.material_instances) < geometry_count:
                default_material_instance = CoreManager.instance().resource_manager.getDefaultMaterialInstance()
                for i in range(geometry_count - len(self.material_instances)):
                    self.material_instances.append(default_material_instance)

        self.transform = TransformObject(object_data.get('pos', [0, 0, 0]))
        self.transform.setRot(object_data.get('rot', [0, 0, 0]))
        self.transform.setScale(object_data.get('scale', [1, 1, 1]))

        self.geometry_instances = []
        self.attributes = Attributes()

        # replace data from source object
        if self.staticmesh:
            mesh = self.staticmesh.mesh
            for i, geometry in enumerate(mesh.geometries):
                geometry_instance = GeometryInstance(parent_actor=self, geometry=geometry,
                                                     material_instance=self.material_instances[i])
                self.geometry_instances.append(geometry_instance)

    def get_save_data(self):
        save_data = dict(
            object_type=GetClassName(self),
            source_object=self.staticmesh.name if self.staticmesh else '',
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
        self.attributes.setAttribute('source_object', self.staticmesh.name if self.staticmesh else '')
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
