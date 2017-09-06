import time
import math

import numpy as np

from Common import logger
from Object import TransformObject, GeometryInstance, Model
from OpenGLContext import UniformBlock
from Utilities import *
from App import CoreManager


class StaticActor:
    def __init__(self, name, **object_data):
        self.name = name
        self.selected = False
        self.mesh = None
        self.model = None
        self.geometries = []

        # animation
        self.animation_frame = 0.0
        self.animation_buffers = []
        self.prev_animation_buffers = []

        self.attributes = Attributes()

        self.set_model(object_data.get('model'))

        # transform
        self.transform = TransformObject()
        self.transform.setPos(object_data.get('pos', [0, 0, 0]))
        self.transform.setRot(object_data.get('rot', [0, 0, 0]))
        self.transform.setScale(object_data.get('scale', [1, 1, 1]))

    def set_model(self, model):
        self.model = model
        self.mesh = self.model.mesh if self.model else None

        self.animation_buffers = []
        self.prev_animation_buffers = []
        self.geometries = []

        if self.model and self.mesh:
            for i in range(self.mesh.get_geometry_count()):
                geometry_instance = GeometryInstance(self, self.model, self.mesh.get_geometry(i))
                self.geometries.append(geometry_instance)

            for i in range(self.mesh.get_animation_count()):
                if self.mesh.animations[i]:
                    animation_buffer = self.mesh.get_animation_transforms(i, self.animation_frame)
                    self.animation_buffers.append(animation_buffer.copy())
                    self.prev_animation_buffers.append(animation_buffer.copy())

    def get_prev_animation_buffer(self, index):
        return self.prev_animation_buffers[index]

    def get_animation_buffer(self, index):
        return self.animation_buffers[index]

    def get_save_data(self):
        save_data = dict(
            name=self.name,
            model=self.model.name if self.model else '',
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
        self.attributes.setAttribute('model', self.model.name if self.model else '')
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

    def update(self, dt):
        # TEST_CODE
        # self.transform.setPitch((time.time() * 0.3) % (math.pi * 2.0))
        # self.transform.setYaw((time.time() * 0.4) % (math.pi * 2.0))
        # self.transform.setRoll((time.time() * 0.5) % (math.pi * 2.0))

        # update transform
        self.transform.updateTransform()

        # update animation
        if self.mesh:
            for i in range(self.mesh.get_animation_count()):
                if self.mesh.animations[i]:
                    count = self.mesh.get_animation_frame_count(i)
                    if count > 0:
                        self.animation_frame = math.fmod(self.animation_frame + dt * 30.0, self.mesh.get_animation_frame_count(i))
                    else:
                        self.animation_frame = 0.0
                    self.prev_animation_buffers[i][...] = self.animation_buffers[i]
                    self.animation_buffers[i][...] = self.mesh.get_animation_transforms(i, self.animation_frame)
