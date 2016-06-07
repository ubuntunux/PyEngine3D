from OpenGL.GL import *

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

        # At last, bind buffers
        if lastPrimitive != self.primitive:
            self.primitive.bindBuffers()

        # Primitive draw
        self.primitive.draw()

        #glUseProgram(0)