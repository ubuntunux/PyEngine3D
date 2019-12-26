import traceback
import copy
import gc
from ctypes import c_void_p
import itertools
import array
import math

import numpy as np

from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.Utilities import Singleton, GetClassName, Attributes, Profiler
from PyEngine3D.OpenGLContext import OpenGLContext


def get_numpy_dtype(data_type):
    if GL_BYTE == data_type:
        return np.int8
    elif GL_UNSIGNED_BYTE == data_type:
        return np.uint8
    elif GL_UNSIGNED_BYTE == data_type:
        return np.uint8
    elif GL_SHORT == data_type:
        return np.int16
    elif GL_UNSIGNED_SHORT == data_type:
        return np.uint16
    elif GL_INT == data_type:
        return np.int32
    elif GL_UNSIGNED_INT == data_type:
        return np.uint32
    elif GL_UNSIGNED_INT64 == data_type:
        return np.uint64
    elif GL_FLOAT == data_type:
        return np.float32
    elif GL_DOUBLE == data_type:
        return np.float64

    logger.error('Cannot convert to numpy dtype. UNKOWN DATA TYPE(%s)', data_type)
    return np.uint8


def get_internal_format(str_image_mode):
    if str_image_mode == "RGBA":
        return GL_RGBA8
    elif str_image_mode == "RGB":
        return GL_RGB8
    elif str_image_mode == "L" or str_image_mode == "P" or str_image_mode == "R":
        return GL_R8
    else:
        logger.error("get_internal_format::unknown image mode ( %s )" % str_image_mode)
    return GL_RGBA8


def get_texture_format(str_image_mode):
    if str_image_mode == "RGBA":
        # R,G,B,A order. GL_BGRA is faster than GL_RGBA
        return GL_RGBA  # GL_BGRA
    elif str_image_mode == "RGB":
        return GL_RGB
    elif str_image_mode == "L" or str_image_mode == "P" or str_image_mode == "R":
        return GL_RED
    else:
        logger.error("get_texture_format::unknown image mode ( %s )" % str_image_mode)
    return GL_RGBA


def get_image_mode(texture_internal_format):
    if texture_internal_format in (GL_RGBA, GL_BGRA):
        return "RGBA"
    elif texture_internal_format in (GL_RGB, GL_BGR):
        return "RGB"
    elif texture_internal_format == GL_RG:
        return "RG"
    elif texture_internal_format in (GL_R8, GL_R16F, GL_RED, GL_DEPTH_STENCIL, GL_DEPTH_COMPONENT):
        return "R"
    elif texture_internal_format == GL_LUMINANCE:
        return "L"
    else:
        logger.error("get_image_mode::unknown image format ( %s )" % texture_internal_format)
    return "RGBA"


def CreateTexture(**texture_datas):
    texture_class = texture_datas.get('texture_type', Texture2D)
    if texture_class is not None:
        if type(texture_class) is str:
            texture_class = eval(texture_class)
        return texture_class(**texture_datas)
    return None


