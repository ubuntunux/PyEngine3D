from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Utilities import Singleton, GetClassName, Attributes,AutoEnum
from Common import logger
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
        logger.info("initialize " + GetClassName(self))
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
