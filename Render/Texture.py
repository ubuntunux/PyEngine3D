import os, glob, traceback, ctypes

from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from PIL import Image

from Resource import *
from Core import logger
from Utilities import Singleton, getClassName, Attributes


def get_texture_mode(str_image_mode):
    if str_image_mode == "RGB":
        return GL_RGB
    elif str_image_mode == "RGBA":
        return GL_RGBA
    return GL_RGBA


class Texture2D:
    def __init__(self, textureFileName, data, width, height, image_mode):
        logger.info("Create " + getClassName(self) + " : " + textureFileName)
        self.name = textureFileName
        self.width = width
        self.height = height
        self.target = GL_TEXTURE_2D
        self.attribute = Attributes()
        texture_mode = get_texture_mode(image_mode)

        self.texture = glGenTextures(1)
        glBindTexture(self.target, self.texture)

        glTexImage2D(self.target, 0, texture_mode, width, height, 0, texture_mode, GL_UNSIGNED_BYTE, data)
        glGenerateMipmap(self.target)

        glTexParameteri(self.target, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(self.target, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(self.target, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(self.target, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDeleteTextures(1, self.texture)

    def bind(self):
        glBindTexture(self.target, self.texture)

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        return self.attribute


class RenderTarget:
    def __init__(self, texture_name, width, height, internal_format=GL_RGBA):
        logger.info("Create " + getClassName(self) + " : " + texture_name)
        self.name = texture_name
        self.width = width
        self.height = height
        self.buffer = glGenRenderbuffers(1)
        self.internal_format = internal_format  # GL_RGBA, GL_DEPTH_COMPONENT24
        glBindRenderbuffer(GL_RENDERBUFFER, self.buffer)
        glRenderbufferStorage(GL_RENDERBUFFER, internal_format, width, height)

    def set_render_target(self, attachment=GL_COLOR_ATTACHMENT0):
        glFramebufferRenderbuffer(GL_DRAW_FRAMEBUFFER, attachment, GL_RENDERBUFFER, self.buffer)

    def set_depth_target(self):
        glFramebufferRenderbuffer(GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.buffer)

    def set_depth_stencil(self):
        glFramebufferRenderbuffer(GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.buffer)


class FrameBuffer:
    def __init__(self, width, height):
        logger.info("Create " + getClassName(self))
        self.width = width
        self.height = height

        self.framebuffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.framebuffer)

        self.backbuffer = RenderTarget(texture_name="BackBuffer", width=width, height=height, internal_format=GL_RGBA)
        self.depthbuffer = RenderTarget(texture_name="DepthTarget", width=width, height=height, internal_format=GL_DEPTH_COMPONENT24)

    def begin(self):
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.framebuffer)
        self.backbuffer.set_render_target()
        self.depthbuffer.set_depth_target()
        glViewport(0, 0, self.width, self.height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def end(self):
        # Set up to read from the renderbuffer and draw to window-system framebuffer
        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.framebuffer)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        # glViewport(0, 0, self.width, self.height)
        # glClearColor(0.0, 0.0, 0.0, 1.0)
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Do the copy
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)
