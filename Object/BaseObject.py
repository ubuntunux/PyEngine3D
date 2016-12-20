import time, math

import numpy as np
from OpenGL.GL import *
from PIL import Image

import Resource
from Resource import *
from Object import TransformObject, Primitive
from Render import Material
from Utilities import Attributes


class BaseObject(TransformObject):

    def __init__(self, name, pos, mesh, material):
        TransformObject.__init__(self, pos)
        self.name = name
        self.selected = False
        self.mesh = mesh
        self.material = None
        self.attributes = Attributes()

        if material:
            self.setMaterial(material)

    # all below parameters must move to Materal Class.
    def setMaterial(self, material):
        self.material = material

        # binding datas
        self.buffer = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)

        if self.material:
            program = self.material.program
            self.bind_pvMatrix = 0
            glUniformBlockBinding(program, glGetUniformBlockIndex(program, 'pvMatrix'), self.bind_pvMatrix)

            self.bind_model = glGetUniformLocation(program, "model")
            self.bind_mvp = glGetUniformLocation(program, "mvp")
            self.bind_diffuseColor = glGetUniformLocation(program, "diffuseColor")
            self.bind_camera_position = glGetUniformLocation(program, "camera_position")
            self.bind_light_color = glGetUniformLocation(self.material.program, "light_color")
            self.bind_light_position = glGetUniformLocation(self.material.program, "light_position")
            self.bind_textureDiffuse = glGetUniformLocation(program, "textureDiffuse")
            self.bind_textureNormal = glGetUniformLocation(program, "textureNormal")

        # binding texture
        self.textureDiffuse = Resource.ResourceManager.instance().getTextureID("wool_d")

        # binding texture
        self.textureNormal = Resource.ResourceManager.instance().getTextureID("wool_n")

    def getAttribute(self):
        self.attributes.setAttribute('name', self.name)
        self.attributes.setAttribute('pos', self.pos)
        self.attributes.setAttribute('rot', self.rot)
        self.attributes.setAttribute('scale', self.scale)
        self.attributes.setAttribute('mesh', self.mesh.name if self.mesh else "", type(Primitive))
        self.attributes.setAttribute('material', self.material.name if self.material else "", type(Material))
        return self.attributes

    def setAttribute(self, attributeName, attributeValue):
        if attributeName == 'pos':
            self.setPos(attributeValue)
        elif attributeName == 'rot':
            self.setRot(attributeValue)
        elif attributeName == 'scale':
            self.setScale(attributeValue)
        elif attributeName == 'mesh':
            self.mesh = Resource.ResourceManager.instance().getMesh(attributeValue)
        elif attributeName == 'material':
            self.material = Resource.ResourceManager.instance().getMaterial(attributeValue)

    def setSelected(self, selected):
        self.selected = selected

    def draw(self, lastProgram, lastMesh, cameraPos, vpBuffer, vpMatrix, lightPos, lightColor, selected=False):
        self.setYaw((time.time() * 0.2) % math.pi * 2.0)  # Test Code
        self.updateTransform()

        if self.material is None or self.mesh is None:
            return

        program = self.material.program

        # bind shader program
        if lastProgram != program:
            glUseProgram(program)

        # Uniform Block
        glBufferData(GL_UNIFORM_BUFFER, vpBuffer.nbytes, vpBuffer, GL_DYNAMIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.bind_pvMatrix, self.buffer)

        glUniformMatrix4fv(self.bind_model, 1, GL_FALSE, self.matrix)
        glUniformMatrix4fv(self.bind_mvp, 1, GL_FALSE, np.dot(self.matrix, vpMatrix))
        glUniform4fv(self.bind_diffuseColor, 1, (0, 0, 0.5, 1) if selected else (0.3, 0.3, 0.3, 1.0))
        glUniform3fv(self.bind_camera_position, 1, cameraPos)
        glUniform3fv(self.bind_light_position, 1, lightPos)
        glUniform4fv(self.bind_light_color, 1, lightColor)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.textureDiffuse)
        glUniform1i(self.bind_textureDiffuse, 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.textureNormal)
        glUniform1i(self.bind_textureNormal, 1)

        # At last, bind buffers
        if lastMesh != self.mesh:
            self.mesh.bindBuffers()
        self.mesh.draw()
        # glUseProgram(0)
