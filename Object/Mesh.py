import os
import traceback

import numpy as np

from Common import logger
from OpenGLContext import CreateVertexArrayBuffer, VertexArrayBuffer, UniformMatrix4
from Utilities import Attributes, GetClassName, normalize, Matrix4
from Object import Skeleton, AnimationNode
from App import CoreManager


class Geometry:
    def __init__(self, parent, vertex_buffer, material_instance, skeleton):
        self.name = vertex_buffer.name
        self.parent = parent
        self.vertex_buffer = vertex_buffer
        self.material_instance = material_instance
        self.skeleton = skeleton

    def get_material_instance(self):
        return self.material_instance

    def get_material_instance_name(self):
        return self.material_instance.name if self.material_instance else ''

    def set_material_instance(self, material_instance):
        self.material_instance = material_instance

    def bindBuffer(self):
        self.vertex_buffer.bindBuffer()

    def draw(self):
        self.vertex_buffer.draw_elements()


class Mesh:
    def __init__(self, mesh_name, **mesh_data):
        logger.info("Load %s : %s" % (GetClassName(self), mesh_name))

        self.name = mesh_name

        self.skeletons = []
        for skeleton_data in mesh_data.get('skeleton_datas', []):
            skeleton = Skeleton(**skeleton_data)
            self.skeletons.append(skeleton)

        self.animation_frame_count = 0
        self.animation_nodes = {}
        for animation_data in mesh_data.get('animation_datas', []):
            animation_node = AnimationNode(**animation_data)
            self.animation_frame_count = max(self.animation_frame_count, len(animation_node.times))
            self.animation_nodes[animation_node.target] = animation_node

        self.geometries = []
        for geometry_data in mesh_data.get('geometry_datas', []):
            vertex_buffer = CreateVertexArrayBuffer(geometry_data)
            if vertex_buffer:
                # find skeleton of geometry
                for skeleton in self.skeletons:
                    if skeleton.name == geometry_data.get('skeleton_name', ''):
                        break
                else:
                    skeleton = None
                # create geometry
                geometry = Geometry(parent=self,
                                    vertex_buffer=vertex_buffer,
                                    material_instance=None,
                                    skeleton=skeleton)
                self.geometries.append(geometry)

        self.attributes = Attributes()

    def get_animation_transform_list(self, skeleton_index=0, frame=0):
        if skeleton_index < len(self.skeletons):
            skeleton = self.skeletons[skeleton_index]
            buffers = np.array(
                [np.dot(skeleton.bones[i].inv_bind_matrix, self.get_animation_transform(bone_name, frame))
                 for i, bone_name in enumerate(skeleton.bone_names)], dtype=np.float32)
            return buffers
        return None

    def get_animation_transform(self, bone_name, frame=0):
        animation_node = self.animation_nodes.get(bone_name)
        return animation_node.get_transform(frame) if animation_node else None

    def get_animation_frame_count(self):
        return self.animation_frame_count

    def get_geometry_count(self):
        return len(self.geometries)

    def getAttribute(self):
        self.attributes.setAttribute("name", self.name)
        self.attributes.setAttribute("geometries", [geometry.name for geometry in self.geometries])
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        pass

    def bindBuffer(self, index=0):
        if index < len(self.geometries):
            self.geometries[index].bindBuffer()

    def draw(self, index=0):
        if index < len(self.geometries):
            self.geometries[index].draw()


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
