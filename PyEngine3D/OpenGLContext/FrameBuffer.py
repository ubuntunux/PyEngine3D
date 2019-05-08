from functools import partial

from OpenGL.GL import *

from PyEngine3D.Utilities import GetClassName, Singleton
from PyEngine3D.Common import logger
from PyEngine3D.OpenGLContext import OpenGLContext


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

    def __init__(self, name=''):
        logger.info("Create %s framebuffer" % name)
        self.name = name
        self.buffer = None
        self.max_draw_buffers = glGetInteger(GL_MAX_DRAW_BUFFERS)
        self.color_textures = [None, ] * self.max_draw_buffers
        self.attach_count = 0
        self.attachments = [0, ] * self.max_draw_buffers
        self.depth_texture = None
        self.width = 0
        self.height = 0
        self.viewport_width = 0
        self.viewport_height = 0
        self.viewport_scale = 1.0
        self.target_face = GL_TEXTURE_CUBE_MAP_POSITIVE_X  # cubemap face
        self.target_layer = 0  # 3d texture layer
        self.target_level = 0  # mipmap level

    def __del__(self):
        self.set_color_textures()
        self.set_depth_texture(None)

    def get_error(self, error_code):
        for error in self.errors:
            if error == error_code:
                return str(error)

    def delete(self):
        logger.info("Delete %s framebuffer" % self.name)
        self.set_color_textures()
        self.set_depth_texture(None)
        glDeleteFramebuffers(1, [self.buffer, ])

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

    def set_viewport(self, x, y, width, height, scale):
        self.width = width
        self.height = height
        self.viewport_width = max(1, int(width * scale))
        self.viewport_height = max(1, int(height * scale))
        self.viewport_scale = scale
        glViewport(x, y, self.viewport_width, self.viewport_height)

    def attachment_framebuffer(self, attachment, target, texture_buffer, offset=0):
        if GL_RENDERBUFFER == target:
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, attachment, GL_RENDERBUFFER, texture_buffer)
        elif GL_TEXTURE_2D == target:
            glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, texture_buffer, self.target_level)
        elif GL_TEXTURE_2D_ARRAY == target:
            glFramebufferTextureLayer(GL_FRAMEBUFFER, attachment, texture_buffer, 0, self.target_layer + offset)
        elif GL_TEXTURE_3D == target:
            glFramebufferTexture3D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_3D, texture_buffer, self.target_level, self.target_layer + offset)
        elif GL_TEXTURE_CUBE_MAP == target:
            glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, self.target_face, texture_buffer, self.target_level)

    def generate_framebuffer(self, target_face=GL_TEXTURE_CUBE_MAP_POSITIVE_X, target_layer=0, target_level=0):
        if self.buffer is None:
            self.buffer = glGenFramebuffers(1)

        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer)

        self.target_face = target_face
        self.target_layer = target_layer
        self.target_level = target_level

        # bind color textures
        layer_offset = 0
        last_texture = None
        for i, color_texture in enumerate(self.color_textures):
            if last_texture != color_texture:
                layer_offset = 0
                last_texture = color_texture
            else:
                layer_offset += 1

            if color_texture is not None:
                self.attachment_framebuffer(GL_COLOR_ATTACHMENT0 + i, color_texture.target, color_texture.buffer, layer_offset)

        if self.attach_count > 0:
            glDrawBuffers(self.attach_count, self.attachments)
        else:
            glDrawBuffer(GL_NONE)
            glReadBuffer(GL_NONE)

        # bind depth texture
        if self.depth_texture is not None:
            attachment = OpenGLContext.get_depth_attachment(self.depth_texture.internal_format)
            self.attachment_framebuffer(attachment, self.depth_texture.target, self.depth_texture.buffer)
        else:
            glFramebufferTexture(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, 0, 0)

        gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if gl_error != GL_FRAMEBUFFER_COMPLETE:
            error_message = "glCheckFramebufferStatus error %s." % self.get_error(gl_error)
            logger.error(error_message)
            raise BaseException(error_message)

    def bind_framebuffer(self):
        viewport_scale = 1.0 / (2.0 ** self.target_level)
        if self.attach_count > 0:
            self.set_viewport(0, 0, self.color_textures[0].width, self.color_textures[0].height, viewport_scale)
        elif self.depth_texture is not None:
            self.set_viewport(0, 0, self.depth_texture.width, self.depth_texture.height, viewport_scale)

        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer)

    def unbind_framebuffer(self):
        self.set_color_textures()
        self.set_depth_texture(None)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def copy_framebuffer(self, src, src_x=0, src_y=0, src_w=0, src_h=0, dst_x=0, dst_y=0, dst_w=0, dst_h=0, target=GL_COLOR_BUFFER_BIT, filter_type=GL_LINEAR):
        glBindFramebuffer(GL_READ_FRAMEBUFFER, src.buffer)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.buffer)

        if GL_COLOR_BUFFER_BIT == target:
            glDrawBuffers(1, (GL_COLOR_ATTACHMENT0,))
            glReadBuffer(GL_COLOR_ATTACHMENT0)
        elif GL_DEPTH_BUFFER_BIT == target and src.depth_texture is not None:
            attachment = OpenGLContext.get_depth_attachment(src.depth_texture.internal_format)
            glDrawBuffers(1, (attachment, ))
            glReadBuffer(attachment)

        glBlitFramebuffer(src_x, src_y, src_w or src.viewport_width, src_h or src.viewport_height,
                          dst_x, dst_y, dst_w or self.viewport_width, dst_h or self.viewport_height,
                          target, filter_type)

    def mirror_framebuffer(self, src, src_x=0, src_y=0, src_w=0, src_h=0, dst_x=0, dst_y=0, dst_w=0, dst_h=0, target=GL_COLOR_BUFFER_BIT, filter_type=GL_LINEAR):
        glBindFramebuffer(GL_READ_FRAMEBUFFER, src.buffer)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.buffer)

        if GL_COLOR_BUFFER_BIT == target:
            glDrawBuffers(1, (GL_COLOR_ATTACHMENT0,))
            glReadBuffer(GL_COLOR_ATTACHMENT0)
        elif GL_DEPTH_BUFFER_BIT == target and src.depth_texture is not None:
            attachment = OpenGLContext.get_depth_attachment(src.depth_texture.internal_format)
            glDrawBuffers(1, (attachment, ))
            glReadBuffer(attachment)

        glBlitFramebuffer(src_w or src.viewport_width, src_y, src_x, src_h or src.viewport_height,
                          dst_x, dst_y, dst_w or self.viewport_width, dst_h or self.viewport_height,
                          target, filter_type)

    def blit_framebuffer(self, src_x=0, src_y=0, src_w=0, src_h=0, dst_x=0, dst_y=0, dst_w=0, dst_h=0, filter_type=GL_LINEAR):
        # active default frame buffer
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glBlitFramebuffer(src_x, src_y, src_w or self.viewport_width, src_h or self.viewport_height,
                          dst_x, dst_y, dst_w or self.viewport_width, dst_h or self.viewport_height,
                          GL_COLOR_BUFFER_BIT, filter_type)


