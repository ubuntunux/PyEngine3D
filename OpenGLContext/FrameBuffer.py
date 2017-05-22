from OpenGL.GL import *

from Utilities import GetClassName
from Common import logger


class FrameBuffer:
    def __init__(self, width, height):
        logger.info("Create " + GetClassName(self))
        self.rendertarget_width = width
        self.rendertarget_height = height
        self.buffer = glGenFramebuffers(1)

    def delete(self):
        glDeleteFramebuffers(self.buffer)

    def bind_framebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer)

    def unbind_framebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def attach_texture(self, texture, attachment=GL_COLOR_ATTACHMENT0):
        """
        :param colortexture: Texture2D
        """
        glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, texture.buffer, 0)

    def attach_renderbuffer(self, renderBuffer, attachment=GL_COLOR_ATTACHMENT0):
        """
        :param colortexture: RenderBuffer
        """
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, attachment, GL_RENDERBUFFER, renderBuffer.buffer)

    def bind_rendertarget(self, colortexture, clear_color, depthtexture, clear_depth):
        """
        :param colortexture: Texture2D
        :param clear_color: Bool
        :param depthtexture: Texture2D
        :param clear_depth: Bool
        :return: None
        """
        clear_flag = 0
        if colortexture:
            if clear_color:
                clear_flag |= GL_COLOR_BUFFER_BIT
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, colortexture.buffer, 0)
            self.rendertarget_width = colortexture.width
            self.rendertarget_height = colortexture.height
            glViewport(0, 0, self.rendertarget_width, self.rendertarget_height)

            # gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            # if gl_error != GL_FRAMEBUFFER_COMPLETE:
            #     logger.error("glCheckFramebufferStatus error %d." % gl_error)

        if depthtexture:
            if clear_depth:
                clear_flag |= GL_DEPTH_BUFFER_BIT
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_TEXTURE_2D, depthtexture.buffer, 0)

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
