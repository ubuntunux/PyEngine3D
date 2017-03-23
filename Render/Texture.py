from OpenGL.GL import *

from Resource import *
from Core import logger
from Utilities import Singleton, getClassName, Attributes


class Texture2D:
    def __init__(self, texture_name, internal_format=GL_RGBA, width=1024, height=1024, texture_format=GL_BGRA,
                 data_type=GL_UNSIGNED_BYTE, data=None):
        logger.info("Create " + getClassName(self) + " : " + texture_name)
        self.name = texture_name
        self.width = width
        self.height = height
        self.attribute = Attributes()
        self.internal_format = internal_format  # The number of channels and the data type
        self.texture_format = texture_format  # R,G,B,A order. GL_BGRA is faster than GL_RGBA

        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        glTexImage2D(GL_TEXTURE_2D, 0, internal_format, width, height, 0, texture_format, data_type, data)
        glGenerateMipmap(GL_TEXTURE_2D)

        # create indivisual mipmapThis creates a texture with a single mipmap level.
        # You will also need separate glTexSubImage2D calls to upload each mipmap
        # glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, width, height)
        # glTexSubImage2D(GL_TEXTURE_2D, 0​, 0, 0, width​, height​, GL_BGRA, GL_UNSIGNED_BYTE, pixels)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDeleteTextures(1, self.texture)

    def bind(self):
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def attach(self, attachment=GL_COLOR_ATTACHMENT0):
        glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, self.texture, 0)

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        return self.attribute


# Use Texture2D intead of RenderBuffer.
class RenderBuffer:
    """
    RenderBuffer is fater than Texture2D, but it's read-only.
    """
    def __init__(self, texture_name, width, height, internal_format=GL_RGBA):
        logger.info("Create " + getClassName(self) + " : " + texture_name)
        self.name = texture_name
        self.width = width
        self.height = height
        self.internal_format = internal_format  # GL_RGBA, GL_DEPTH_COMPONENT32, GL_DEPTH24_STENCIL8

        self.buffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.buffer)
        glRenderbufferStorage(GL_RENDERBUFFER, internal_format, width, height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    def attach(self, attachment=GL_COLOR_ATTACHMENT0):
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, attachment, GL_RENDERBUFFER, self.buffer)
