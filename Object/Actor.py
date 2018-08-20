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
        self.transform.set_pos(object_data.get('pos', [0, 0, 0]))
        self.transform.set_rotation(object_data.get('rot', [0, 0, 0]))
        self.transform.set_scale(object_data.get('scale', [1, 1, 1]))

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

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        self.attributes.set_attribute('pos', self.transform.pos)
        self.attributes.set_attribute('rot', self.transform.rot)
        self.attributes.set_attribute('scale', self.transform.scale)
        self.attributes.set_attribute('model', self.model.name if self.model else '')
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        if attribute_name == 'pos':
            self.transform.set_pos(attribute_value)
        elif attribute_name == 'rot':
            self.transform.set_rotation(attribute_value)
        elif attribute_name == 'scale':
            self.transform.set_scale(attribute_value)

    def get_mesh(self):
        return self.model.mesh if self.has_mesh else None

    def get_geometries(self):
        return self.model.mesh.geometries if self.has_mesh else None

    def get_material_instance(self, index):
        return self.model.material_instances[index] if self.model else None

    def setSelected(self, selected):
        self.selected = selected

    def update(self, dt):
        self.transform.update_transform()


class InstanceStaticActor(StaticActor):
    pass


class SkeletonActor(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)

        self.animation_time = 0.0
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
        self.transform.update_transform()

        # update animation
        if self.has_mesh:
            for i, animation in enumerate(self.model.mesh.animations):
                if animation:
                    frame_count = animation.frame_count
                    if frame_count > 1:
                        self.animation_time = math.fmod(self.animation_time + dt, animation.animation_length)
                        frame = animation.get_time_to_frame(self.animation_time)
                    else:
                        frame = 0.0
                    self.prev_animation_buffers[i][...] = self.animation_buffers[i]
                    self.animation_buffers[i][...] = animation.get_animation_transforms(frame)


class InstanceSkeletonActor(SkeletonActor):
    pass
