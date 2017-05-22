import copy
import os, traceback
from collections import OrderedDict

import numpy as np

from Common import logger

defaultTexCoord = [0.0, 0.0]
defaultNormal = [0.1, 0.1, 0.1]


class OBJ:
    def __init__(self, filename, scale, swapyz):
        """
        Loads a wavefront OBJ file.
        """
        self.positions = []
        self.normals = []
        self.texcoords = []
        self.defaultTexCoordIndex = -1
        self.faces = []
        self.mtl = None
        self.glList = None
        self.filename = filename
        self.name = ""

        # check is exist file
        if os.path.exists(filename):
            filePath = os.path.split(filename)[0]
            lastMaterial = None

            # load OBJ file
            for line in open(filename, "r"):
                # is comment?
                line = line.strip()
                if line.startswith('#'):
                    continue

                # split with space
                line = line.split()

                # is empty?
                if not line:
                    continue

                # first strings
                preFix = line[0]

                # auto generate normal flag
                bNormalAutoGen = True
                # name
                if preFix == 'o':
                    self.name = line[1].strip()
                # vertex position
                if preFix == 'v' and len(line) >= 4:
                    # apply scale
                    self.positions.append(list(map(lambda x:float(x) * scale, line[1:4])))
                # vertex normal
                elif preFix == 'vn' and len(line) >= 4:
                    bNormalAutoGen = False
                    self.normals.append(list(map(float, line[1:4])))
                # texture coordinate
                elif preFix == 'vt' and len(line) >= 3:
                    self.texcoords.append(list(map(float, line[1:3])))
                # material name
                elif preFix in ('usemtl', 'usemat'):
                    lastMaterial = line[1]
                # material filename, load material
                elif preFix == 'mtllib':
                    pass
                    # self.mtl = LoadMTL(filePath,  line[1])
                # faces
                elif preFix == 'f':
                    positions = []
                    normals = []
                    texcoords = []
                    values = line[1:]
                    # split data
                    for value in values:
                        value = list(map(lambda x:int(x)-1 if x else -1, value.split('/')))
                        # check there is a texcoord or not.
                        if value[1] == -1:
                            if self.defaultTexCoordIndex == -1:
                                self.defaultTexCoordIndex = len(self.texcoords)
                                self.texcoords.append(defaultTexCoord)
                            value[1] = self.defaultTexCoordIndex

                        # insert vertex, texcoord, normal index
                        positions.append(value[0])
                        texcoords.append(value[1])
                        normals.append(value[2])

                    # append face list
                    if len(positions) == 3:
                        self.faces.append((positions, normals, texcoords, lastMaterial))
                    elif len(positions) == 4:
                        self.faces.append((positions[:3], normals[:3], texcoords[:3], lastMaterial))
                        self.faces.append(([positions[2], positions[3], positions[0]], [normals[2], normals[3], normals[0]], [texcoords[2], texcoords[3], texcoords[0]], lastMaterial))

    def get_geometry_data(self):
        positions = []
        normals = []
        texcoords = []
        indices = []
        indexMap = OrderedDict()

        for face in self.faces:
            # exclude material
            postionIndicies, normalIndicies, texcoordIndicies, material = face
            for i in range(len(postionIndicies)):
                vertIndex = (postionIndicies[i], normalIndicies[i], texcoordIndicies[i])
                if vertIndex in indexMap:
                    indices.append(list(indexMap.keys()).index(vertIndex))
                else:
                    indices.append(len(indexMap))
                    indexMap[vertIndex] = None
                    positions.append(self.positions[postionIndicies[i]])
                    normals.append(self.normals[normalIndicies[i]])

                    texcoords.append(self.texcoords[texcoordIndicies[i]])
        geometry_name = self.name or os.path.splitext(os.path.split(self.filename)[1])[0]
        geometry_data = dict(geometry_name=copy.deepcopy(geometry_name),
                             positions=copy.deepcopy(positions),
                             normals=copy.deepcopy(normals),
                             texcoords=copy.deepcopy(texcoords),
                             indices=copy.deepcopy(indices))
        return [geometry_data, ]

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
