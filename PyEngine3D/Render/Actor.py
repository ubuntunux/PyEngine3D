import math

import numpy as np

from PyEngine3D.Utilities import *


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

        self.instance_pos = RangeVariable(**object_data.get('instance_pos',
                                                            dict(min_value=Float3(-10.0, 0.0, -10.0),
                                                                 max_value=Float3(10.0, 0.0, 10.0))))
        self.instance_rot = RangeVariable(**object_data.get('instance_rot', dict(min_value=FLOAT3_ZERO)))
        self.instance_scale = RangeVariable(**object_data.get('instance_scale', dict(min_value=1.0)))
        self.instance_pos_list = object_data.get('instance_pos_list', [])
        self.instance_rot_list = object_data.get('instance_rot_list', [])
        self.instance_scale_list = object_data.get('instance_scale_list', [])

        self.instance_matrix = None
        self.instance_radius_offset = object_data.get('instance_radius_offset', 0.0)
        self.instance_radius_scale = object_data.get('instance_radius_scale', 1.0)

        self.instance_count = object_data.get('instance_count', 1)
        self.set_instance_count(self.instance_count)

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
            scale=self.transform.scale.tolist(),
            instance_count=self.instance_count,
            instance_pos=self.instance_pos.get_save_data(),
            instance_rot=self.instance_rot.get_save_data(),
            instance_scale=self.instance_scale.get_save_data(),
            instance_pos_list=self.instance_pos_list,
            instance_rot_list=self.instance_rot_list,
            instance_scale_list=self.instance_scale_list,
        )
        return save_data

    def set_instance_count(self, count):
        self.instance_count = count

        if 1 < count:
            self.instance_pos_list = [self.instance_pos.get_uniform() for i in range(count)]
            self.instance_rot_list = [self.instance_rot.get_uniform() for i in range(count)]
            self.instance_scale_list = [self.instance_scale.get_uniform() for i in range(count)]

            self.instance_matrix = np.zeros(count, (np.float32, (4, 4)))

            offset_max = FLOAT32_MIN
            scale_max = FLOAT32_MIN
            self.instance_radius_offset = 0.0
            self.instance_radius_scale = 1.0

            for i in range(count):
                uniform_scale = self.instance_scale_list[i]
                offset_max = max(offset_max, max(np.abs(self.instance_pos_list[i])))
                scale_max = max(scale_max, np.abs(uniform_scale))

                self.instance_matrix[i][...] = MATRIX4_IDENTITY
                matrix_scale(self.instance_matrix[i], uniform_scale, uniform_scale, uniform_scale)
                matrix_rotate(self.instance_matrix[i], *self.instance_rot_list[i])
                matrix_translate(self.instance_matrix[i], *self.instance_pos_list[i])
            self.instance_radius_offset = offset_max
            self.instance_radius_scale = scale_max
        else:
            self.instance_matrix = None

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        self.attributes.set_attribute('pos', self.transform.pos)
        self.attributes.set_attribute('rot', self.transform.rot)
        self.attributes.set_attribute('scale', self.transform.scale)
        self.attributes.set_attribute('model', self.model.name if self.model else '')
        self.attributes.set_attribute('instance_count', self.instance_count)
        self.attributes.set_attribute('instance_pos', self.instance_pos.get_save_data())
        self.attributes.set_attribute('instance_rot', self.instance_rot.get_save_data())
        self.attributes.set_attribute('instance_scale', self.instance_scale.get_save_data())
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        item_info_history = []
        parent_attribute_name = attribute_name
        while parent_info is not None:
            parent_attribute_name = parent_info.attribute_name
            item_info_history.insert(0, parent_info)
            parent_info = parent_info.parent_info

        if 1 < len(item_info_history) or 'instance_scale' == parent_attribute_name:
            attribute = getattr(self, item_info_history[0].attribute_name)
            if attribute is not None and isinstance(attribute, RangeVariable):
                if 'min_value' == attribute_name:
                    attribute.set_range(attribute_value, attribute.value[1])
                elif 'max_value' == attribute_name:
                    attribute.set_range(attribute.value[0], attribute_value)
                self.set_instance_count(self.instance_count)
        else:
            if attribute_name == 'pos':
                self.transform.set_pos(attribute_value)
            elif attribute_name == 'rot':
                self.transform.set_rotation(attribute_value)
            elif attribute_name == 'scale':
                self.transform.set_scale(attribute_value)
            elif attribute_name == 'instance_count':
                self.set_instance_count(attribute_value)
            elif hasattr(self, attribute_name):
                setattr(self, attribute_name, attribute_value)

    def get_mesh(self):
        return self.model.mesh if self.has_mesh else None

    def get_geometries(self):
        return self.model.mesh.geometries if self.has_mesh else None

    def get_material_instance(self, index):
        return self.model.material_instances[index] if self.model else None

    def set_selected(self, selected):
        self.selected = selected

    def update(self, dt):
        self.transform.update_transform()


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
