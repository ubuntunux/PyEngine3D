import time, math
from collections import OrderedDict

import numpy as np
from OpenGL.GL import *
from PIL import Image

import Resource
from Resource import *
from Object import TransformObject



class BaseObject(TransformObject):
    def __init__(self, name, pos, mesh, material):
        TransformObject.__init__(self, pos)
        self.name = name
        self.selected = False
        self.mesh = mesh
        self.material = material

        # load texture file
        image = Image.open(os.path.join(PathTextures, 'Wool_carpet_pxr128_bmp.tif'))
        ix, iy = image.size
        image = image.tobytes("raw", "RGBX", 0, -1)

        # binding texture
        self.textureDiffuse = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.textureDiffuse)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

        # load texture file
        image = Image.open(os.path.join(PathTextures, 'Wool_carpet_pxr128_normal.tif'))
        ix, iy = image.size
        image = image.tobytes("raw", "RGBX", 0, -1)

        # binding texture
        self.textureNormal = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.textureNormal)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

    def getObjectData(self):
        data = OrderedDict()
        data['name'] = self.name
        data['position'] = self.pos
        data['rotation'] = self.rot
        data['scale'] = self.scale
        data['mesh'] = self.mesh.name if self.mesh else ""
        data['material'] = self.material.name if self.material else ""
        return data

    def setObjectData(self, propertyName, propertyValue):
        if propertyName == 'position':
            self.setPos(propertyValue)
        elif propertyName == 'rotation':
            self.setRot(propertyValue)
        elif propertyName == 'scale':
            self.setScale(propertyValue)
        elif propertyName == 'mesh':
            self.mesh = Resource.ResourceManager.instance().getMesh(propertyValue)
        elif propertyName == 'material':
            self.material = Resource.ResourceManager.instance().getMaterial(propertyValue)

    def setSelected(self, selected):
        self.selected = selected

    def draw(self, lastProgram, lastMesh, cameraPos, view, perspective, vpMatrix, lightPos, lightColor, selected=False):
        self.setYaw((time.time() * 0.2) % math.pi * 2.0)  # Test Code
        self.updateTransform()

        if self.material is None or self.mesh is None:
            return

        # bind shader program
        if lastProgram != self.material.program:
            glUseProgram(self.material.program)

        loc = glGetUniformLocation(self.material.program, "model")
        glUniformMatrix4fv(loc, 1, GL_FALSE, self.matrix)

        loc = glGetUniformLocation(self.material.program, "view")
        glUniformMatrix4fv(loc, 1, GL_FALSE, view)

        loc = glGetUniformLocation(self.material.program, "perspective")
        glUniformMatrix4fv(loc, 1, GL_FALSE, perspective)

        loc = glGetUniformLocation(self.material.program, "mvp")
        glUniformMatrix4fv(loc, 1, GL_FALSE, np.dot(self.matrix, vpMatrix))

        loc = glGetUniformLocation(self.material.program, "diffuseColor")
        glUniform4fv(loc, 1, (0,0,0.5,1) if selected else (0.3, 0.3, 0.3, 1.0))

        # selected object render color
        loc = glGetUniformLocation(self.material.program, "camera_position")
        glUniform3fv(loc, 1, cameraPos)

        # selected object render color
        loc = glGetUniformLocation(self.material.program, "light_position")
        glUniform3fv(loc, 1, lightPos)

        # selected object render color
        loc = glGetUniformLocation(self.material.program, "light_color")
        glUniform4fv(loc, 1, lightColor)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.textureDiffuse)
        glUniform1i(glGetUniformLocation(self.material.program, "textureDiffuse"), 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.textureNormal)
        glUniform1i(glGetUniformLocation(self.material.program, "textureNormal"), 1)

        # At last, bind buffers
        if lastMesh != self.mesh:
            self.mesh.bindBuffers()
        self.mesh.draw()
        # glUseProgram(0)
