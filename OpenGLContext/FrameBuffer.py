from OpenGL.GL import *

from Utilities import GetClassName
from Common import logger

from .RenderBuffer import RenderBuffer

class FrameBuffer:
    def __init__(self):
        logger.info("Create " + GetClassName(self))
        self.buffer = glGenFramebuffers(1)
        self.max_draw_buffers = glGetInteger(GL_MAX_DRAW_BUFFERS)
        self.color_textures = [None, ] * self.max_draw_buffers
        self.attachments = [0, ] * self.max_draw_buffers
        self.depth_texture = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

    def delete(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glDeleteFramebuffers(1, [self.buffer, ])

    def clear(self, clear_flag=GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT, clear_color=(0.0, 0.0, 0.0, 1.0)):
        glClearColor(*clear_color)
        glClear(clear_flag)

    def set_viewport(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        glViewport(x, y, width, height)

    def set_color_texture(self, texture):
        self.set_color_textures([texture, ])

    def set_color_textures(self, textures):
        """
        :param textures: [Texture2D, ]
        """
        texture_count = len(textures)
        for i in range(len(self.color_textures)):
            if self.color_textures[i]:
                self.color_textures[i].set_attachment(False)

            if i < texture_count:
                if textures[i]:
                    textures[i].set_attachment(True)
                self.color_textures[i] = textures[i]
            else:
                self.color_textures[i] = None

    def set_depth_texture(self, texture):
        """
        :param texture: Texture2D
        """
        if self.depth_texture:
            self.depth_texture.set_attachment(False)

        if texture:
            texture.set_attachment(True)
        self.depth_texture = texture

    def bind_framebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer)

        # bind color textures
        attach_count = 0
        for i, color_texture in enumerate(self.color_textures):
            attachment = GL_COLOR_ATTACHMENT0 + i
            if color_texture:
                attach_count += 1
                self.attachments[i] = attachment
                if type(color_texture) == RenderBuffer:
                    glFramebufferRenderbuffer(GL_FRAMEBUFFER, attachment, GL_RENDERBUFFER, color_texture.buffer)
                else:
                    glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, color_texture.target, color_texture.buffer, 0)
                # just for single render target.
                # glDrawBuffer(attachment)
                glReadBuffer(attachment)
            else:
                self.attachments[i] = 0
                glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, 0, 0)

        if attach_count > 0:
            # Specifies a list of color buffers to be drawn into
            glDrawBuffers(attach_count, self.attachments)
        else:
            # Important - We need to explicitly tell OpenGL we're not going to render any color data.
            glDrawBuffer(GL_NONE)
            glReadBuffer(GL_NONE)

        # bind depth texture
        if self.depth_texture:
            if self.depth_texture.internal_format in (GL_DEPTH_STENCIL, GL_DEPTH24_STENCIL8, GL_DEPTH32F_STENCIL8):
                attachment = GL_DEPTH_STENCIL_ATTACHMENT
            else:
                attachment = GL_DEPTH_ATTACHMENT
            if type(self.depth_texture) == RenderBuffer:
                glFramebufferRenderbuffer(GL_FRAMEBUFFER, attachment, GL_RENDERBUFFER, self.depth_texture.buffer)
            else:
                glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, self.depth_texture.target, self.depth_texture.buffer, 0)
        else:
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_TEXTURE_2D, 0, 0)

        # set viewport
        if attach_count > 0:
            self.set_viewport(0, 0, self.color_textures[0].width, self.color_textures[0].height)
        elif self.depth_texture:
            # Set viewport if there isn't any color texture.
            self.set_viewport(0, 0, self.depth_texture.width, self.depth_texture.height)

        gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if gl_error != GL_FRAMEBUFFER_COMPLETE:
            logger.error("glCheckFramebufferStatus error %d." % gl_error)

    def unbind_framebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def blit_framebuffer(self, rendertarget, framebuffer_width, framebuffer_height):
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)  # the default framebuffer active
        # glBindFramebuffer(GL_READ_FRAMEBUFFER, rendertarget.buffer)
        # glDrawBuffer(GL_BACK)
        # glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        # glViewport(0, 0, self.width, self.height)
        # glClearColor(0.0, 0.0, 0.0, 1.0)
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glBlitFramebuffer(0, 0, rendertarget.width, rendertarget.height,
                          0, 0, framebuffer_width, framebuffer_height,
                          GL_COLOR_BUFFER_BIT, GL_NEAREST)
