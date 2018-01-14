import gc
from ctypes import c_void_p
import itertools

from OpenGL.GL import *

from Common import logger
from Utilities import Singleton, GetClassName, Attributes


def get_internal_format(str_image_mode):
    if str_image_mode == "RGB":
        return GL_RGB
    elif str_image_mode == "RGBA":
        return GL_RGBA
    else:
        logger.error("get_internal_format::unknown image mode ( %s )" % str_image_mode)
    return GL_RGBA


def get_texture_format(str_image_mode):
    if str_image_mode == "RGB":
        return GL_RGB
    elif str_image_mode == "RGBA":
        # R,G,B,A order. GL_BGRA is faster than GL_RGBA
        return GL_RGBA  # GL_BGRA
    else:
        logger.error("get_texture_format::unknown image mode ( %s )" % str_image_mode)
    return GL_RGBA


def get_image_mode(texture_internal_format):
    if texture_internal_format in (GL_RGB, GL_BGR):
        return "RGB"
    elif texture_internal_format in (GL_RGBA, GL_BGRA):
        return "RGBA"
    elif texture_internal_format in (GL_RED, GL_DEPTH_STENCIL, GL_DEPTH_COMPONENT):
        return "R"
    elif texture_internal_format == GL_RG:
        return "RG"
    else:
        logger.error("get_image_mode::unknown image format ( %s )" % texture_internal_format)
    return "RGBA"


def CreateTexture(**texture_datas):
    texture_class = texture_datas.get('texture_type', Texture2D)
    if texture_class is not None:
        return texture_class(**texture_datas)
    return None


