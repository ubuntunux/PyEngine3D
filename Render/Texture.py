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


class Texture:
    def __init__(self, textureFileName, buffer, width, height, image_mode):
        logger.info("Create " + getClassName(self) + " : " + textureFileName)
        self.name = textureFileName
        self.width = width
        self.height = height
        self.target = GL_TEXTURE_2D
        self.attribute = Attributes()
        texture_mode = get_texture_mode(image_mode)

        self.texture_bind = glGenTextures(1)
        glBindTexture(self.target, self.texture_bind)
        glTexImage2D(self.target, 0, texture_mode, width, height, 0, texture_mode, GL_UNSIGNED_BYTE, buffer)
        glTexParameteri(self.target, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(self.target, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(self.target, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(self.target, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(self.target)

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDeleteTextures(1, self.texture_bind)

    def bind(self):
        glBindTexture(self.target, self.texture_bind)

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        return self.attribute


class FrameBuffer:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.render_buffer_color = glGenRenderbuffers(1)
        self.render_buffer_depth = glGenRenderbuffers(1)

        glBindRenderbuffer(GL_RENDERBUFFER, self.render_buffer_color)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA, width, height)
        glBindRenderbuffer(GL_RENDERBUFFER, self.render_buffer_depth)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height)

        self.framebuffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.framebuffer)
        glFramebufferRenderbuffer(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, self.render_buffer_color)
        glFramebufferRenderbuffer(GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.render_buffer_depth)

    def begin(self):
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.framebuffer)
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
