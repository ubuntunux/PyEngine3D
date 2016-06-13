import os, datetime, glob, traceback
from collections import OrderedDict

from PIL import Image
from OpenGL.GL import *

from Core import logger

defaultTexCoord = [0.0, 0.0]
defaultNormal = [0.1, 0.1, 0.1]

def LoadMTL(filepath, filename):
    contents = {}
    mtl = None
    # check is exist file
    filename = os.path.join(filepath, filename)
    if os.path.isfile(filename):
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
            
            preFix = line[0]
            # create new material
            if preFix == 'newmtl' and len(line) > 1:
                mtlName = line[1]
                mtl = contents[mtlName] = {}
            elif mtl is None:
                logger.warn("mtl file doesn't start with newmtl stmt")
                raise ValueError("mtl file doesn't start with newmtl stmt")
            elif preFix == 'map_Kd':
                # load the texture referred to by this declaration
                texName = os.path.join(filepath, line[1])
                mtl['map_Kd'] = texName
                try:
                    # load texture file
                    image = Image.open(texName)                    
                    ix, iy = image.size
                    image = image.tobytes("raw", "RGBX", 0, -1)
    
                    # binding texture
                    texid = mtl['texture_Kd'] = glGenTextures(1)
                    glBindTexture(GL_TEXTURE_2D, texid)
                    glPixelStorei(GL_UNPACK_ALIGNMENT,1)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)                    
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)                    
                except:
                    logger.error(traceback.format_exc())
            elif len(line) > 1:
                mtl[preFix] = list(map(float, line[1:]))
    return contents
    

class OBJ:
    def __init__(self, filename, scale, swapyz):
        """
        Loads a wavefront OBJ file.
        """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.defaultTexCoordIndex = -1
        self.faces = []
        self.mtl = None
        self.glList = None
        self.filename = filename
        self.modifyTime = ''
        self.fileSize = 0 # byte
        
        # check is exist file
        if os.path.exists(filename):
            mTime = os.path.getmtime(filename)
            self.modifyTime = str(datetime.datetime.fromtimestamp(mTime))
            self.fileSize = os.path.getsize(filename)
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
                
                # vertex position
                if preFix == 'v' and len(line) >= 4:
                    # apply scale
                    self.vertices.append(list(map(lambda x:float(x) * scale, line[1:4])))
                # vertex normal
                elif preFix == 'vn' and len(line) >= 4:
                    bNormalAutoGen = False
                    self.normals.append(list(map(float, line[1:4])))
                # texture coordinate
                elif preFix == 'vt'  and len(line) >= 3:
                    self.texcoords.append(list(map(float, line[1:3])))
                # material name
                elif preFix in ('usemtl', 'usemat'):
                    lastMaterial = line[1]
                # material filename, load material
                elif preFix == 'mtllib':
                    self.mtl = LoadMTL(filePath,  line[1])
                # faces
                elif preFix == 'f':
                    vertices = []
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
                        vertices.append(value[0])
                        texcoords.append(value[1])
                        normals.append(value[2])

                    # append face list
                    if len(vertices) == 3:
                        self.faces.append((vertices, normals, texcoords, lastMaterial))
                    elif len(vertices) == 4:
                        self.faces.append((vertices[:3], normals[:3], texcoords[:3], lastMaterial))
                        self.faces.append(([vertices[2], vertices[3], vertices[0]], [normals[2], normals[3], normals[0]], [texcoords[2], texcoords[3], texcoords[0]], lastMaterial))

    def saveToMesh(self):
        vertices = []
        normals = []
        texcoords = []
        indices = []
        indexMap = OrderedDict()

        for face in self.faces:
            # exclude material
            vertexIndex, normalIndex, texcoordIndex, material = face
            for i in range(len(vertexIndex)):
                vntIndex = (vertexIndex[i], normalIndex[i], texcoordIndex[i])
                if vntIndex in indexMap:
                    indices.append(list(indexMap.keys()).index(vntIndex))
                else:
                    indices.append(len(indexMap))
                    indexMap[vntIndex] = None
                    vertices.append(self.vertices[vertexIndex[i]])
                    normals.append(self.normals[normalIndex[i]])
                    texcoords.append(self.texcoords[texcoordIndex[i]])

        data = dict(filename=self.filename, modifyTime=self.modifyTime, fileSize=self.fileSize,
                    vertices=vertices, normals=normals, texcoords=texcoords, indices=indices)

        newFilename = os.path.splitext(self.filename)[0] + ".mesh"
        f = open(newFilename, 'w')
        f.writelines(str(data))
        f.close()

                    
    # Generate        
    def generateInstruction(self):
        self.glList = glGenLists(1)
        glNewList(self.glList, GL_COMPILE)
        glEnable(GL_TEXTURE_2D)
        glFrontFace(GL_CCW)
        # generate  face
        for face in self.faces:
            vertices, normals, texcoords, material = face
            
            # set material
            if self.mtl != None and material in self.mtl:
                mtl = self.mtl[material]
                if 'texture_Kd' in mtl:
                    # set diffuse texture
                    glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
                elif 'Kd' in mtl:
                    # just use diffuse colour
                    glColor(*mtl['Kd'])
            
            # generate face
            glBegin(GL_POLYGON)
            for i in range(len(vertices)):
                # set normal
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i]])
                # set texture Coordinate
                if texcoords[i] > 0:
                    glTexCoord2fv(self.texcoords[texcoords[i]])
                # set vertices
                glVertex3fv(self.vertices[vertices[i]])
            glEnd()
        glDisable(GL_TEXTURE_2D)
        glEndList()
        
    def changeColor(self):
        glColor(1, 1, 0)
    
    # draw
    def draw(self):
        if self.glList:
            glCallList(self.glList)


def convertToMesh(filePath):
    for filename in glob.glob(os.path.join(filePath, '*.obj')):
        obj = OBJ(filename, 1, True)
        print("Convering :", filename)
        obj.saveToMesh()
        print("Done.")


if __name__ == '__main__':
    convertToMesh(os.path.join('..', 'Resources', 'Meshes'))