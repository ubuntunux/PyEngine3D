import os
import traceback

import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import CreateVertexArrayBuffer, VertexArrayBuffer, UniformMatrix4
from PyEngine3D.Utilities import *
from .Skeleton import Skeleton
from .Animation import Animation


def calc_bounding(positions):
    # precompute bind_shape_matrix
    bound_min = Float3(FLOAT32_MAX, FLOAT32_MAX, FLOAT32_MAX)
    bound_max = Float3(FLOAT32_MIN, FLOAT32_MIN, FLOAT32_MIN)
    for position in positions:
        bound_min = np.minimum(bound_min, position)
        bound_max = np.maximum(bound_max, position)
    radius = length(bound_max - bound_min)
    return bound_min, bound_max, radius


class BoundBox:
    def __init__(self, **data):
        self.bound_min = data.get('bound_min', Float3())
        self.bound_max = data.get('bound_max', Float3())
        self.bound_center = (self.bound_min + self.bound_max) * 0.5
        self.radius = data.get('radius', length(self.bound_max - self.bound_min))
        self.update()

    def get_save_data(self):
        save_data = dict(
            bound_min=self.bound_min.copy(),
            bound_max=self.bound_max.copy(),
            bound_center=self.bound_center.copy(),
            radius=self.radius,
        )
        return save_data

    def check_collide(self, pos, scale=1.0):
        return np.all((self.bound_center + (self.bound_min - self.bound_center) * scale) <= pos) and np.all(pos <= (self.bound_center + (self.bound_max - self.bound_center) * scale))

    def clone(self, bound_box):
        self.bound_min[...] = bound_box.bound_min
        self.bound_max[...] = bound_box.bound_max
        self.bound_center[...] = bound_box.bound_center
        self.radius = bound_box.radius

    def update(self):
        self.bound_center = (self.bound_min + self.bound_max) * 0.5
        self.radius = length(self.bound_max - self.bound_min)

    def update_with_matrix(self, bound_box, matrix):
        bound_min = np.dot(np.array([bound_box.bound_min[0], bound_box.bound_min[1], bound_box.bound_min[2], 1.0], dtype=np.float32), matrix)[: 3]
        bound_max = np.dot(np.array([bound_box.bound_max[0], bound_box.bound_max[1], bound_box.bound_max[2], 1.0], dtype=np.float32), matrix)[: 3]
        self.bound_min = np.minimum(bound_min, bound_max)
        self.bound_max = np.maximum(bound_min, bound_max)
        self.bound_center = (self.bound_min + self.bound_max) * 0.5
        self.radius = length(self.bound_max - self.bound_min)


class Geometry:
    def __init__(self, **geometry_data):
        self.name = geometry_data.get('name', '')
        self.index = geometry_data.get('index', 0)
        self.vertex_buffer = geometry_data.get('vertex_buffer')
        self.skeleton = geometry_data.get('skeleton')
        self.bound_box = BoundBox(**geometry_data)

    def draw_elements(self):
        self.vertex_buffer.draw_elements()

    def draw_elements_instanced(self, instance_count, instance_buffer=None, instance_datas=[]):
        self.vertex_buffer.draw_elements_instanced(instance_count, instance_buffer, instance_datas)

    def draw_elements_indirect(self, offset=0):
        self.vertex_buffer.draw_elements_indirect(offset)


