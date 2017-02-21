import time, math

import numpy as np
from OpenGL.GL import *
from PIL import Image

import Resource
from Resource import *
from Object import TransformObject, Primitive
from Material import MaterialInstance
from Utilities import Attributes


class BaseObject:
    def __init__(self, objName, pos, mesh, material_instance):
        self.name = objName
        self.selected = False
        self.transform = TransformObject(pos)
        self.mesh = mesh
        self.attributes = Attributes()
        self.material_instance = None
        self.setMaterialInstance(material_instance)

    # all below parameters must move to Materal Class.
    def setMaterialInstance(self, material_instance):
        self.material_instance = material_instance

        if self.material_instance:
            self.modelBind = glGetUniformLocation(self.material_instance.program, "model")
            self.mvpBind = glGetUniformLocation(self.material_instance.program, "mvp")

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        self.attributes.setAttribute('pos', self.transform.pos)
        self.attributes.setAttribute('rot', self.transform.rot)
        self.attributes.setAttribute('scale', self.transform.scale)
        self.attributes.setAttribute('mesh', self.mesh.name if self.mesh else "", type(Primitive))
        self.attributes.setAttribute('material_instance', self.material_instance.name if self.material_instance else "", type(MaterialInstance))
        return self.attributes

    def setAttribute(self, attributeName, attributeValue):
        if attributeName == 'pos':
            self.transform.setPos(attributeValue)
        elif attributeName == 'rot':
            self.transform.setRot(attributeValue)
        elif attributeName == 'scale':
            self.transform.setScale(attributeValue)
        elif attributeName == 'mesh':
            self.mesh = Resource.ResourceManager.instance().getMesh(attributeValue)
        elif attributeName == 'material_instance':
            self.material_instance = Resource.ResourceManager.instance().getMaterialInstance(attributeValue)

    def setSelected(self, selected):
        self.selected = selected

    def update(self):
        transform = self.transform
        # TEST_CODE
        transform.setYaw((time.time() * 0.2) % math.pi * 2.0)  # Test Code

        # update transform
        transform.updateTransform()

    def bind(self, vpMatrix):
        # bind uniform variables
        glUniformMatrix4fv(self.modelBind, 1, GL_FALSE, self.transform.matrix)
        glUniformMatrix4fv(self.mvpBind, 1, GL_FALSE, np.dot(self.transform.matrix, vpMatrix))
