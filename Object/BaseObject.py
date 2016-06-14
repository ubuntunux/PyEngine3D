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
        image = Image.open('Resources/Textures/multimaterial.jpg')
        ix, iy = image.size
        image = image.tobytes("raw", "RGBX", 0, -1)

        # binding texture
        self.texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

    def setSelected(self, selected):
        self.selected = selected

    def draw(self, lastProgram, lastPrimitive,  cameraPos, view, perspective, lightPos, lightColor, selected=False):
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
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glUniform1i(glGetUniformLocation(self.shader.program, "ourTexture"), 0)

        # At last, bind buffers
        if lastPrimitive != self.primitive:
            self.primitive.bindBuffers()

        # Primitive draw
        self.primitive.draw()

        #glUseProgram(0)