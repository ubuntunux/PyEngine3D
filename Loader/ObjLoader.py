import os
import Image
from OpenGL.GL import *
import traceback

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
                raise ValueError, "mtl file doesn't start with newmtl stmt"
                print "mtl file doesn't start with newmtl stmt"
            elif preFix == 'map_Kd':
                # load the texture referred to by this declaration
                texName = os.path.join(filepath, line[1])
                mtl['map_Kd'] = texName
                try:
                    # load texture file
                    image = Image.open(texName)                    
                    ix, iy = image.size
                    image = image.tostring("raw", "RGBX", 0, -1)
    
                    # binding texture
                    texid = mtl['texture_Kd'] = glGenTextures(1)
                    glBindTexture(GL_TEXTURE_2D, texid)
                    glPixelStorei(GL_UNPACK_ALIGNMENT,1)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)                    
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)                    
                except:
                    print traceback.format_exc()
            elif len(line) > 1:
                mtl[preFix] = map(float, line[1:])
    return contents
    

class OBJ:
    def __init__(self, filename, scale, swapyz):
        '''Loads a wavefront OBJ file.'''
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.mtl = None
        self.glList = None
        
        # check is exist file
        if os.path.isfile(filename):
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
                    self.vertices.append(map(lambda x:float(x) * scale, line[1:4]))
                # vertex normal
                elif preFix == 'vn' and len(line) >= 4:
                    bNormalAutoGen = False
                    self.normals.append(map(float, line[1:4]))
                # texture coordinate
                elif preFix == 'vt'  and len(line) >= 3:
                    self.texcoords.append(map(float, line[1:3]))
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
                        value = map(int, value.split('/'))                        
                        value += [0, 0]
                        
                        # insert vertex, texcoord, normal index
                        vertices.append(int(value[0]))
                        texcoords.append(value[1])
                        normals.append(value[2])
                    # append face list                       
                    self.faces.append((vertices, normals, texcoords, lastMaterial))
                    
            # generate gl list
            self.generate()
                    
    # Generate        
    def generate(self):
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
                    glNormal3fv(self.normals[normals[i] - 1])
                # set texture Coordinate
                if texcoords[i] > 0:
                    glTexCoord2fv(self.texcoords[texcoords[i] - 1])
                # set vertices
                glVertex3fv(self.vertices[vertices[i] - 1])
            glEnd()
        glDisable(GL_TEXTURE_2D)
        glEndList()
        
    def changeColor(self):
        glColor(1, 1, 0)
    
    # draw
    def draw(self):
        if self.glList:
            glCallList(self.glList)
            