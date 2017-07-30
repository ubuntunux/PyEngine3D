from OpenGL.GL import *

from Utilities import GetClassName
from Common import logger


class FrameBuffer:
    def __init__(self):
        logger.info("Create " + GetClassName(self))
        self.buffer = glGenFramebuffers(1)
        self.max_draw_buffers = glGetInteger(GL_MAX_DRAW_BUFFERS)
        self.color_textures = [None, ] * self.max_draw_buffers
        self.attachments = [0, ] * self.max_draw_buffers
        self.clear_color = None
        self.depth_texture = None
        self.clear_depth = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

    def delete(self):
        glDeleteFramebuffers(self.buffer)

    def clear(self):
        self.set_color_texture(None)
        self.set_depth_texture(None)

    def set_viewport(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        glViewport(x, y, width, height)

    def set_color_texture(self, texture, clear_color=None):
        for i in range(len(self.color_textures)):
            if self.color_textures[i]:
                self.color_textures[i].set_attachment(False)

            if i == 0:
                if texture:
                    texture.set_attachment(True)
                self.color_textures[i] = texture
            else:
                self.color_textures[i] = None
        self.clear_color = clear_color

    def set_color_textures(self, textures, clear_color=None):
        """
        :param textures: [Texture2D, ]
        :param clear_color: None or 4 Color Tuple
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
        self.clear_color = clear_color

    def set_depth_texture(self, texture, clear_color=None):
        """
        :param texture: Texture2D
        :param clear_color: None or 4 Color Tuple
        """
        if self.depth_texture:
            self.depth_texture.set_attachment(False)

        if texture:
            texture.set_attachment(True)
        self.depth_texture = texture
        self.clear_depth = clear_color

    def bind_framebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer)
        # bind color textures
        attach_count = 0
        for i, color_texture in enumerate(self.color_textures):
            attachment = GL_COLOR_ATTACHMENT0 + i
            if color_texture:
                attach_count += 1
                self.attachments[i] = attachment
                glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, color_texture.buffer, 0)
                # just for single render target.
                # glDrawBuffer(attachment)
                glReadBuffer(attachment)
            else:
                self.attachments[i] = 0
                glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, 0, 0)
        # Specifies a list of color buffers to be drawn into
        glDrawBuffers(attach_count, self.attachments)

        if self.color_textures[0]:
            self.set_viewport(0, 0, self.color_textures[0].width, self.color_textures[0].height)

            if self.clear_color:
                glClearColor(*self.clear_color)
                glClear(GL_COLOR_BUFFER_BIT)
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

            glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, self.depth_texture.buffer, 0)

            # Set viewport if there isn't any color texture.
            if not self.color_textures[0]:
                self.set_viewport(0, 0, self.depth_texture.width, self.depth_texture.height)

            if self.clear_depth:
                glClearColor(*self.clear_depth)
                glClear(GL_DEPTH_BUFFER_BIT)
        else:
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_TEXTURE_2D, 0, 0);

        gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if gl_error != GL_FRAMEBUFFER_COMPLETE:
            logger.error("glCheckFramebufferStatus error %d." % gl_error)

    def unbind_framebuffer(self):
        self.clear()
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def blit_framebuffer(self, framebuffer_width, framebuffer_height):
        self.clear()
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)  # the default framebuffer active
        # glViewport(0, 0, self.width, self.height)
        # glClearColor(0.0, 0.0, 0.0, 1.0)
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glBlitFramebuffer(self.x, self.y, self.width, self.height,
                          0, 0, framebuffer_width, framebuffer_height,
                          GL_COLOR_BUFFER_BIT, GL_NEAREST)
