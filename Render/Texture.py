import os, glob, traceback

from OpenGL.GL import *
from PIL import Image

from Resource import *
from Core import logger
from Utilities import Singleton, getClassName, Attributes


class Texture:
    def __init__(self, textureFileName, buffer, width, height):
        logger.info("Create " + getClassName(self) + " : " + textureFileName)
        self.name = textureFileName
        self.width = width
        self.height = height

        self.texture_bind = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_bind)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, buffer)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

    def __del__(self):
        self.delete()

    def delete(self):
        pass
        #glDeleteTextures(1, self.texture_bind)

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        return self.attribute
