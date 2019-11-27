from math import *
import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.App.CoreManager import CoreManager
from PyEngine3D.Utilities import *
from . import StaticActor


# ------------------------------ #
# CLASS : Camera
# ------------------------------ #
class Camera(StaticActor):
    def __init__(self, name, scene_manager, **object_data):
        if 'pos' not in object_data:
            object_data['pos'] = [0, 1.0, 0]

        StaticActor.__init__(self, name, **object_data)

        self.scene_manager = scene_manager
        self.postprocess = self.scene_manager.renderer.postprocess

        self.meter_per_unit = object_data.get('meter_per_unit', 1.0)
        self.aspect = object_data.get('aspect', 0.0)
        self.fov = object_data.get('fov', 0.0)
        self.near = object_data.get('near', 0.0)
        self.far = object_data.get('far', 0.0)
        self.move_speed = object_data.get('move_speed', 0.0)
        self.pan_speed = object_data.get('pan_speed', 0.0)
        self.rotation_speed = object_data.get('rotation_speed', 0.005)

        self.half_cone = 0.0  # view frustum cone half radian
        self.frustum_vectors = np.zeros(12, dtype=np.float32).reshape(4, 3)

        self.projection = Matrix4()
        self.projection_jitter = Matrix4()
        self.inv_projection = Matrix4()
        self.inv_projection_jitter = Matrix4()
        self.projection_offset = Float2()

        self.view = Matrix4()
        self.inv_view = Matrix4()
        self.view_origin = Matrix4()
        self.inv_view_origin = Matrix4()
        self.view_projection = Matrix4()
        self.view_projection_jitter = Matrix4()
        self.view_origin_projection = Matrix4()
        self.view_origin_projection_jitter = Matrix4()
        self.inv_view_origin_projection = Matrix4()

        self.prev_view = Matrix4()
        self.inv_prev_view = Matrix4()
        self.prev_view_origin = Matrix4()
        self.inv_prev_view_origin = Matrix4()
        self.prev_view_projection = Matrix4()
        self.prev_view_projection_jitter = Matrix4()
        self.prev_view_origin_projection = Matrix4()
        self.prev_view_origin_projection_jitter = Matrix4()

    def initialize(self):
        config = CoreManager.instance().project_manager.config
        # get properties
        self.fov = config.Camera.fov
        self.near = config.Camera.near
        self.far = config.Camera.far
        self.move_speed = config.Camera.move_speed
        self.pan_speed = config.Camera.pan_speed
        self.rotation_speed = config.Camera.rotation_speed

    def get_save_data(self):
        save_data = StaticActor.get_save_data(self)
        save_data['meter_per_unit'] = 1.0
        save_data['aspect'] = 0.0
        save_data['fov'] = 0.0
        save_data['near'] = 0.0
        save_data['far'] = 0.0
        save_data['move_speed'] = 0.0
        save_data['pan_speed'] = 0.0
        save_data['rotation_speed'] = 0.0
        return save_data

    def write_to_config(self, config):
        config.setValue("Camera", "meter_per_unit", self.meter_per_unit)
        config.setValue("Camera", "aspect", self.aspect)
        config.setValue("Camera", "fov", self.fov)
        config.setValue("Camera", "near", self.near)
        config.setValue("Camera", "far", self.far)
        config.setValue("Camera", "move_speed", self.move_speed)
        config.setValue("Camera", "pan_speed", self.pan_speed)
        config.setValue("Camera", "rotation_speed", self.rotation_speed)

    def get_attribute(self):
        StaticActor.get_attribute(self)
        self.attributes.set_attribute('fov', self.fov)
        self.attributes.set_attribute('near', self.near)
        self.attributes.set_attribute('far', self.far)
        self.attributes.set_attribute('move_speed', self.move_speed)
        self.attributes.set_attribute('pan_speed', self.pan_speed)
        self.attributes.set_attribute('rotation_speed', self.rotation_speed)
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        StaticActor.set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index)
        if hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)
            if "fov" == attribute_name:
                self.update_projection(force_update=True)
            else:
                self.scene_manager.renderer.reset_renderer()

    def update_projection(self, fov=0.0, aspect=0.0, force_update=False):
        need_to_update = False
        if 0.0 < fov != self.fov:
            self.fov = fov
            need_to_update = True

        if 0.0 < aspect != self.aspect:
            self.aspect = aspect
            need_to_update = True

        if force_update or need_to_update:
            self.projection[...] = perspective(self.fov, self.aspect, self.near, self.far)
            self.projection_jitter[...] = self.projection
            self.projection_jitter[2][0] = -self.postprocess.jitter[0]
            self.projection_jitter[2][1] = -self.postprocess.jitter[1]

            self.inv_projection[...] = np.linalg.inv(self.projection)
            self.inv_projection_jitter[...] = np.linalg.inv(self.projection_jitter)

    def update(self, force_update=False):
        updated = self.transform.update_transform(update_inverse_matrix=True, force_update=force_update)

        if updated or force_update:
            self.prev_view = self.transform.prev_inverse_matrix
            self.inv_prev_view = self.transform.prev_matrix
            self.prev_view_origin[...] = self.view_origin
            self.inv_prev_view_origin[...] = self.inv_view_origin

            self.view = self.transform.inverse_matrix
            self.inv_view = self.transform.matrix
            self.view_origin[...] = self.view
            self.view_origin[3, 0:3] = [0.0, 0.0, 0.0]
            self.inv_view_origin[...] = np.transpose(self.view_origin)

        self.prev_view_projection[...] = self.view_projection
        self.prev_view_projection_jitter[...] = self.view_projection_jitter
        self.prev_view_origin_projection[...] = self.view_origin_projection
        self.prev_view_origin_projection_jitter[...] = self.view_origin_projection_jitter

        # Update projection jitter.
        # This part is very important because the w value of the projection matrix 3rd row is ​​-1.0.
        self.projection_jitter[2][0] = -self.postprocess.jitter[0]
        self.projection_jitter[2][1] = -self.postprocess.jitter[1]
        self.inv_projection_jitter[...] = np.linalg.inv(self.projection_jitter)

        self.view_projection[...] = np.dot(self.view, self.projection)
        self.view_projection_jitter[...] = np.dot(self.view, self.projection_jitter)
        self.view_origin_projection[...] = np.dot(self.view_origin, self.projection)
        self.view_origin_projection_jitter[...] = np.dot(self.view_origin, self.projection_jitter)

        self.inv_view_origin_projection[...] = np.dot(self.inv_projection, self.inv_view_origin)

        # update frustum planes
        if updated or force_update:
            frustum_vectors = self.frustum_vectors
            view_projection = self.view_origin_projection

            # Left
            frustum_vectors[0][0] = view_projection[0][3] + view_projection[0][0]
            frustum_vectors[0][1] = view_projection[1][3] + view_projection[1][0]
            frustum_vectors[0][2] = view_projection[2][3] + view_projection[2][0]

            # Right
            frustum_vectors[1][0] = view_projection[0][3] - view_projection[0][0]
            frustum_vectors[1][1] = view_projection[1][3] - view_projection[1][0]
            frustum_vectors[1][2] = view_projection[2][3] - view_projection[2][0]

            # Top
            frustum_vectors[2][0] = view_projection[0][3] - view_projection[0][1]
            frustum_vectors[2][1] = view_projection[1][3] - view_projection[1][1]
            frustum_vectors[2][2] = view_projection[2][3] - view_projection[2][1]

            # Bottom
            frustum_vectors[3][0] = view_projection[0][3] + view_projection[0][1]
            frustum_vectors[3][1] = view_projection[1][3] + view_projection[1][1]
            frustum_vectors[3][2] = view_projection[2][3] + view_projection[2][1]

            for i in range(4):
                frustum_vectors[i][...] = normalize(frustum_vectors[i])

            frustum_vectors[0][...] = -np.cross(self.transform.up, frustum_vectors[0])
            frustum_vectors[1][...] = np.cross(self.transform.up, frustum_vectors[1])
            frustum_vectors[2][...] = np.cross(-self.transform.left, frustum_vectors[2])
            frustum_vectors[3][...] = -np.cross(-self.transform.left, frustum_vectors[3])
