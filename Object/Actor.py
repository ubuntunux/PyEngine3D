import time
import math

import numpy as np

from Common import logger
from Object import TransformObject, Model
from OpenGLContext import UniformBlock
from Utilities import *
from App import CoreManager


class StaticActor:
    def __init__(self, name, **object_data):
        self.name = name
        self.selected = False
        self.model = None
        self.has_mesh = False

        # transform
        self.transform = TransformObject()
        self.transform.setPos(object_data.get('pos', [0, 0, 0]))
        self.transform.setRot(object_data.get('rot', [0, 0, 0]))
        self.transform.setScale(object_data.get('scale', [1, 1, 1]))

        self.set_model(object_data.get('model'))

        self.attributes = Attributes()

    def set_model(self, model):
        if model:
            self.model = model
            self.has_mesh = model.mesh is not None

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

    def get_mesh(self):
        return self.model.mesh if self.has_mesh else None

    def get_geometries(self):
        return self.model.mesh.geometries if self.has_mesh else None

    def get_material_instance(self, index):
        return self.model.material_instances[index] if self.model else None

    def setSelected(self, selected):
        self.selected = selected

    def update(self, dt):
        self.transform.updateTransform()


class SkeletonActor(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)

        self.animation_frame = 0.0
        self.animation_buffers = []
        self.prev_animation_buffers = []

        if self.has_mesh:
            for animation in self.model.mesh.animations:
                if animation:
                    animation_buffer = animation.get_animation_transforms(0.0)
                    # just initialize
                    self.animation_buffers.append(animation_buffer.copy())
                    self.prev_animation_buffers.append(animation_buffer.copy())

    def get_prev_animation_buffer(self, index):
        return self.prev_animation_buffers[index]

    def get_animation_buffer(self, index):
        return self.animation_buffers[index]

    def update(self, dt):
        # TEST_CODE
        # self.transform.setPitch((time.time() * 0.3) % (math.pi * 2.0))
        # self.transform.setYaw((time.time() * 0.4) % (math.pi * 2.0))
        # self.transform.setRoll((time.time() * 0.5) % (math.pi * 2.0))

        # update
        self.transform.updateTransform()

        # update animation
        if self.has_mesh:
            for i, animation in enumerate(self.model.mesh.animations):
                if animation:
                    frame_count = animation.frame_count
                    if frame_count > 0:
                        self.animation_frame = math.fmod(self.animation_frame + dt * 30.0, frame_count)
                    else:
                        self.animation_frame = 0.0
                    self.prev_animation_buffers[i][...] = self.animation_buffers[i]
                    self.animation_buffers[i][...] = animation.get_animation_transforms(self.animation_frame)