class Texture:
    target = GL_TEXTURE_2D
    default_wrap = GL_REPEAT
    use_glTexStorage = False

    def __init__(self, **texture_data):
        self.name = texture_data.get('name')
        self.attachment = False
        self.image_mode = "RGBA"
        self.internal_format = GL_RGBA8
        self.texture_format = GL_RGBA
        self.sRGB = False
        self.clear_color = None
        self.multisample_count = 0

        self.width = 0
        self.height = 0
        self.depth = 1
        self.data_type = GL_UNSIGNED_BYTE
        self.min_filter = GL_LINEAR_MIPMAP_LINEAR
        self.mag_filter = GL_LINEAR
        self.enable_mipmap = False

        self.wrap = self.default_wrap
        self.wrap_s = self.default_wrap
        self.wrap_t = self.default_wrap
        self.wrap_r = self.default_wrap
        self.buffer = -1
        self.sampler_handle = -1
        self.attribute = Attributes()

        self.create_texture(**texture_data)

    def create_texture(self, **texture_data):
        if self.buffer != -1:
            self.delete()

        self.attachment = False
        self.image_mode = texture_data.get('image_mode')
        self.internal_format = texture_data.get('internal_format')
        self.texture_format = texture_data.get('texture_format')
        self.sRGB = texture_data.get('sRGB', False)
        self.clear_color = texture_data.get('clear_color')
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
                self.internal_format = GL_SRGB8
            elif self.internal_format == GL_RGBA:
                self.internal_format = GL_SRGB8_ALPHA8

        if GL_RGBA == self.internal_format:
            self.internal_format = GL_RGBA8
        if GL_RGB == self.internal_format:
            self.internal_format = GL_RGB8

        self.width = int(texture_data.get('width', 0))
        self.height = int(texture_data.get('height', 0))
        self.depth = int(max(1, texture_data.get('depth', 1)))
        self.data_type = texture_data.get('data_type', GL_UNSIGNED_BYTE)
        self.min_filter = texture_data.get('min_filter', GL_LINEAR_MIPMAP_LINEAR)
        self.mag_filter = texture_data.get('mag_filter', GL_LINEAR)  # GL_LINEAR_MIPMAP_LINEAR, GL_LINEAR, GL_NEAREST

        mipmap_filters = (GL_LINEAR_MIPMAP_LINEAR, GL_LINEAR_MIPMAP_NEAREST,
                          GL_NEAREST_MIPMAP_LINEAR, GL_NEAREST_MIPMAP_NEAREST)
        self.enable_mipmap = self.min_filter in mipmap_filters
        if self.target == GL_TEXTURE_2D_MULTISAMPLE:
            self.enable_mipmap = False

        self.wrap = texture_data.get('wrap', self.default_wrap)  # GL_REPEAT, GL_CLAMP
        self.wrap_s = texture_data.get('wrap_s')
        self.wrap_t = texture_data.get('wrap_t')
        self.wrap_r = texture_data.get('wrap_r')
        self.buffer = -1
        self.sampler_handle = -1

        # texture parameter overwrite
        # self.sampler_handle = glGenSamplers(1)
        # glSamplerParameteri(self.sampler_handle, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        # glBindSampler(0, self.sampler_handle)

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

    def get_texture_info(self):
        return dict(
            texture_type=self.__class__.__name__,
            width=self.width,
            height=self.height,
            depth=self.depth,
            image_mode=self.image_mode,
            internal_format=self.internal_format,
            texture_format=self.texture_format,
            data_type=self.data_type,
            min_filter=self.min_filter,
            mag_filter=self.mag_filter,
            wrap=self.wrap,
            wrap_s=self.wrap_s,
            wrap_t=self.wrap_t,
            wrap_r=self.wrap_r,
        )

    def get_save_data(self):
        save_data = self.get_texture_info()
        data = self.get_image_data()
        if data is not None:
            save_data['data'] = data
        return save_data

    def get_mipmap_size(self, level=0):
        if 0 < level:
            divider = 2.0 ** level
            width = max(1, int(self.width / divider))
            height = max(1, int(self.height / divider))
            return width, height
        return self.width, self.height

    def get_image_data(self, level=0):
        if self.target not in (GL_TEXTURE_2D, GL_TEXTURE_2D_ARRAY, GL_TEXTURE_3D):
            return None

        level = min(level, self.get_mipmap_count())
        dtype = get_numpy_dtype(self.data_type)

        try:
            glBindTexture(self.target, self.buffer)
            data = OpenGLContext.glGetTexImage(self.target, level, self.texture_format, self.data_type)
            # convert to numpy array
            if type(data) is bytes:
                data = np.fromstring(data, dtype=dtype)
            else:
                data = np.array(data, dtype=dtype)
            glBindTexture(self.target, 0)
            return data
        except:
            logger.error(traceback.format_exc())
            logger.error('%s failed to get image data.' % self.name)
            logger.info('Try to glReadPixels.')

        glBindTexture(self.target, self.buffer)
        fb = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fb)

        data = []
        for layer in range(self.depth):
            if GL_TEXTURE_2D == self.target:
                glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.buffer, level)
            elif GL_TEXTURE_3D == self.target:
                glFramebufferTexture3D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_3D, self.buffer, level, layer)
            elif GL_TEXTURE_2D_ARRAY == self.target:
                glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.buffer, level, layer)
            glReadBuffer(GL_COLOR_ATTACHMENT0)
            width, height = self.get_mipmap_size(level)
            pixels = glReadPixels(0, 0, width, height, self.texture_format, self.data_type)
            # convert to numpy array
            if type(pixels) is bytes:
                pixels = np.fromstring(pixels, dtype=dtype)
            data.append(pixels)
        data = np.array(data, dtype=dtype)
        glBindTexture(self.target, 0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glDeleteFramebuffers(1, [fb, ])
        return data

    def get_mipmap_count(self):
        factor = max(max(self.width, self.height), self.depth)
        return math.floor(math.log2(factor)) + 1

    def generate_mipmap(self):
        if self.enable_mipmap:
            glBindTexture(self.target, self.buffer)
            glGenerateMipmap(self.target)
        else:
            logger.warn('%s disable to generate mipmap.' % self.name)

    def texure_wrap(self, wrap):
        glTexParameteri(self.target, GL_TEXTURE_WRAP_S, wrap)
        glTexParameteri(self.target, GL_TEXTURE_WRAP_T, wrap)
        glTexParameteri(self.target, GL_TEXTURE_WRAP_R, wrap)

    def bind_texture(self, wrap=None):
        if self.buffer == -1:
            logger.warn("%s texture is invalid." % self.name)
            return

        glBindTexture(self.target, self.buffer)

        if wrap is not None:
            self.texure_wrap(wrap)

    def bind_image(self, image_unit, level=0, access=GL_READ_WRITE):
        if self.buffer == -1:
            logger.warn("%s texture is invalid." % self.name)
            return
        # flag : GL_READ_WRITE, GL_WRITE_ONLY, GL_READ_ONLY
        glBindImageTexture(image_unit, self.buffer, level, GL_FALSE, 0, access, self.internal_format)

    def is_attached(self):
        return self.attachment

    def set_attachment(self, attachment):
        self.attachment = attachment

    def get_attribute(self):
        self.attribute.set_attribute("name", self.name)
        self.attribute.set_attribute("target", self.target)
        self.attribute.set_attribute("width", self.width)
        self.attribute.set_attribute("height", self.height)
        self.attribute.set_attribute("depth", self.depth)
        self.attribute.set_attribute("image_mode", self.image_mode)
        self.attribute.set_attribute("internal_format", self.internal_format)
        self.attribute.set_attribute("texture_format", self.texture_format)
        self.attribute.set_attribute("data_type", self.data_type)
        self.attribute.set_attribute("min_filter", self.min_filter)
        self.attribute.set_attribute("mag_filter", self.mag_filter)
        self.attribute.set_attribute("multisample_count", self.multisample_count)
        self.attribute.set_attribute("wrap", self.wrap)
        self.attribute.set_attribute("wrap_s", self.wrap_s)
        self.attribute.set_attribute("wrap_t", self.wrap_t)
        self.attribute.set_attribute("wrap_r", self.wrap_r)
        return self.attribute

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if hasattr(self, attribute_name) and "" != attribute_value:
            setattr(self, attribute_name, eval(attribute_value))

        if 'wrap' in attribute_name:
            glBindTexture(self.target, self.buffer)
            glTexParameteri(self.target, GL_TEXTURE_WRAP_S, self.wrap_s or self.wrap)
            glTexParameteri(self.target, GL_TEXTURE_WRAP_T, self.wrap_t or self.wrap)
            glTexParameteri(self.target, GL_TEXTURE_WRAP_R, self.wrap_r or self.wrap)
            glBindTexture(self.target, 0)

        return self.attribute


class Texture2D(Texture):
    target = GL_TEXTURE_2D

    def create_texture(self, **texture_data):
        Texture.create_texture(self, **texture_data)

        data = texture_data.get('data')

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.buffer)

        if self.use_glTexStorage:
            glTexStorage2D(GL_TEXTURE_2D,
                           self.get_mipmap_count(),
                           self.internal_format,
                           self.width, self.height)

            if data is not None:
                glTexSubImage2D(GL_TEXTURE_2D,
                                0,
                                0, 0,
                                self.width, self.height,
                                self.texture_format,
                                self.data_type,
                                data)
        else:
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

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, self.wrap_s or self.wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, self.wrap_t or self.wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, self.mag_filter)

        if self.clear_color is not None:
            glClearTexImage(self.buffer, 0, self.texture_format, self.data_type, self.clear_color)

        glBindTexture(GL_TEXTURE_2D, 0)


