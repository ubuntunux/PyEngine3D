from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Common import logger
from Utilities import GetClassName


class RenderBuffer:
    target = GL_RENDERBUFFER

    def __init__(self, name, **datas):
        logger.info("Create " + GetClassName(self) + " : " + name)
        self.name = name
        self.width = datas.get('width', 1024)
        self.height = datas.get('height', 1024)
        # GL_RGBA, GL_DEPTH_COMPONENT32, GL_DEPTH24_STENCIL8
        self.internal_format = datas.get('internal_format', GL_RGBA)
        self.mutlisamples = datas.get('multisamples', 0)
        self.attachment = False
        self.using = False

        self.buffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.buffer)
        if self.mutlisamples == 0:
            glRenderbufferStorage(GL_RENDERBUFFER, self.internal_format, self.width, self.height)
        else:
            glRenderbufferStorageMultisample(GL_RENDERBUFFER, self.mutlisamples, self.internal_format, self.width,
                                             self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    def bind_render_buffer(self):
        glBindRenderbuffer(GL_RENDERBUFFER, self.buffer)

    def is_attached(self):
        return self.attachment

    def set_attachment(self, attachment):
        self.attachment = attachment
