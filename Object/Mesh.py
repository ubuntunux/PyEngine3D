import os
import traceback

import numpy as np

from Common import logger
from OpenGLContext import VertexArrayBuffer, UniformMatrix4
from Utilities import Attributes, GetClassName, normalize, compute_tangent
from App import CoreManager


class Geometry:
    def __init__(self, parent_mesh, parent_object, vertex_buffer, material_instance):
        self.name = vertex_buffer.name
        self.parent_mesh = parent_mesh
        self.parent_object = parent_object
        self.vertex_buffer = vertex_buffer
        self.material_instance = material_instance

    @staticmethod
    def get_instance(geometry, parent_object):
        return Geometry(geometry.parent_mesh, parent_object, geometry.vertex_buffer, geometry.material_instance)

    def set_material_instance(self, material_instance):
        self.material_instance = material_instance

    def bindBuffer(self):
        self.vertex_buffer.bindBuffer()

    def draw(self):
        self.vertex_buffer.draw_elements()


class Mesh:
    def __init__(self, mesh_name, geometry_datas):
        logger.info("Load %s : %s" % (GetClassName(self), mesh_name))

        self.name = mesh_name
        self.vertex_buffers = []
        self.create_vertex_buffers(geometry_datas)
        self.attributes = Attributes()

    def get_geometries(self, parent_object, material_instance):
        geometries = []
        for vertex_buffer in self.vertex_buffers:
            geometries.append(Geometry(parent_mesh=self, parent_object=parent_object, vertex_buffer=vertex_buffer,
                                       material_instance=material_instance))
        return geometries

    def create_vertex_buffers(self, geometry_datas):
        for geometry_index, geometry_data in enumerate(geometry_datas):
            vertex_buffer_name = geometry_data.get('name', "%s_%d" % (self.name, geometry_index))
            logger.info("Load %s geometry." % vertex_buffer_name)

            vertex_count = len(geometry_data.get('positions', []))
            if vertex_count == 0:
                logger.error("%s geometry has no position data." % vertex_buffer_name)
                continue

            positions = np.array(geometry_data['positions'], dtype=np.float32)

            if 'indices' not in geometry_data:
                logger.error("%s geometry has no index data." % vertex_buffer_name)
                continue

            indices = np.array(geometry_data['indices'], dtype=np.uint32)

            bone_indicies = geometry_data.get('bone_indicies', None)
            if bone_indicies:
                if 4 * vertex_count == sum([len(bone_index_list) for bone_index_list in bone_indicies]):
                    bone_indicies = np.array(bone_indicies, dtype=np.float32)
                else:
                    new_bone_indicies = np.array([[0.0, 0.0, 0.0, 0.0]] * vertex_count, dtype=np.float32)
                    for i in range(min(vertex_count, len(bone_indicies))):
                        for j in range(min(4, len(bone_indicies[i]))):
                            new_bone_indicies[i][j] = bone_indicies[i][j]
                    geometry_data['bone_indicies'] = new_bone_indicies.tolist()
                    bone_indicies = new_bone_indicies

            bone_weights = geometry_data.get('bone_weights', None)
            if bone_weights:
                if 4 * vertex_count == sum([len(bone_weight_list) for bone_weight_list in bone_weights]):
                    bone_weights = np.array(bone_weights, dtype=np.float32)
                else:
                    new_bone_weights = np.array([[0.0, 0.0, 0.0, 0.0]] * vertex_count, dtype=np.float32)
                    for i in range(min(vertex_count, len(bone_weights))):
                        for j in range(min(4, len(bone_weights[i]))):
                            new_bone_weights[i][j] = bone_weights[i][j]
                    geometry_data['bone_weights'] = new_bone_weights.tolist()
                    bone_weights = new_bone_weights

            colors = np.array(geometry_data.get('colors', []), dtype=np.float32)
            if len(colors) == 0:
                colors = np.array([[1.0, 1.0, 1.0, 1.0]] * vertex_count, dtype=np.float32)

            texcoords = np.array(geometry_data.get('texcoords', []), dtype=np.float32)
            if len(texcoords) == 0:
                texcoords = np.array([[0.0, 0.0]] * vertex_count, dtype=np.float32)

            normals = np.array(geometry_data.get('normals', []), dtype=np.float32)
            if len(normals) == 0:
                normals = np.array([[0.0, 0.0, 1.0], ] * vertex_count, dtype=np.float32)

            tangents = np.array(geometry_data.get('tangents', []), dtype=np.float32)
            if len(tangents) == 0:
                tangents = compute_tangent(positions, texcoords, normals, indices)
                geometry_data['tangents'] = tangents.tolist()

            if bone_indicies is not None and bone_weights is not None:
                vertexBuffer = VertexArrayBuffer(vertex_buffer_name,
                                                 [positions, colors, normals, tangents, texcoords, bone_indicies,
                                                  bone_weights], indices)
            else:
                vertexBuffer = VertexArrayBuffer(vertex_buffer_name, [positions, colors, normals, tangents, texcoords],
                                                 indices)
            self.vertex_buffers.append(vertexBuffer)

    def getAttribute(self):
        self.attributes.setAttribute("name", self.name)
        self.attributes.setAttribute("geometries", [vertex_buffer.name for vertex_buffer in self.vertex_buffers])
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        pass

    def bindBuffer(self, index=0):
        if index < len(self.vertex_buffers):
            self.vertex_buffers[index].bindBuffer()

    def draw(self, index=0):
        if index < len(self.vertex_buffers):
            self.vertex_buffers[index].draw_elements()



class Triangle(Mesh):
    def __init__(self):
        geometry_data = dict(
            positions=[(-1, -1, 0), (1, -1, 0), (-1, 1, 0)],
            colors=[(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)],
            normals=[(0, 0, 1), (0, 0, 1), (0, 0, 1)],
            texcoords=[(0, 0), (1, 0), (0, 1)],
            indices=[0, 1, 2])
        geometry_datas = [geometry_data, ]
        Mesh.__init__(self, GetClassName(self), geometry_datas)


# ------------------------------#
# CLASS : Quad
# ------------------------------#
class Quad(Mesh):
    def __init__(self):
        geometry_data = dict(
            positions=[(-1, -1, 0), (1, -1, 0), (-1, 1, 0), (1, 1, 0)],
            colors=[(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (1, 1, 0, 1)],
            normals=[(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)],
            texcoords=[(0, 0), (1, 0), (0, 1), (1, 1)],
            indices=[0, 1, 2, 1, 3, 2])
        geometry_datas = [geometry_data, ]
        Mesh.__init__(self, GetClassName(self), geometry_datas)


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