class Texture2DArray(Texture):
    target = GL_TEXTURE_2D_ARRAY

    def create_texture(self, **texture_data):
        Texture.create_texture(self, **texture_data)

        data = texture_data.get('data')

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.buffer)

        if self.use_glTexStorage:
            glTexStorage3D(GL_TEXTURE_2D_ARRAY,
                           self.get_mipmap_count(),
                           self.internal_format,
                           self.width, self.height, self.depth)
            if data is not None:
                glTexSubImage3D(GL_TEXTURE_2D_ARRAY,
                                0,
                                0, 0, 0,
                                self.width, self.height, self.depth,
                                self.texture_format,
                                self.data_type,
                                data)
        else:
            glTexImage3D(GL_TEXTURE_2D_ARRAY,
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
            glGenerateMipmap(GL_TEXTURE_2D_ARRAY)

        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, self.wrap_s or self.wrap)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, self.wrap_t or self.wrap)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glBindTexture(GL_TEXTURE_2D_ARRAY, 0)


class Texture3D(Texture):
    target = GL_TEXTURE_3D

    def create_texture(self, **texture_data):
        Texture.create_texture(self, **texture_data)

        data = texture_data.get('data')

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_3D, self.buffer)

        if self.use_glTexStorage:
            glTexStorage3D(GL_TEXTURE_3D,
                           self.get_mipmap_count(),
                           self.internal_format,
                           self.width, self.height, self.depth)
            if data is not None:
                glTexSubImage3D(GL_TEXTURE_3D,
                                0,
                                0, 0, 0,
                                self.width, self.height, self.depth,
                                self.texture_format,
                                self.data_type,
                                data)
        else:
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

        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, self.wrap_s or self.wrap)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, self.wrap_t or self.wrap)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, self.wrap_r or self.wrap)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glBindTexture(GL_TEXTURE_3D, 0)


