from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *

from ..Common import logger
from ..Utilities import GetClassName
from .Texture import Texture


class RenderBuffer(Texture):
    target = GL_RENDERBUFFER

    def __init__(self, name, datas):
        Texture.__init__(self, name=name, **datas.get_dict())

        self.multisample_count = datas.multisample_count or 0

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

    def bind_texture(self):
        logger.error('%s RenderBuffer cannot use bind_texture method.' % self.name)
