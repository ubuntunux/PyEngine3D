from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Core import logger


# Use Texture2D intead of RenderBuffer.
class RenderBuffer:
    """
    RenderBuffer is fater than Texture2D, but it's read-only.
    """
    def __init__(self, texture_name, width, height, internal_format=GL_RGBA):
        logger.info("Create " + GetClassName(self) + " : " + texture_name)
        self.name = texture_name
        self.width = width
        self.height = height
        self.internal_format = internal_format  # GL_RGBA, GL_DEPTH_COMPONENT32, GL_DEPTH24_STENCIL8

        self.buffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.buffer)
        glRenderbufferStorage(GL_RENDERBUFFER, internal_format, width, height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)