class Mesh:
    def __init__(self, mesh_name, **mesh_data):
        logger.info("Load %s : %s" % (GetClassName(self), mesh_name))

        self.name = mesh_name
        self.instance_location_model = -1

        self.bound_box = BoundBox()
        self.bound_box.bound_min = Float3(FLOAT32_MAX, FLOAT32_MAX, FLOAT32_MAX)
        self.bound_box.bound_max = Float3(FLOAT32_MIN, FLOAT32_MIN, FLOAT32_MIN)
        self.bound_box.bound_center = Float3()
        self.bound_box.radius = 0.0

        self.skeletons = []
        for i, skeleton_data in enumerate(mesh_data.get('skeleton_datas', [])):
            skeleton = Skeleton(index=i, **skeleton_data)
            self.skeletons.append(skeleton)

        self.animations = []
        for i, animation_data in enumerate(mesh_data.get('animation_datas', [])):
            if animation_data:
                animation_name = "%s_%s" % (self.name, self.skeletons[i].name)
                animation = Animation(name=animation_name, index=i, skeleton=self.skeletons[i], animation_data=animation_data)
                self.animations.append(animation)
            else:
                self.animations.append(None)

        core_manager = CoreManager().instance()

        self.geometries = []
        self.geometry_datas = []
        for i, geometry_data in enumerate(mesh_data.get('geometry_datas', [])):
            if 'name' not in geometry_data:
                geometry_data['name'] = "%s_%d" % (mesh_name, i)

            # find skeleton of geometry
            skeleton = None
            for skeleton in self.skeletons:
                if skeleton.name == geometry_data.get('skeleton_name', ''):
                    break

            bound_min = geometry_data.get('bound_min')
            bound_max = geometry_data.get('bound_max')
            radius = geometry_data.get('radius')

            if bound_min is None or bound_max is None or radius is None:
                positions = np.array(geometry_data['positions'], dtype=np.float32)
                bound_min, bound_max, radius = calc_bounding(positions)

            self.bound_box.bound_min = np.minimum(self.bound_box.bound_min, bound_min)
            self.bound_box.bound_max = np.maximum(self.bound_box.bound_max, bound_max)
            self.bound_box.radius = max(self.bound_box.radius, radius)

            if core_manager.is_basic_mode:
                vertex_buffer = None
            else:
                vertex_buffer = CreateVertexArrayBuffer(geometry_data)

            # create geometry
            geometry = Geometry(
                name=vertex_buffer.name if vertex_buffer is not None else '',
                index=i,
                vertex_buffer=vertex_buffer,
                skeleton=skeleton,
                bound_min=bound_min,
                bound_max=bound_max,
                radius=radius
            )
            self.geometries.append(geometry)

        self.geometry_datas = []
        self.gl_call_list = []
        if core_manager.is_basic_mode:
            for geometry_data in mesh_data.get('geometry_datas', []):
                indices = geometry_data['indices']
                positions = geometry_data['positions']
                normals = geometry_data['normals']
                texcoords = geometry_data['texcoords']

                self.geometry_datas.append(geometry_data)

                gl_call_list = glGenLists(1)
                glNewList(gl_call_list, GL_COMPILE)
                glBegin(GL_TRIANGLES)
                for index in indices:
                    glTexCoord2f(*texcoords[index])
                    glNormal3f(*normals[index])
                    glVertex3f(*positions[index])
                glEnd()
                glEndList()
                self.gl_call_list.append(gl_call_list)

        self.bound_box.bound_center = (self.bound_box.bound_min + self.bound_box.bound_max) * 0.5

        self.attributes = Attributes()

    def get_attribute(self):
        self.attributes.set_attribute("name", self.name)
        self.attributes.set_attribute("geometries", [geometry.name for geometry in self.geometries])
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        pass

    def get_save_data(self):
        save_data = dict(
            geometry_datas=self.get_geometry_datas()
        )
        return save_data

    def has_bone(self):
        return len(self.skeletons) > 0

    def get_geometry_count(self):
        return len(self.geometries)

    def get_geometry(self, index=0):
        return self.geometries[index] if index < len(self.geometries) else None

    def get_geometry_data(self, index=0):
        return self.geometry_datas[index] if index < len(self.geometry_datas) else None

    def get_gl_call_list(self, index=0):
        return self.gl_call_list[index] if index < len(self.gl_call_list) else None

    def get_geometry_datas(self):
        return self.geometry_datas

    def get_animation(self, index=0):
        return self.animations[index] if index < len(self.animations) else None

    def get_animation_count(self):
        return len(self.animations)


# ------------------------------#
# CLASS : Triangle
# ------------------------------#
class Triangle(Mesh):
    def __init__(self, mesh_name):
        geometry_datas = self.get_geometry_datas()
        Mesh.__init__(self, mesh_name, geometry_datas=geometry_datas)

    def get_geometry_datas(self):
        geometry_data = dict(
            positions=[(-1, -1, 0), (1, -1, 0), (-1, 1, 0)],
            colors=[(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)],
            normals=[(0, 0, 1), (0, 0, 1), (0, 0, 1)],
            texcoords=[(0, 0), (1, 0), (0, 1)],
            indices=[0, 1, 2])
        return [geometry_data, ]


# ------------------------------#
# CLASS : Quad
# ------------------------------#
class Quad(Mesh):
    def __init__(self, mesh_name):
        geometry_datas = self.get_geometry_datas()
        Mesh.__init__(self, mesh_name, geometry_datas=geometry_datas)

    def get_geometry_datas(self):
        geometry_data = dict(
            positions=[(-1, 1, 0), (-1, -1, 0), (1, -1, 0), (1, 1, 0)],
            colors=[(1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1)],
            normals=[(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)],
            texcoords=[(0, 1), (0, 0), (1, 0), (1, 1)],
            indices=[0, 1, 2, 0, 2, 3])

        return [geometry_data, ]


