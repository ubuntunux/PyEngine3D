from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Core import logger
from Utilities import Singleton, getClassName, Attributes,AutoEnum
from .Texture import Texture2D
from Render import Renderer


def copy_rendertarget(src: Texture2D, dst: Texture2D, filter_type=GL_NEAREST):
    glBlitFramebuffer(0, 0, src.width, src.height,
                      0, 0, dst.width, dst.height,
                      GL_COLOR_BUFFER_BIT, filter_type)


class RenderTargets(AutoEnum):
    BACKBUFFER = ()
    DEPTHSTENCIL = ()
    DIFFUSE = ()
    COUNT = ()


class RenderTargetManager(Singleton):
    name = "RenderTargetManager"

    def __init__(self):
        self.rendertargets = [None, ] * RenderTargets.COUNT.value
        self.renderer = None

    def initialize(self):
        logger.info("initialize " + getClassName(self))
        self.renderer = Renderer.Renderer.instance()

        fullsize_x = self.renderer.width
        fullsize_y = self.renderer.height
        halfsize_x = int(self.renderer.width / 2)
        halfsize_y = int(self.renderer.height / 2)
        no_mipmap = False
        no_data = None

        # Create Render Targets
        self.__create_rendertarget(RenderTargets.BACKBUFFER, GL_RGBA8, fullsize_x, fullsize_y, GL_BGRA,
                                   GL_UNSIGNED_BYTE, no_data, no_mipmap)
        self.__create_rendertarget(RenderTargets.DEPTHSTENCIL, GL_DEPTH24_STENCIL8, fullsize_x, fullsize_y,
                                   GL_DEPTH_STENCIL, GL_UNSIGNED_INT_24_8, no_data, no_mipmap)
        self.__create_rendertarget(RenderTargets.DIFFUSE, GL_RGBA8, fullsize_x, fullsize_y, GL_BGRA,
                                   GL_UNSIGNED_BYTE, no_data, no_mipmap)

    def __create_rendertarget(self, texture_enum: RenderTargets, internal_format=GL_RGBA, width=1024, height=1024,
                              texture_format=GL_BGRA, data_type=GL_UNSIGNED_BYTE, data=None, mipmap=True) -> Texture2D:
        texture = Texture2D(str(texture_enum), internal_format, width, height, texture_format, data_type, data, mipmap)
        self.rendertargets[texture_enum.value] = texture
        return texture

    def get_rendertarget(self, texture_enum: RenderTargets) -> Texture2D:
        return self.rendertargets[texture_enum.value]


class FrameBuffer:
    def __init__(self, width, height):
        logger.info("Create " + getClassName(self))
        self.framebuffer_width = width
        self.framebuffer_height = height
        self.rendertarget_width = width
        self.rendertarget_height = height
        self.framebuffer = glGenFramebuffers(1)

    def delete(self):
        glDeleteFramebuffers(self.framebuffer)

    def begin(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)

    def bind_rendertarget(self, colortexture, depthtexture, clear):
        if colortexture:
            colortexture.attach(GL_COLOR_ATTACHMENT0)
            self.rendertarget_width = colortexture.width
            self.rendertarget_height = colortexture.height
            glViewport(0, 0, self.rendertarget_width, self.rendertarget_height)

            # gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            # if gl_error != GL_FRAMEBUFFER_COMPLETE:
            #     logger.error("glCheckFramebufferStatus error %d." % gl_error)

        if depthtexture:
            depthtexture.attach(GL_DEPTH_STENCIL_ATTACHMENT)

        if clear:
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def end(self):
        # Set up to read from the renderbuffer and draw to window-system framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)  # the default framebuffer active
        # glViewport(0, 0, self.width, self.height)
        # glClearColor(0.0, 0.0, 0.0, 1.0)
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glBlitFramebuffer(0, 0, self.rendertarget_width, self.rendertarget_height,
                          0, 0, self.framebuffer_width, self.framebuffer_height,
                          GL_COLOR_BUFFER_BIT, GL_NEAREST)
