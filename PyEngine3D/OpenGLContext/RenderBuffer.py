from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from PyEngine3D.Common import logger
from PyEngine3D.Utilities import GetClassName
from .Texture import Texture


class RenderBuffer(Texture):
    target = GL_RENDERBUFFER

    def __init__(self, **datas):
        Texture.__init__(self, **datas)

    def create_texture(self, **datas):
        if self.buffer != -1:
            self.delete()

        self.multisample_count = datas.get('multisample_count', 0)

        self.buffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.buffer)
        if self.multisample_count == 0:
            glRenderbufferStorage(GL_RENDERBUFFER, self.internal_format, self.width, self.height)
        else:
            glRenderbufferStorageMultisample(GL_RENDERBUFFER, self.multisample_count, self.internal_format, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    def delete(self):
        logger.info("Delete %s : %s" % (GetClassName(self), self.name))
        glDeleteRenderbuffers(1, [self.buffer, ])
        self.buffer = -1

    def bind_render_buffer(self):
        glBindRenderbuffer(GL_RENDERBUFFER, self.buffer)

    def bind_texture(self, wrap=None):
        logger.error('%s RenderBuffer cannot use bind_texture method.' % self.name)