class Texture2DMultiSample(Texture):
    target = GL_TEXTURE_2D_MULTISAMPLE

    def create_texture(self, **texture_data):
        Texture.create_texture(self, **texture_data)

        multisample_count = texture_data.get('multisample_count', 4)
        self.multisample_count = multisample_count - (multisample_count % 4)

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, self.buffer)

        if self.use_glTexStorage:
            glTexStorage2DMultisample(GL_TEXTURE_2D_MULTISAMPLE,
                                      self.multisample_count,
                                      self.internal_format,
                                      self.width,
                                      self.height,
                                      GL_TRUE)
        else:
            glTexImage2DMultisample(GL_TEXTURE_2D_MULTISAMPLE,
                                    self.multisample_count,
                                    self.internal_format,
                                    self.width,
                                    self.height,
                                    GL_TRUE)

        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, 0)


class TextureCube(Texture):
    target = GL_TEXTURE_CUBE_MAP
    default_wrap = GL_REPEAT

    def __init__(self, **texture_data):
        self.texture_positive_x = None
        self.texture_negative_x = None
        self.texture_positive_y = None
        self.texture_negative_y = None
        self.texture_positive_z = None
        self.texture_negative_z = None

        Texture.__init__(self, **texture_data)

    def create_texture(self, **texture_data):
        Texture.create_texture(self, **texture_data)

        # If texture2d is None then create render target.
        face_texture_datas = copy.copy(texture_data)
        face_texture_datas.pop('name')
        face_texture_datas['texture_type'] = Texture2D

        self.texture_positive_x = texture_data.get('texture_positive_x', CreateTexture(name=self.name + "_right", **face_texture_datas))
        self.texture_negative_x = texture_data.get('texture_negative_x', CreateTexture(name=self.name + "_left", **face_texture_datas))
        self.texture_positive_y = texture_data.get('texture_positive_y', CreateTexture(name=self.name + "_top", **face_texture_datas))
        self.texture_negative_y = texture_data.get('texture_negative_y', CreateTexture(name=self.name + "_bottom", **face_texture_datas))
        self.texture_positive_z = texture_data.get('texture_positive_z', CreateTexture(name=self.name + "_front", **face_texture_datas))
        self.texture_negative_z = texture_data.get('texture_negative_z', CreateTexture(name=self.name + "_back", **face_texture_datas))

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.buffer)

        if self.use_glTexStorage:
            glTexStorage2D(GL_TEXTURE_CUBE_MAP, self.get_mipmap_count(), self.internal_format, self.width, self.height)
            self.createTexSubImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X, self.texture_positive_x)  # Right
            self.createTexSubImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_X, self.texture_negative_x)  # Left
            self.createTexSubImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Y, self.texture_positive_y)  # Top
            self.createTexSubImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, self.texture_negative_y)  # Bottom
            self.createTexSubImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Z, self.texture_positive_z)  # Front
            self.createTexSubImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, self.texture_negative_z)  # Back
        else:
            self.createTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X, self.texture_positive_x)  # Right
            self.createTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_X, self.texture_negative_x)  # Left
            self.createTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Y, self.texture_positive_y)  # Top
            self.createTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, self.texture_negative_y)  # Bottom
            self.createTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Z, self.texture_positive_z)  # Front
            self.createTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, self.texture_negative_z)  # Back

        if self.enable_mipmap:
            glGenerateMipmap(GL_TEXTURE_CUBE_MAP)

        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, self.wrap_s or self.wrap)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, self.wrap_t or self.wrap)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, self.wrap_r or self.wrap)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

    @staticmethod
    def createTexImage2D(target_face, texture):
        glTexImage2D(target_face,
                     0,
                     texture.internal_format,
                     texture.width,
                     texture.height,
                     0,
                     texture.texture_format,
                     texture.data_type,
                     texture.get_image_data())

    @staticmethod
    def createTexSubImage2D(target_face, texture):
        glTexSubImage2D(target_face,
                        0,
                        0, 0,
                        texture.width, texture.height,
                        texture.texture_format,
                        texture.data_type,
                        texture.get_image_data())

    def delete(self):
        super(TextureCube, self).delete()
        self.texture_positive_x.delete()
        self.texture_negative_x.delete()
        self.texture_positive_y.delete()
        self.texture_negative_y.delete()
        self.texture_positive_z.delete()
        self.texture_negative_z.delete()

    def get_save_data(self, get_image_data=True):
        save_data = Texture.get_save_data(self)
        save_data['texture_positive_x'] = self.texture_positive_x.name
        save_data['texture_negative_x'] = self.texture_negative_x.name
        save_data['texture_positive_y'] = self.texture_positive_y.name
        save_data['texture_negative_y'] = self.texture_negative_y.name
        save_data['texture_positive_z'] = self.texture_positive_z.name
        save_data['texture_negative_z'] = self.texture_negative_z.name
        return save_data

    def get_attribute(self):
        Texture.get_attribute(self)
        self.attribute.set_attribute("texture_positive_x", self.texture_positive_x.name)
        self.attribute.set_attribute("texture_negative_x", self.texture_negative_x.name)
        self.attribute.set_attribute("texture_positive_y", self.texture_positive_y.name)
        self.attribute.set_attribute("texture_negative_y", self.texture_negative_y.name)
        self.attribute.set_attribute("texture_positive_z", self.texture_positive_z.name)
        self.attribute.set_attribute("texture_negative_z", self.texture_negative_z.name)
        return self.attribute