class Texture:
    target = GL_TEXTURE_2D
    default_wrap = GL_REPEAT

    def __init__(self, **texture_data):
        self.name = texture_data.get('name')
        self.attachment = False
        self.image_mode = texture_data.get('image_mode')
        self.internal_format = texture_data.get('internal_format')
        self.texture_format = texture_data.get('texture_format')
        self.sRGB = texture_data.get('sRGB', None)
        self.multisample_count = 0

        if self.internal_format is None and self.image_mode:
            self.internal_format = get_internal_format(self.image_mode)
        if self.texture_format is None and self.image_mode:
            self.texture_format = get_texture_format(self.image_mode)
        if self.image_mode is None and self.texture_format:
            self.image_mode = get_image_mode(self.texture_format)

        # Convert to sRGB
        if self.sRGB:
            if self.internal_format == GL_RGB:
                self.internal_format = GL_SRGB
            elif self.internal_format == GL_RGBA:
                self.internal_format = GL_SRGB_ALPHA

        self.width = texture_data.get('width', 0)
        self.height = texture_data.get('height', 0)
        self.depth = max(1, texture_data.get('depth', 1))
        self.data_type = texture_data.get('data_type', GL_UNSIGNED_BYTE)
        self.min_filter = texture_data.get('min_filter', GL_LINEAR_MIPMAP_LINEAR)
        self.mag_filter = texture_data.get('mag_filter', GL_LINEAR)  # GL_LINEAR_MIPMAP_LINEAR, GL_LINEAR, GL_NEAREST

        mipmap_filters = (GL_LINEAR_MIPMAP_LINEAR, GL_LINEAR_MIPMAP_NEAREST,
                          GL_NEAREST_MIPMAP_LINEAR, GL_NEAREST_MIPMAP_NEAREST)
        self.enable_mipmap = self.min_filter in mipmap_filters
        if self.target == GL_TEXTURE_2D_MULTISAMPLE:
            self.enable_mipmap = False

        self.wrap = texture_data.get('wrap', self.default_wrap)  # GL_REPEAT, GL_CLAMP
        self.buffer = None

        logger.info("Create %s : %s %dx%dx%d %s mipmap(%s)." % (
            GetClassName(self), self.name, self.width, self.height, self.depth, str(self.internal_format),
            'Enable' if self.enable_mipmap else 'Disable'))

        self.attribute = Attributes()

    def __del__(self):
        pass

    def delete(self):
        logger.info("Delete %s : %s" % (GetClassName(self), self.name))
        glDeleteTextures([self.buffer, ])
        self.buffer = -1

    def get_save_data(self, get_image_data=True):
        save_data = dict(
            texture_type=self.__class__,
            width=self.width,
            height=self.height,
            depth=self.depth,
            image_mode=self.image_mode,
            internal_format=self.internal_format,
            texture_format=self.texture_format,
            data_type=self.data_type,
            min_filter=self.min_filter,
            mag_filter=self.mag_filter,
            wrap=self.wrap
        )

        if get_image_data:
            data = self.get_image_data()
            if data is not None:
                save_data['data'] = data
        return save_data

    def get_image_data(self):
        if self.target not in (GL_TEXTURE_2D, GL_TEXTURE_3D) or self.texture_format not in (GL_RGB, GL_RGBA):
            return None

        if GL_TEXTURE_2D == self.target:
            glBindTexture(self.target, self.buffer)
            data = glGetTexImage(self.target, 0, self.texture_format, self.data_type)
            glBindTexture(self.target, 0)
            return data
        elif GL_TEXTURE_3D == self.target:
            glBindTexture(self.target, self.buffer)
            fb = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, fb)

            data = []
            for layer in range(self.depth):
                glFramebufferTexture3D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_3D, self.buffer, 0, layer)
                glReadBuffer(GL_COLOR_ATTACHMENT0)
                pixels = glReadPixels(0, 0, self.width, self.height, self.texture_format, self.data_type)
                # Note : pixels is numpy.ndarray
                data.append(pixels.tolist())
            # list concatenate
            data = list(itertools.chain(*data))
            glBindTexture(self.target, 0)
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glDeleteFramebuffers(1, [fb, ])
        return data

    def generate_mipmap(self):
        if self.enable_mipmap:
            glBindTexture(self.target, self.buffer)
            glGenerateMipmap(self.target)
        else:
            logger.warn('%s disable to generate mipmap.' % self.name)

    def bind_texture(self):
        if self.buffer == -1:
            logger.warn("%s texture is invalid." % self.name)
            return
        glBindTexture(self.target, self.buffer)
        # if self.attachment:
        #     error_msg = "%s can not bind to a texture because it is attached to a frame buffer.." % self.name
        #     logger.error(error_msg)
        #     raise BaseException(error_msg)

    def is_attached(self):
        return self.attachment

    def set_attachment(self, attachment):
        self.attachment = attachment

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        self.attribute.setAttribute("target", self.target)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        self.attribute.setAttribute("depth", self.depth)
        self.attribute.setAttribute("image_mode", self.image_mode)
        self.attribute.setAttribute("internal_format", self.internal_format)
        self.attribute.setAttribute("texture_format", self.texture_format)
        self.attribute.setAttribute("data_type", self.data_type)
        self.attribute.setAttribute("min_filter", self.min_filter)
        self.attribute.setAttribute("mag_filter", self.mag_filter)
        self.attribute.setAttribute("multisample_count", self.multisample_count)
        self.attribute.setAttribute("wrap", self.wrap)
        return self.attribute


class Texture2D(Texture):
    target = GL_TEXTURE_2D

    def __init__(self, **texture_data):
        Texture.__init__(self, **texture_data)

        data = texture_data.get('data', c_void_p(0))

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.buffer)
        glTexImage2D(GL_TEXTURE_2D,
                     0,
                     self.internal_format,
                     self.width,
                     self.height,
                     0,
                     self.texture_format,
                     self.data_type,
                     data)

        if self.enable_mipmap:
            glGenerateMipmap(GL_TEXTURE_2D)
            # create indivisual mipmapThis creates a texture with a single mipmap level.
            # You will also need separate glTexSubImage2D calls to upload each mipmap
            # glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, width, height)
            # glTexSubImage2D(GL_TEXTURE_2D, 0​, 0, 0, width​, height​, GL_BGRA, GL_UNSIGNED_BYTE, pixels)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, self.wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, self.wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glBindTexture(GL_TEXTURE_2D, 0)


