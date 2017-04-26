import os
import traceback

import numpy as np

from Core import logger
from OpenGLContext import VertexArrayBuffer
from Utilities import Attributes, GetClassName, normalize, compute_tangent


class Geometry:
    def __init__(self, geometry_data):
        self.valid = False
        self.name = geometry_data['geometry_name'] if 'geometry_name' in geometry_data else ""
        self.vertexBuffer = None

        my_class_name = GetClassName(self)
        logger.info("Create %s : %s" % (my_class_name, self.name))

        if 'indices' in geometry_data:
            indices = np.array(geometry_data['indices'], dtype=np.uint32)
        else:
            logger.error("Create %s %s error. Mesh has no index data." % (my_class_name, self.name))
            return

        if 'positions' in geometry_data:
            positions = np.array(geometry_data['positions'], dtype=np.float32)
            vertex_count = len(positions)
        else:
            logger.error("Create %s %s error. Mesh has no position data." % (my_class_name, self.name))
            return

        if 'colors' in geometry_data and geometry_data['colors']:
            colors = np.array(geometry_data['colors'], dtype=np.float32)
        else:
            colors = np.array([1.0, 1.0, 1.0, 1.0] * vertex_count, dtype=np.float32).reshape(vertex_count, 4)

        if 'texcoords' in geometry_data and geometry_data['texcoords']:
            texcoords = np.array(geometry_data['texcoords'], dtype=np.float32)
        else:
            texcoords = np.array([0.0, 0.0] * vertex_count, dtype=np.float32).reshape(vertex_count, 2)

        if 'normals' in geometry_data and geometry_data['normals']:
            normals = np.array(geometry_data['normals'], dtype=np.float32)
        else:
            normals = np.array([0.0, 0.0, 1.0] * vertex_count, dtype=np.float32).reshape(vertex_count, 3)

        # Important!! : doing this at last.
        if 'tangents' in geometry_data and geometry_data['tangents']:
            tangents = np.array(geometry_data['tangents'], dtype=np.float32)
        else:
            tangents = compute_tangent(positions, texcoords, normals, indices)
            geometry_data['tangents'] = tangents.tolist()

        self.vertexBuffer = VertexArrayBuffer([positions, colors, normals, tangents, texcoords], indices,
                                              dtype=np.float32)
        self.valid = True

    def bindBuffers(self):
        self.vertexBuffer.bindBuffer()

    def draw(self):
        self.vertexBuffer.draw_elements()


class GeometryInstance:
    def __init__(self, geometry, parent_mesh, parent_object):
        """
        :param geometry: Geometry
        :param parent_mesh: Mesh
        :param parent_object: BaseObject...
        """
        self.geometry = geometry
        self.parent_mesh = parent_mesh
        self.parent_object = parent_object
        self.material_instance = None

    def set_material_instance(self, material_instance):
        self.material_instance = material_instance

    def bindBuffers(self):
        self.geometry.vertexBuffer.bindBuffer()

    def draw(self):
        self.geometry.vertexBuffer.draw_elements()


class Mesh:
    def __init__(self, mesh_name, geometry_datas):
        logger.info("Create %s : %s" % (GetClassName(self), mesh_name))

        self.name = mesh_name
        self.geometry_datas_for_save = geometry_datas  # Test Code : temp data for save
        self.geometries = []
        self.attributes = Attributes()

        for geometry_data in geometry_datas:
            geometry = Geometry(geometry_data)
            if geometry.valid:
                self.geometries.append(geometry)
        self.geometry_count = len(self.geometries)

    def get_save_data(self):
        return self.geometry_datas_for_save

    def get_geometry_instances(self, parent_object):
        """
        :param parent_object: BaseObject
        :return:
        """
        geometry_instances = []
        for geometry in self.geometries:
            geometry_instance = GeometryInstance(geometry, self, parent_object)
            geometry_instances.append(geometry_instance)
        return geometry_instances

    def get_geometry_count(self):
        return self.geometry_count

    def getAttribute(self):
        self.attributes.setAttribute("name", self.name)
        return self.attributes


class Triangle(Mesh):
    def __init__(self):
        geometry_data = dict(
            positions=[(-1, -1, 0), (1, -1, 0), (-1, 1, 0)],
            colors=[(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)],
            normals=[(0, 0, 1), (0, 0, 1), (0, 0, 1)],
            texcoords=[(0, 0), (1, 0), (0, 1)],
            indices=[0, 1, 2])
        geometry_datas = [geometry_data, ]
        Mesh.__init__(self, GetClassName(self).lower(), geometry_datas)


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
        Mesh.__init__(self, GetClassName(self).lower(), geometry_datas)


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