# ------------------------------#
# CLASS : Cube
# ------------------------------#
class Cube(Mesh):
    def __init__(self, mesh_name):
        geometry_datas = self.get_geometry_datas()
        Mesh.__init__(self, mesh_name, geometry_datas=geometry_datas)

    def get_geometry_datas(self):
        geometry_data = dict(
            positions=[
                (-1, 1, 1), (-1, -1, 1), (1, -1, 1), (1, 1, 1),
                (1, 1, 1), (1, -1, 1), (1, -1, -1), (1, 1, -1),
                (1, 1, -1), (1, -1, -1), (-1, -1, -1), (-1, 1, -1),
                (-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1),
                (-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1),
                (-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1)
            ],
            colors=[
                (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1),
                (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1),
                (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1),
                (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1),
                (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1),
                (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1)
            ],
            normals=[
                (0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1),
                (1, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 0),
                (0, 0, -1), (0, 0, -1), (0, 0, -1), (0, 0, -1),
                (-1, 0, 0), (-1, 0, 0), (-1, 0, 0), (-1, 0, 0),
                (0, 1, 0), (0, 1, 0), (0, 1, 0), (0, 1, 0),
                (0, -1, 0), (0, -1, 0), (0, -1, 0), (0, -1, 0)
            ],
            texcoords=[
                (0, 1), (0, 0), (1, 0), (1, 1),
                (0, 1), (0, 0), (1, 0), (1, 1),
                (0, 1), (0, 0), (1, 0), (1, 1),
                (0, 1), (0, 0), (1, 0), (1, 1),
                (0, 1), (0, 0), (1, 0), (1, 1),
                (0, 1), (0, 0), (1, 0), (1, 1)
            ],
            indices=[
                0, 1, 2, 0, 2, 3,
                4, 5, 6, 4, 6, 7,
                8, 9, 10, 8, 10, 11,
                12, 13, 14, 12, 14, 15,
                16, 17, 18, 16, 18, 19,
                20, 21, 22, 20, 22, 23
            ])
        return [geometry_data, ]


# ------------------------------#
# CLASS : Plane
# ------------------------------#
class Plane(Mesh):
    def __init__(self, mesh_name, width=4, height=4, xz_plane=True, mode=GL_TRIANGLES):
        self.width = width
        self.height = height
        self.xz_plane = xz_plane
        self.mode = mode
        geometry_datas = self.get_geometry_datas()
        Mesh.__init__(self, mesh_name, geometry_datas=geometry_datas)

    def get_geometry_datas(self):
        width_points = self.width + 1
        height_points = self.height + 1
        width_step = 1.0 / self.width
        height_step = 1.0 / self.height
        array_count = width_points * height_points
        positions = np.array([[0, 0, 0], ] * array_count, dtype=np.float32)
        colors = np.array([[1, 1, 1, 1], ] * array_count, dtype=np.float32)
        normals = np.array([[0, 1, 0], ] * array_count, dtype=np.float32)
        tangents = np.array([[1, 0, 0], ] * array_count, dtype=np.float32)
        texcoords = np.array([[0, 0], ] * array_count, dtype=np.float32)
        array_index = 0
        for y in range(height_points):
            y *= height_step
            for x in range(width_points):
                x *= width_step
                positions[array_index][:] = [x * 2.0 - 1.0, 0.0, 1.0 - y * 2.0] if self.xz_plane else [x * 2.0 - 1.0, 1.0 - y * 2.0, 0.0]
                texcoords[array_index][:] = [x, 1.0 - y]
                array_index += 1

        array_index = 0
        vertex_count = 4 if self.mode == GL_QUADS else 6
        indices = np.zeros(self.width * self.height * vertex_count, dtype=np.uint32)
        for y in range(self.height):
            for x in range(self.width):
                i = y * width_points + x
                if GL_QUADS == self.mode:
                    indices[array_index: array_index + vertex_count] = [i, i + 1, i + 1 + width_points, i + width_points]
                else:
                    indices[array_index: array_index + vertex_count] = [i, i + 1, i + 1 + width_points, i, i + 1 + width_points, i + width_points]
                array_index += vertex_count

        geometry_data = dict(
            mode=self.mode,
            positions=positions,
            colors=colors,
            normals=normals,
            tangents=tangents,
            texcoords=texcoords,
            indices=indices)

        return [geometry_data, ]


# ------------------------------#
# CLASS : Line
# ------------------------------#
class Line:
    vertex_array_buffer = None

    @staticmethod
    def get_vertex_array_buffer():
        if Line.vertex_array_buffer is None:
            positions = np.array([(0, 0, 0, 1), (0, 1, 0, 1)], dtype=np.float32)
            indices = np.array([0, 1], dtype=np.uint32)
            Line.vertex_array_buffer = VertexArrayBuffer(name='line',
                                                         mode=GL_LINES,
                                                         datas=[positions, ],
                                                         index_data=indices)
        return Line.vertex_array_buffer


# ------------------------------#
# CLASS : Screen Quad
# ------------------------------#
class ScreenQuad:
    vertex_array_buffer = None

    @staticmethod
    def get_vertex_array_buffer():
        if ScreenQuad.vertex_array_buffer is None:
            positions = np.array([(-1, 1, 0, 1), (-1, -1, 0, 1), (1, -1, 0, 1), (1, 1, 0, 1)], dtype=np.float32)
            indices = np.array([0, 1, 2, 3], dtype=np.uint32)
            ScreenQuad.vertex_array_buffer = VertexArrayBuffer(name='screen quad',
                                                               mode=GL_QUADS,
                                                               datas=[positions, ],
                                                               index_data=indices)
        return ScreenQuad.vertex_array_buffer