class FrameBufferManager(Singleton):
    def __init__(self):
        self.framebuffers = {}
        self.current_framebuffer = None

    def clear_framebuffer(self):
        for framebuffer in self.framebuffers.values():
            framebuffer.delete()
        self.framebuffers = {}
        self.current_framebuffer = None

    def rebuild_command(self):
        for framebuffer in self.framebuffers.values():
            framebuffer.build_command()

    def delete_framebuffer(self, *textures, depth_texture):
        key = (textures, depth_texture)
        if key in self.framebuffers:
            framebuffer = self.framebuffers.pop(key)
            framebuffer.delete()

    def get_framebuffer(self, *textures, depth_texture=None, target_face=GL_TEXTURE_CUBE_MAP_POSITIVE_X, target_layer=0, target_level=0):
        key = (textures, depth_texture, target_face, target_layer, target_level)
        if key in self.framebuffers:
            framebuffer = self.framebuffers[key]
        else:
            name = ''
            if 0 < len(textures):
                name = textures[0].name
                error = False
                width = textures[0].width
                height = textures[0].height

                for texture in textures[1:]:
                    if texture is not None and (width != texture.width or height != texture.height):
                        error = True
                        break

                if depth_texture is not None and (width != depth_texture.width or height != depth_texture.height):
                    error = True

                if error:
                    error_message = "Render targets must be the same size."
                    logger.error(error_message)
                    raise BaseException(error_message)

            framebuffer = FrameBuffer(name)
            self.framebuffers[key] = framebuffer
            framebuffer.set_color_textures(*textures)
            framebuffer.set_depth_texture(depth_texture)
            framebuffer.generate_framebuffer(target_face=target_face, target_layer=target_layer, target_level=target_level)
        return framebuffer

    def bind_framebuffer(self, *textures, depth_texture=None, target_face=GL_TEXTURE_CUBE_MAP_POSITIVE_X, target_layer=0, target_level=0):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.current_framebuffer = self.get_framebuffer(*textures, depth_texture=depth_texture, target_face=target_face, target_layer=target_layer, target_level=target_level)
        self.current_framebuffer.bind_framebuffer()
        return self.current_framebuffer

    def unbind_framebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def copy_rendertarget(self, src_render_target, dst_render_target,
                           src_x=0, src_y=0, src_w=0, src_h=0,
                           dst_x=0, dst_y=0, dst_w=0, dst_h=0, target=GL_COLOR_BUFFER_BIT, filter_type=GL_LINEAR):
        src_framebuffer = self.bind_framebuffer(src_render_target)
        self.bind_framebuffer(dst_render_target)
        glClear(GL_COLOR_BUFFER_BIT)
        self.current_framebuffer.copy_framebuffer(src_framebuffer, src_x, src_y, src_w, src_h, dst_x, dst_y, dst_w, dst_h, target, filter_type)

    def copy_framebuffer(self, src, src_x=0, src_y=0, src_w=0, src_h=0, dst_x=0, dst_y=0, dst_w=0, dst_h=0, target=GL_COLOR_BUFFER_BIT, filter_type=GL_LINEAR):
        self.current_framebuffer.copy_framebuffer(src, src_x, src_y, src_w, src_h, dst_x, dst_y, dst_w, dst_h, target, filter_type)

    def mirror_framebuffer(self, src, src_x=0, src_y=0, src_w=0, src_h=0, dst_x=0, dst_y=0, dst_w=0, dst_h=0, target=GL_COLOR_BUFFER_BIT, filter_type=GL_LINEAR):
        self.current_framebuffer.mirror_framebuffer(src, src_x, src_y, src_w, src_h, dst_x, dst_y, dst_w, dst_h, target, filter_type)

    def blit_framebuffer(self, src_x=0, src_y=0, src_w=0, src_h=0, dst_x=0, dst_y=0, dst_w=0, dst_h=0, filter_type=GL_LINEAR):
        self.current_framebuffer.blit_framebuffer(src_x, src_y, src_w, src_h, dst_x, dst_y, dst_w, dst_h, filter_type)