class Texture3D(Texture):
    target = GL_TEXTURE_3D

    def __init__(self, **texture_data):
        Texture.__init__(self, **texture_data)

        data = texture_data.get('data', c_void_p(0))

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_3D, self.buffer)
        glTexImage3D(GL_TEXTURE_3D,
                     0,
                     self.internal_format,
                     self.width,
                     self.height,
                     self.depth,
                     0,
                     self.texture_format,
                     self.data_type,
                     data)

        if self.enable_mipmap:
            glGenerateMipmap(GL_TEXTURE_3D)
            # create indivisual mipmapThis creates a texture with a single mipmap level.
            # You will also need separate glTexSubImage2D calls to upload each mipmap
            # glTexStorage2D(GL_TEXTURE_3D, 1, GL_RGBA8, width, height)
            # glTexSubImage2D(GL_TEXTURE_3D, 0​, 0, 0, width​, height​, GL_BGRA, GL_UNSIGNED_BYTE, pixels)

        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, self.wrap)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, self.wrap)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, self.wrap)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glBindTexture(GL_TEXTURE_3D, 0)


class Texture2DMultiSample(Texture):
    target = GL_TEXTURE_2D_MULTISAMPLE

    def __init__(self, **texture_data):
        Texture.__init__(self, **texture_data)

        multisample_count = texture_data.get('multisample_count', 4)
        self.multisample_count = multisample_count - (multisample_count % 4)

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, self.buffer)
        glTexImage2DMultisample(GL_TEXTURE_2D_MULTISAMPLE,
                                self.multisample_count,
                                self.internal_format,
                                self.width,
                                self.height,
                                GL_TRUE)
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, 0)


class TextureCube(Texture):
    target = GL_TEXTURE_CUBE_MAP
    default_wrap = GL_CLAMP_TO_EDGE

    def __init__(self, **texture_data):
        Texture.__init__(self, **texture_data)

        self.texture_positive_x = texture_data.get('texture_positive_x')
        self.texture_negative_x = texture_data.get('texture_negative_x')
        self.texture_positive_y = texture_data.get('texture_positive_y')
        self.texture_negative_y = texture_data.get('texture_negative_y')
        self.texture_positive_z = texture_data.get('texture_positive_z')
        self.texture_negative_z = texture_data.get('texture_negative_z')

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.buffer)

        def createTexImage2D(cube_index, texture):
            if texture:
                return glTexImage2D(cube_index,
                                    0,
                                    texture.internal_format,
                                    texture.width,
                                    texture.height,
                                    0,
                                    texture.texture_format,
                                    texture.data_type,
                                    texture.get_image_data())
            else:
                return glTexImage2D(cube_index,
                                    0,
                                    self.internal_format,
                                    self.width,
                                    self.height,
                                    0,
                                    self.texture_format,
                                    self.data_type,
                                    c_void_p(0))

        createTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X, self.texture_positive_x)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_X, self.texture_negative_x)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Y, self.texture_positive_y)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, self.texture_negative_y)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Z, self.texture_positive_z)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, self.texture_negative_z)

        glGenerateMipmap(GL_TEXTURE_CUBE_MAP)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, self.wrap)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, self.wrap)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, self.wrap)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

    def get_save_data(self, get_image_data=True):
        save_data = Texture.get_save_data(self)
        save_data['texture_positive_x'] = self.texture_positive_x.name
        save_data['texture_negative_x'] = self.texture_negative_x.name
        save_data['texture_positive_y'] = self.texture_positive_y.name
        save_data['texture_negative_y'] = self.texture_negative_y.name
        save_data['texture_positive_z'] = self.texture_positive_z.name
        save_data['texture_negative_z'] = self.texture_negative_z.name
        return save_data

    def getAttribute(self):
        Texture.getAttribute(self)
        self.attribute.setAttribute("texture_positive_x", self.texture_positive_x.name)
        self.attribute.setAttribute("texture_negative_x", self.texture_negative_x.name)
        self.attribute.setAttribute("texture_positive_y", self.texture_positive_y.name)
        self.attribute.setAttribute("texture_negative_y", self.texture_negative_y.name)
        self.attribute.setAttribute("texture_positive_z", self.texture_positive_z.name)
        self.attribute.setAttribute("texture_negative_z", self.texture_negative_z.name)
        return self.attribute
