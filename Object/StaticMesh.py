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
            self.set_material_instance(material_instance, i)
        self.attributes = Attributes()

    def set_mesh(self, mesh):
        self.mesh = mesh

    def get_save_data(self):
        save_data = dict(
            object_type=GetClassName(self),
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instances=[material_instance.name for material_instance in self.material_instances]
        )
        return save_data

    def get_material_count(self):
        return len(self.material_instances)

    def get_material_instance(self, index):
        return self.material_instances[index] if index < len(self.material_instances) else None

    def set_material_instance(self, material_instance, attribute_index):
        if attribute_index < len(self.material_instances):
            self.material_instances[attribute_index] = material_instance

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

        self.transform = TransformObject(object_data.get('pos', [0, 0, 0]))
        self.transform.setRot(object_data.get('rot', [0, 0, 0]))
        self.transform.setScale(object_data.get('scale', [1, 1, 1]))

        self.geometry_instances = []
        self.attributes = Attributes()

        # replace data from source object
        if self.staticmesh and self.staticmesh.mesh:
            mesh = self.staticmesh.mesh
            material_instances = object_data.get('material_instances', [])
            default_material_instance = CoreManager.instance().resource_manager.getDefaultMaterialInstance()
            for i, geometry in enumerate(mesh.geometries):
                if i < len(material_instances):
                    material_instance = material_instances[i]
                else:
                    material_instance = self.staticmesh.get_material_instance(i) or default_material_instance
                geometry_instance = GeometryInstance(parent_actor=self, geometry=geometry,
                                                     material_instance=material_instance)
                self.geometry_instances.append(geometry_instance)

    def get_save_data(self):
        save_data = dict(
            source_object=self.staticmesh.name if self.staticmesh else '',
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

    def get_material_instance_names(self):
        return [self.geometry_instances[i].get_material_instance().name for i in range(self.get_material_count())]

    def set_material_instance(self, material_instance, index):
        if index < len(self.geometry_instances):
            self.geometry_instances[index].set_material_instance(material_instance)

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        self.attributes.setAttribute('pos', self.transform.pos)
        self.attributes.setAttribute('rot', self.transform.rot)
        self.attributes.setAttribute('scale', self.transform.scale)
        self.attributes.setAttribute('source_object', self.staticmesh.name if self.staticmesh else '')
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
