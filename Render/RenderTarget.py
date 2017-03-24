from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Core import logger
from Utilities import Singleton, getClassName, Attributes,AutoEnum
from .Texture import Texture2D


class RenderTargets(AutoEnum):
    BACKBUFFER = ()
    DEPTHSTENCIL = ()
    DIFFUSE = ()
    COUNT = ()


class RenderTargetManager(Singleton):
    name = "RenderTargetManager"

    def __init__(self):
        self.rendertargets = [None, ] * RenderTargets.COUNT.value

    def initialize(self):
        logger.info("initialize " + getClassName(self))
        self.clear()

    def create_rendertargets(self, width, height):
        self.clear()

        fullsize_x = width
        fullsize_y = height
        halfsize_x = int(width / 2)
        halfsize_y = int(height / 2)
        no_data = None

        self.__create_rendertarget(RenderTargets.BACKBUFFER, GL_RGBA8, fullsize_x, fullsize_y, GL_BGRA,
                                   GL_UNSIGNED_BYTE, no_data)
        self.__create_rendertarget(RenderTargets.DEPTHSTENCIL, GL_DEPTH24_STENCIL8, fullsize_x, fullsize_y,
                                   GL_DEPTH_STENCIL, GL_UNSIGNED_INT_24_8, no_data)
        self.__create_rendertarget(RenderTargets.DIFFUSE, GL_RGBA8, fullsize_x, fullsize_y, GL_BGRA,
                                   GL_UNSIGNED_BYTE, no_data)

    def clear(self):
        self.rendertargets = [None, ] * RenderTargets.COUNT.value

    def __create_rendertarget(self, texture_enum: RenderTargets, internal_format=GL_RGBA, width=1024, height=1024,
                              texture_format=GL_BGRA, data_type=GL_UNSIGNED_BYTE, data=None) -> Texture2D:
        texture = Texture2D(str(texture_enum), internal_format, width, height, texture_format, data_type, data)
        self.rendertargets[texture_enum.value] = texture
        return texture

    def get_rendertarget(self, texture_enum: RenderTargets) -> Texture2D:
        return self.rendertargets[texture_enum.value]


class FrameBuffer:
    def __init__(self, width, height):
        logger.info("Create " + getClassName(self))
        self.rendertarget_width = width
        self.rendertarget_height = height
        self.buffer = glGenFramebuffers(1)

    def delete(self):
        glDeleteFramebuffers(self.buffer)

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer)

    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def bind_rendertarget(self, colortexture, clear_color, depthtexture, clear_depth):
        clear_flag = 0
        if colortexture:
            if clear_color:
                clear_flag |= GL_COLOR_BUFFER_BIT
            colortexture.attach(GL_COLOR_ATTACHMENT0)
            self.rendertarget_width = colortexture.width
            self.rendertarget_height = colortexture.height
            glViewport(0, 0, self.rendertarget_width, self.rendertarget_height)

            # gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            # if gl_error != GL_FRAMEBUFFER_COMPLETE:
            #     logger.error("glCheckFramebufferStatus error %d." % gl_error)

        if depthtexture:
            if clear_depth:
                clear_flag |= GL_DEPTH_BUFFER_BIT
            depthtexture.attach(GL_DEPTH_STENCIL_ATTACHMENT)

        if clear_flag:
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(clear_flag)

    def blitFramebuffer(self, framebuffer_width, framebuffer_height):
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)  # the default framebuffer active
        # glViewport(0, 0, self.width, self.height)
        # glClearColor(0.0, 0.0, 0.0, 1.0)
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glBlitFramebuffer(0, 0, self.rendertarget_width, self.rendertarget_height,
                          0, 0, framebuffer_width, framebuffer_height,
                          GL_COLOR_BUFFER_BIT, GL_NEAREST)
