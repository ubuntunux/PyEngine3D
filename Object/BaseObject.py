import time, math

from OpenGL.GL import *
from PIL import Image

from Object import TransformObject

#------------------------------#
# CLASS : BaseObject
#------------------------------#
class BaseObject(TransformObject):
    def __init__(self, name, pos, primitive, material):
        # init TransformObject
        TransformObject.__init__(self, pos)
        self.name = name
        self.selected = False
        self.primitive = primitive
        self.material = material
        self.shader = self.material.shader if self.material else None

        # load texture file
        image = Image.open('Resources/Textures/Wool_carpet_pxr128_bmp.tif')
        ix, iy = image.size
        image = image.tobytes("raw", "RGBX", 0, -1)

        # binding texture
        self.textureDiffuse = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.textureDiffuse)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

        # load texture file
        image = Image.open('Resources/Textures/Wool_carpet_pxr128_normal.tif')
        ix, iy = image.size
        image = image.tobytes("raw", "RGBX", 0, -1)

        # binding texture
        self.textureNormal = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.textureNormal)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

    def setSelected(self, selected):
        self.selected = selected

    def draw(self, lastProgram, lastPrimitive,  cameraPos, view, perspective, lightPos, lightColor, selected=False):
        # Test Code
        self.setYaw((time.time() * 0.2) % math.pi * 2.0)

        # update transform
        self.updateTransform()

        # use program
        if lastProgram != self.shader.program:
            glUseProgram(self.shader.program)

        loc = glGetUniformLocation(self.shader.program, "model")
        glUniformMatrix4fv(loc, 1, GL_FALSE, self.matrix)

        loc = glGetUniformLocation(self.shader.program, "view")
        glUniformMatrix4fv(loc, 1, GL_FALSE, view)

        loc = glGetUniformLocation(self.shader.program, "perspective")
        glUniformMatrix4fv(loc, 1, GL_FALSE, perspective)

        loc = glGetUniformLocation(self.shader.program, "diffuseColor")
        glUniform4fv(loc, 1, (0,0,0.5,1) if selected else (0.3, 0.3, 0.3, 1.0))

        # selected object render color
        loc = glGetUniformLocation(self.shader.program, "camera_position")
        glUniform3fv(loc, 1, cameraPos)

        # selected object render color
        loc = glGetUniformLocation(self.shader.program, "light_position")
        glUniform3fv(loc, 1, lightPos)

        # selected object render color
        loc = glGetUniformLocation(self.shader.program, "light_color")
        glUniform4fv(loc, 1, lightColor)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.textureDiffuse)
        glUniform1i(glGetUniformLocation(self.shader.program, "textureDiffuse"), 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.textureNormal)
        glUniform1i(glGetUniformLocation(self.shader.program, "textureNormal"), 1)

        # At last, bind buffers
        if lastPrimitive != self.primitive:
            self.primitive.bindBuffers()

        # Primitive draw
        self.primitive.draw()

        #glUseProgram(0)