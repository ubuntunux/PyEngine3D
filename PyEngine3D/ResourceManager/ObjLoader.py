import copy
import os, traceback
from collections import OrderedDict

import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.Utilities import *


defaultTexCoord = [0.0, 0.0]
defaultNormal = [0.0, 1.0, 0.0]


class MeshObject:
    def __init__(self, default_name):
        self.name = default_name
        self.group_name = ''
        self.mtl_name = ''
        self.indices = []


class OBJ:
    def __init__(self, filename, scale, swapyz):
        """
        Loads a wavefront OBJ file.
        """
        self.meshes = []
        self.positions = []
        self.normals = []
        self.texcoords = []
        self.glList = None
        self.filename = filename

        # check is exist file
        if os.path.exists(filename):
            # load OBJ file
            default_name = os.path.splitext(os.path.split(filename)[-1])[0]
            preFix = None
            mesh_object = None
            for line in open(filename, "r"):
                # is comment?
                line = line.strip()
                if line == '' or line.startswith('#'):
                    continue

                values = [value.strip() for value in line.split()]
                if len(values) < 2:
                    continue

                # start to paring a new mesh.
                if mesh_object is None or (preFix == 'f' and values[0] not in ('f', 's')):
                    mesh_object = MeshObject(default_name)
                    self.meshes.append(mesh_object)

                # first strings
                preFix = values[0]
                values = values[1:]

                if preFix == 'o':
                    mesh_object.name = ' '.join(values)
                elif preFix == 'g':
                    mesh_object.group_name = ' '.join(values)
                    if mesh_object.name == '':
                        mesh_object.name = mesh_object.group_name
                elif preFix == 'mtllib':
                    # TODO : Parsing mtllib
                    pass
                # vertex position
                elif preFix == 'v' and len(values) >= 3:
                    # apply scale
                    self.positions.append(list(map(lambda x: float(x) * scale, values[:3])))
                # vertex normal
                elif preFix == 'vn' and len(values) >= 3:
                    self.normals.append(list(map(float, values[:3])))
                # texture coordinate
                elif preFix == 'vt' and len(values) >= 2:
                    self.texcoords.append(list(map(float, values[:2])))
                # material name
                elif preFix in ('usemtl', 'usemat'):
                    mesh_object.material = ' '.join(values)
                    if mesh_object.name == '':
                        mesh_object.name = mesh_object.material
                # faces
                elif preFix == 'f':
                    pos_indices = []
                    normal_indices = []
                    tex_indices = []

                    # If texcoord is empty, add the default texcoord.
                    if len(self.texcoords) < 1:
                        self.texcoords.append(copy.copy(defaultTexCoord))
                    # If normal is empty, add the default normal.
                    if len(self.normals) < 1:
                        self.normals.append(copy.copy(defaultNormal))

                    # parsing index data
                    for indices in values:
                        pos_index, tex_index, normal_index = list(
                            map(lambda x: int(x) - 1 if x else 0, indices.split('/')))
                        # insert vertex, texcoord, normal index
                        pos_indices.append(pos_index)
                        tex_indices.append(tex_index)
                        normal_indices.append(normal_index)

                    # append face list
                    if len(pos_indices) == 3:
                        mesh_object.indices.append((pos_indices, normal_indices, tex_indices))
                    # Quad to Two Triangles.
                    elif len(pos_indices) == 4:
                        mesh_object.indices.append((pos_indices[:3], normal_indices[:3], tex_indices[:3]))
                        mesh_object.indices.append(([pos_indices[2], pos_indices[3], pos_indices[0]],
                                                    [normal_indices[2], normal_indices[3], normal_indices[0]],
                                                    [tex_indices[2], tex_indices[3], tex_indices[0]]))

    def get_geometry_data(self):
        geometry_datas = []
        for mesh in self.meshes:
            positions = []
            normals = []
            texcoords = []
            indices = []

            indexMap = {}

            bound_min = Float3(FLOAT32_MAX, FLOAT32_MAX, FLOAT32_MAX)
            bound_max = Float3(FLOAT32_MIN, FLOAT32_MIN, FLOAT32_MIN)
            for n, mesh_indices in enumerate(mesh.indices):
                # exclude material
                postionIndicies, normalIndicies, texcoordIndicies = mesh_indices
                for i in range(len(postionIndicies)):
                    index_key = (postionIndicies[i], normalIndicies[i], texcoordIndicies[i])
                    if index_key in indexMap:
                        indices.append(indexMap[index_key])
                    else:
                        indices.append(len(indexMap))
                        indexMap[index_key] = len(indexMap)
                        positions.append(self.positions[postionIndicies[i]])
                        normals.append(self.normals[normalIndicies[i]])
                        texcoords.append(self.texcoords[texcoordIndicies[i]])
                        # bounding box
                        position = positions[-1]
                        for j in range(3):
                            if bound_min[j] > position[j]:
                                bound_min[j] = position[j]
                            if bound_max[j] < position[j]:
                                bound_max[j] = position[j]

            if len(positions) == 0:
                logger.info('%s has a empty mesh. %s' % (self.filename, mesh.name))
                continue

            geometry_data = dict(name=mesh.name,
                                 positions=copy.deepcopy(positions),
                                 normals=copy.deepcopy(normals),
                                 texcoords=copy.deepcopy(texcoords),
                                 indices=copy.deepcopy(indices),
                                 bound_min=copy.deepcopy(bound_min),
                                 bound_max=copy.deepcopy(bound_max),
                                 radius=length(bound_max - bound_min))
            geometry_datas.append(geometry_data)
        return geometry_datas

    def get_mesh_data(self):
        geometry_datas = self.get_geometry_data()
        # skeleton_datas = self.get_skeleton_data()
        mesh_data = dict(
            geometry_datas=geometry_datas
        )
        return mesh_data

    # Generate
    def generateInstruction(self):
        self.glList = glGenLists(1)
        glNewList(self.glList, GL_COMPILE)
        glEnable(GL_TEXTURE_2D)
        glFrontFace(GL_CCW)
        # generate  face
        for face in self.faces:
            positions, normals, texcoords, material = face

            # set material
            if self.mtl is not None and material in self.mtl:
                mtl = self.mtl[material]
                if 'texture_Kd' in mtl:
                    # set diffuse texture
                    glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
                elif 'Kd' in mtl:
                    # just use diffuse colour
                    glColor(*mtl['Kd'])
            
            # generate face
            glBegin(GL_POLYGON)
            for i in range(len(positions)):
                # set normal
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i]])
                # set texture Coordinate
                if texcoords[i] > 0:
                    glTexCoord2fv(self.texcoords[texcoords[i]])
                # set positions
                glVertex3fv(self.positions[positions[i]])
            glEnd()
        glDisable(GL_TEXTURE_2D)
        glEndList()
        
    def changeColor(self):
        glColor(1, 1, 0)
    
    # draw
    def draw(self):
        if self.glList:
            glCallList(self.glList)
