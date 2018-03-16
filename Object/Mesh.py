import os
import traceback

import numpy as np

from Common import logger
from OpenGLContext import CreateVertexArrayBuffer, UniformMatrix4
from Utilities import Attributes, GetClassName, normalize, Matrix4, MATRIX4_IDENTITY
from Object import Skeleton, Animation
from App import CoreManager


class Geometry:
    def __init__(self, **geometry_data):
        self.name = geometry_data.get('name', '')
        self.index = geometry_data.get('index', 0)
        self.vertex_buffer = geometry_data.get('vertex_buffer')
        self.skeleton = geometry_data.get('skeleton')

    def create_instance_buffer(self, instance_name, layout_location, element_data):
        self.vertex_buffer.create_instance_buffer(instance_name, layout_location, element_data)

    def bind_instance_buffer(self, instance_name, instance_data, divisor):
        self.vertex_buffer.bind_instance_buffer(instance_name, instance_data, divisor)

    def bind_vertex_buffer(self):
        self.vertex_buffer.bind_vertex_buffer()

    def draw_elements(self):
        self.vertex_buffer.draw_elements()

    def draw_elements_instanced(self, count):
        self.vertex_buffer.draw_elements_instanced(count)


class Mesh:
    def __init__(self, mesh_name, **mesh_data):
        logger.info("Load %s : %s" % (GetClassName(self), mesh_name))

        self.name = mesh_name
        self.instance_location_model = -1

        self.skeletons = []
        for i, skeleton_data in enumerate(mesh_data.get('skeleton_datas', [])):
            skeleton = Skeleton(index=i, **skeleton_data)
            self.skeletons.append(skeleton)

        self.animations = []
        for i, animation_data in enumerate(mesh_data.get('animation_datas', [])):
            if animation_data:
                animation_name = "%s_%s" % (self.name, self.skeletons[i].name)
                animation = Animation(name=animation_name, index=i, skeleton=self.skeletons[i],
                                      animation_data=animation_data)
                self.animations.append(animation)
            else:
                self.animations.append(None)

        self.geometries = []
        for i, geometry_data in enumerate(mesh_data.get('geometry_datas', [])):
            vertex_buffer = CreateVertexArrayBuffer(geometry_data)
            if vertex_buffer:
                # find skeleton of geometry
                skeleton = None
                for skeleton in self.skeletons:
                    if skeleton.name == geometry_data.get('skeleton_name', ''):
                        break

                # create geometry
                geometry = Geometry(
                    name=vertex_buffer.name,
                    index=i,
                    vertex_buffer=vertex_buffer,
                    skeleton=skeleton
                )
                self.geometries.append(geometry)
        self.attributes = Attributes()

    def has_bone(self):
        return len(self.skeletons) > 0

    def get_geometry(self, index=0):
        return self.geometries[index] if index < len(self.geometries) else None

    def get_geometry_count(self):
        return len(self.geometries)

    def get_animation(self, index=0):
        return self.animations[index] if index < len(self.animations) else None

    def get_animation_count(self):
        return len(self.animations)

    def getAttribute(self):
        self.attributes.setAttribute("name", self.name)
        self.attributes.setAttribute("geometries", [geometry.name for geometry in self.geometries])
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        pass


class Triangle(Mesh):
    def __init__(self):
        geometry_data = dict(
            positions=[(-1, -1, 0), (1, -1, 0), (-1, 1, 0)],
            colors=[(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)],
            normals=[(0, 0, 1), (0, 0, 1), (0, 0, 1)],
            texcoords=[(0, 0), (1, 0), (0, 1)],
            indices=[0, 1, 2])
        geometry_datas = [geometry_data, ]
        Mesh.__init__(self, GetClassName(self), geometry_datas=geometry_datas)


# ------------------------------#
# CLASS : Quad
# ------------------------------#
class Quad(Mesh):
    def __init__(self):
        geometry_data = dict(
            positions=[(-1, 1, 0), (-1, -1, 0), (1, -1, 0), (1, 1, 0)],
            colors=[(1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1)],
            normals=[(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)],
            texcoords=[(0, 1), (0, 0), (1, 0), (1, 1)],
            indices=[0, 1, 2, 0, 2, 3])

        geometry_datas = [geometry_data, ]
        Mesh.__init__(self, GetClassName(self), geometry_datas=geometry_datas)


# ------------------------------#
# CLASS : Cube
# ------------------------------#
class Cube(Mesh):
    def __init__(self):
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
        geometry_datas = [geometry_data, ]
        Mesh.__init__(self, GetClassName(self), geometry_datas=geometry_datas)


# ------------------------------#
# CLASS : Plane
# ------------------------------#
class Plane(Mesh):
    def __init__(self, width=4, height=4, xz_plane=True):
        width_points = width + 1
        height_points = height + 1
        width_step = 1.0 / width
        height_step = 1.0 / height
        array_count = width_points * height_points
        positions = np.zeros(array_count * 3).reshape(array_count, 3)
        colors = np.zeros(array_count * 4).reshape(array_count, 4)
        normals = np.zeros(array_count * 3).reshape(array_count, 3)
        texcoords = np.zeros(array_count * 2).reshape(array_count, 2)
        array_index = 0
        for y in range(height_points):
            y = y * height_step
            for x in range(width_points):
                x = x * width_step
                positions[array_index][:] = \
                    [x * 2.0 - 1.0, 0.0, 1.0 - y * 2.0] if xz_plane else [x * 2.0 - 1.0, 1.0 - y * 2.0, 0.0]
                colors[array_index][:] = [1, 1, 1, 1]
                normals[array_index][:] = [0, 1, 0]
                texcoords[array_index][:] = [x, 1.0 - y]
                array_index += 1

        array_index = 0
        indices = np.zeros(width * height * 6)
        for y in range(height):
            for x in range(width):
                i = y * width_points + x
                indices[array_index: array_index + 6] = [i, i + width_points, i + width_points + 1, i, i + width_points + 1, i + 1]
                array_index += 6

        geometry_data = dict(
            positions=positions,
            colors=colors,
            normals=normals,
            texcoords=texcoords,
            indices=indices)

        geometry_datas = [geometry_data, ]
        Mesh.__init__(self, GetClassName(self), geometry_datas=geometry_datas)


# ------------------------------#
# CLASS : DebugLine
# ------------------------------#
class DebugLine:
    def __init__(self, pos1, pos2, width=2.5, color=(1, 1, 0)):
        self.width = width
        self.pos1 = pos1
        self.pos2 = pos2
        self.color = color

    def draw(self):
        pass
        # glLineWidth(self.width)
        # glColor3f(1, 1, 1)
        # glBegin(GL_LINES)
        # glVertex3f(*self.pos1)
        # glVertex3f(*self.pos2)
        # glEnd()
