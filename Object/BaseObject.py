import time, math

import numpy as np
from OpenGL.GL import *
from PIL import Image

import Resource
from Resource import *
from Object import TransformObject, Primitive
from Render import Material
from Utilities import Attributes


class BaseObject:
    def __init__(self, name, pos, mesh, material):
        self.name = name
        self.selected = False
        self.transform = TransformObject(pos)
        self.mesh = mesh
        self.material = None
        self.attributes = Attributes()

        if material:
            self.setMaterial(material)

    # all below parameters must move to Materal Class.
    def setMaterial(self, material):
        self.material = material

        # binding datas
        self.commonBuffer = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.commonBuffer)

        if self.material:
            program = self.material.program
            self.commonBind = 0
            glUniformBlockBinding(program, glGetUniformBlockIndex(program, 'commonConstants'), self.commonBind)

            self.bind_model = glGetUniformLocation(program, "model")
            self.bind_mvp = glGetUniformLocation(program, "mvp")
            self.bind_diffuseColor = glGetUniformLocation(program, "diffuseColor")
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
        self.attributes.setAttribute('pos', self.transform.pos)
        self.attributes.setAttribute('rot', self.transform.rot)
        self.attributes.setAttribute('scale', self.transform.scale)
        self.attributes.setAttribute('mesh', self.mesh.name if self.mesh else "", type(Primitive))
        self.attributes.setAttribute('material', self.material.name if self.material else "", type(Material))
        return self.attributes

    def setAttribute(self, attributeName, attributeValue):
        if attributeName == 'pos':
            self.transform.setPos(attributeValue)
        elif attributeName == 'rot':
            self.transform.setRot(attributeValue)
        elif attributeName == 'scale':
            self.transform.setScale(attributeValue)
        elif attributeName == 'mesh':
            self.mesh = Resource.ResourceManager.instance().getMesh(attributeValue)
        elif attributeName == 'material':
            self.material = Resource.ResourceManager.instance().getMaterial(attributeValue)

    def setSelected(self, selected):
        self.selected = selected

    def draw(self, lastProgram, lastMesh, commonData, vpMatrix, lightPos, lightColor, selected=False):
        transform = self.transform
        # test code
        transform.setYaw((time.time() * 0.2) % math.pi * 2.0)  # Test Code

        # update transform
        transform.updateTransform()

        if self.material is None or self.mesh is None:
            return

        program = self.material.program

        # bind shader program
        if lastProgram != program:
            glUseProgram(program)

        # Uniform Block
        glBufferData(GL_UNIFORM_BUFFER, commonData.nbytes, commonData, GL_STATIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.commonBind, self.commonBuffer)

        glUniformMatrix4fv(self.bind_model, 1, GL_FALSE, transform.matrix)
        glUniformMatrix4fv(self.bind_mvp, 1, GL_FALSE, np.dot(transform.matrix, vpMatrix))
        glUniform4fv(self.bind_diffuseColor, 1, (0, 0, 0.5, 1) if selected else (0.3, 0.3, 0.3, 1.0))
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
