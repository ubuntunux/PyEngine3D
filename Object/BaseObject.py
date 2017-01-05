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

        if self.material:
            program = self.material.program

            self.sceneConstBuffer = glGenBuffers(1)
            glBindBuffer(GL_UNIFORM_BUFFER, self.sceneConstBuffer)
            self.sceneConstBind = 0
            self.sceneConstIndex = glGetUniformBlockIndex(program, 'sceneConstants')
            glUniformBlockBinding(program, self.sceneConstIndex, self.sceneConstBind)
            glBindBufferBase(GL_UNIFORM_BUFFER, self.sceneConstBind, self.sceneConstBuffer)

            self.lightConstBuffer = glGenBuffers(1)
            glBindBuffer(GL_UNIFORM_BUFFER, self.lightConstBuffer)
            self.lightConstBind = 0
            self.lightConstIndex = glGetUniformBlockIndex(program, 'lightConstants')
            glUniformBlockBinding(program, self.lightConstIndex, self.lightConstBind)
            glBindBufferBase(GL_UNIFORM_BUFFER, self.lightConstBind, self.lightConstBuffer)

            self.bind_model = glGetUniformLocation(program, "model")
            self.bind_mvp = glGetUniformLocation(program, "mvp")
            self.bind_diffuseColor = glGetUniformLocation(program, "diffuseColor")
            self.bind_light_color = glGetUniformLocation(self.material.program, "light_color")
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

    def draw(self, lastProgram, lastMesh, sceneConstData, lightConstData, vpMatrix, lightColor, selected=False):
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

            #glBindBuffer(GL_UNIFORM_BUFFER, self.sceneConstBuffer)
            #glUniformBlockBinding(program, self.sceneConstIndex, self.sceneConstBind)
            glBufferData(GL_UNIFORM_BUFFER, sceneConstData.nbytes, sceneConstData, GL_STATIC_DRAW)
            glBindBufferBase(GL_UNIFORM_BUFFER, self.sceneConstBind, self.sceneConstBuffer)

            #glBindBuffer(GL_UNIFORM_BUFFER, self.lightConstBuffer)
            #glUniformBlockBinding(program, self.lightConstIndex, self.lightConstBind)
            glBufferData(GL_UNIFORM_BUFFER, lightConstData.nbytes, lightConstData, GL_STATIC_DRAW)
            glBindBufferBase(GL_UNIFORM_BUFFER, self.lightConstBind, self.lightConstBuffer)

        glUniformMatrix4fv(self.bind_model, 1, GL_FALSE, transform.matrix)
        glUniformMatrix4fv(self.bind_mvp, 1, GL_FALSE, np.dot(transform.matrix, vpMatrix))
        glUniform4fv(self.bind_diffuseColor, 1, (0, 0, 0.5, 1) if selected else (0.3, 0.3, 0.3, 1.0))
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
