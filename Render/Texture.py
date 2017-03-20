import os, glob, traceback, ctypes

from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from PIL import Image

from Resource import *
from Core import logger
from Utilities import Singleton, getClassName, Attributes


class Texture2D:
    def __init__(self, textureFileName, internal_format=GL_RGBA, width=1024, height=1024, format=GL_BGRA,
                 data_type=GL_UNSIGNED_BYTE, data=None, mipmap=True):
        logger.info("Create " + getClassName(self) + " : " + textureFileName)
        self.name = textureFileName
        self.width = width
        self.height = height
        self.attribute = Attributes()
        self.internal_format = internal_format  # The number of channels and the data type
        self.format = format  # R,G,B,A order. GL_BGRA is faster than GL_RGBA

        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        glTexImage2D(GL_TEXTURE_2D, 0, internal_format, width, height, 0, format, data_type, data)
        if mipmap:
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


class RenderObject:
    """
    RenderObject is fater than Texture2D, but it's read-only.
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


class FrameBuffer:
    def __init__(self, width, height):
        logger.info("Create " + getClassName(self))
        self.width = width
        self.height = height

        self.framebuffer = glGenFramebuffers(1)
        # read/write : GL_FRAMEBUFFER, read : GL_READ_FRAMEBUFFER, write :GL_DRAW_FRAMEBUFFER
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)

        self.default_color_texture = Texture2D("ColorTexture", GL_RGBA8, width, height, GL_BGRA, GL_UNSIGNED_BYTE, None,
                                               False)
        self.default_depth_stencil_texture = Texture2D("DepthStencilTexture", GL_DEPTH24_STENCIL8, width, height,
                                                       GL_DEPTH_STENCIL, GL_UNSIGNED_INT_24_8, None, False)

        # RenderBufferObject is faster than Texture2D object, but it's read-only.
        # self.default_color_buffer = RenderObject(texture_name="ColorBuffer", width=width, height=height,
        #                                          internal_format=GL_RGBA)
        # self.default_depth_stencil_buffer = RenderObject(texture_name="DepthStencilBuffer", width=width,
        #                                                  height=height, internal_format=GL_DEPTH24_STENCIL8)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def delete(self):
        glDeleteFramebuffers(self.framebuffer)

    def begin(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)

        self.default_color_texture.attach(GL_COLOR_ATTACHMENT0)
        self.default_depth_stencil_texture.attach(GL_DEPTH_STENCIL_ATTACHMENT)

        gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if gl_error != GL_FRAMEBUFFER_COMPLETE:
            logger.error("glCheckFramebufferStatus error %d." % gl_error)

        glViewport(0, 0, self.width, self.height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def end(self):
        # Set up to read from the renderbuffer and draw to window-system framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)  # the default framebuffer active
        # glViewport(0, 0, self.width, self.height)
        # glClearColor(0.0, 0.0, 0.0, 1.0)
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Do the copy
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)
