from functools import partial

from OpenGL.GL import *

from Utilities import GetClassName
from Common import logger

from .RenderBuffer import RenderBuffer


class FrameBuffer:
    errors = (
        GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT,
        GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER,
        GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT,
        GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE,
        GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER,
        GL_FRAMEBUFFER_UNDEFINED,
        GL_FRAMEBUFFER_UNSUPPORTED
    )

    def __init__(self):
        logger.info("Create " + GetClassName(self))
        self.buffer = glGenFramebuffers(1)
        self.max_draw_buffers = glGetInteger(GL_MAX_DRAW_BUFFERS)
        self.color_textures = [None, ] * self.max_draw_buffers
        self.attach_count = 0
        self.attachments = [0, ] * self.max_draw_buffers
        self.depth_texture = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.commands = []

    def __del__(self):
        self.set_color_textures()
        self.set_depth_texture(None)
        # glBindFramebuffer(GL_FRAMEBUFFER, 0)
        # glDeleteFramebuffers(1, [self.buffer, ])

    def clear(self, clear_flag=GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT, clear_color=(0.0, 0.0, 0.0, 1.0)):
        glClearColor(*clear_color)
        glClear(clear_flag)

    def set_viewport(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        glViewport(x, y, width, height)

    def set_color_textures(self, *textures):
        texture_count = len(textures)
        self.attach_count = 0
        for i, color_texture in enumerate(self.color_textures):
            if color_texture:
                color_texture.set_attachment(False)

            texture = textures[i] if i < texture_count else None

            if texture is None:
                self.attachments[i] = 0
                self.color_textures[i] = None
            else:
                self.attach_count += 1
                self.attachments[i] = GL_COLOR_ATTACHMENT0 + i
                self.color_textures[i] = texture
                texture.set_attachment(True)

    def set_depth_texture(self, texture):
        if self.depth_texture:
            self.depth_texture.set_attachment(False)

        if texture:
            texture.set_attachment(True)
        self.depth_texture = texture

    def add_command(self, *args):
        self.commands.append(partial(*args))

    def build_command(self):
        self.add_command(glBindFramebuffer, GL_FRAMEBUFFER, self.buffer)

        # bind color textures
        for i, color_texture in enumerate(self.color_textures):
            if color_texture:
                attachment = GL_COLOR_ATTACHMENT0 + i
                if type(color_texture) == RenderBuffer:
                    self.add_command(glFramebufferRenderbuffer, GL_FRAMEBUFFER, attachment, GL_RENDERBUFFER,
                                     color_texture.buffer)
                else:
                    self.add_command(glFramebufferTexture2D, GL_FRAMEBUFFER, attachment, color_texture.target,
                                     color_texture.buffer, 0)
                # just for single render target.
                # self.add_command(glDrawBuffer, attachment)
                # important
                self.add_command(glReadBuffer, attachment)
            else:
                glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, 0, 0)

        if self.attach_count > 0:
            # Specifies a list of color buffers to be drawn into
            self.add_command(glDrawBuffers, self.attach_count, self.attachments)
        else:
            # Important - We need to explicitly tell OpenGL we're not going to render any color data.
            self.add_command(glDrawBuffer, GL_NONE)
            self.add_command(glReadBuffer, GL_NONE)

        # bind depth texture
        if self.depth_texture:
            if self.depth_texture.internal_format in (GL_DEPTH_STENCIL, GL_DEPTH24_STENCIL8, GL_DEPTH32F_STENCIL8):
                attachment = GL_DEPTH_STENCIL_ATTACHMENT
            else:
                attachment = GL_DEPTH_ATTACHMENT
            if type(self.depth_texture) == RenderBuffer:
                self.add_command(glFramebufferRenderbuffer, GL_FRAMEBUFFER, attachment, GL_RENDERBUFFER,
                                 self.depth_texture.buffer)
            else:
                self.add_command(glFramebufferTexture2D, GL_FRAMEBUFFER, attachment, self.depth_texture.target,
                                 self.depth_texture.buffer, 0)
        else:
            self.add_command(glFramebufferTexture2D, GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_TEXTURE_2D, 0, 0)

    def run_bind_framebuffer_command(self):
        for cmd in self.commands:
            cmd()

        # set viewport
        if self.attach_count > 0:
            self.set_viewport(0, 0, self.color_textures[0].width, self.color_textures[0].height)
        elif self.depth_texture:
            # Set viewport if there isn't any color texture.
            self.set_viewport(0, 0, self.depth_texture.width, self.depth_texture.height)

        gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if gl_error != GL_FRAMEBUFFER_COMPLETE:
            error_message = "glCheckFramebufferStatus error %s." % self.get_error(gl_error)
            logger.error(error_message)
            raise BaseException(error_message)

    def bind_framebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer)

        # bind color textures
        for i, color_texture in enumerate(self.color_textures):
            attachment = GL_COLOR_ATTACHMENT0 + i
            if color_texture:
                if type(color_texture) == RenderBuffer:
                    glFramebufferRenderbuffer(GL_FRAMEBUFFER, attachment, GL_RENDERBUFFER, color_texture.buffer)
                else:
                    glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, color_texture.target, color_texture.buffer, 0)
                # just for single render target.
                # glDrawBuffer(attachment)
                # important
                glReadBuffer(attachment)
            else:
                glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, 0, 0)

        if self.attach_count > 0:
            # Specifies a list of color buffers to be drawn into
            glDrawBuffers(self.attach_count, self.attachments)
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
        if self.attach_count > 0:
            self.set_viewport(0, 0, self.color_textures[0].width, self.color_textures[0].height)
        elif self.depth_texture:
            # Set viewport if there isn't any color texture.
            self.set_viewport(0, 0, self.depth_texture.width, self.depth_texture.height)

        gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if gl_error != GL_FRAMEBUFFER_COMPLETE:
            error_message = "glCheckFramebufferStatus error %s." % self.get_error(gl_error)
            logger.error(error_message)
            raise BaseException(error_message)

    def get_error(self, error_code):
        for error in self.errors:
            if error == error_code:
                return str(error)

    def unbind_framebuffer(self):
        self.set_color_textures()
        self.set_depth_texture(None)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def copy_framebuffer(self, src, target=GL_COLOR_BUFFER_BIT, filter_type=GL_LINEAR):
        glBindFramebuffer(GL_READ_FRAMEBUFFER, src.buffer)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.buffer)
        glBlitFramebuffer(0, 0, src.width, src.height, 0, 0, self.width, self.height, target, filter_type)

    def blit_framebuffer(self, window_width, window_height, filter_type=GL_LINEAR):
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)  # the default framebuffer active
        glBlitFramebuffer(0, 0, self.width, self.height,
                          0, 0, window_width, window_height,
                          GL_COLOR_BUFFER_BIT, filter_type)


class FrameBufferManager:
    def __init__(self):
        self.framebuffers = {}
        self.current_framebuffer = None

    def clear(self):
        for framebuffer in self.framebuffers:
            framebuffer.__del__()
        self.framebuffers = {}
        self.current_framebuffer = None

    def get_framebuffer(self, *textures, depth_texture=None):
        key = (textures, depth_texture)
        if key in self.framebuffers:
            framebuffer = self.framebuffers[key]
        else:
            framebuffer = FrameBuffer()
            self.framebuffers[key] = framebuffer
            framebuffer.set_color_textures(*textures)
            framebuffer.set_depth_texture(depth_texture)
            framebuffer.build_command()
        return framebuffer

    def bind_framebuffer(self, *textures, depth_texture=None):
        self.current_framebuffer = self.get_framebuffer(*textures, depth_texture)
        self.current_framebuffer.run_bind_framebuffer_command()
        return self.current_framebuffer
