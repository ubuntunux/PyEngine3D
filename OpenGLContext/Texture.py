from ctypes import c_void_p

from OpenGL.GL import *

from Utilities import Singleton, GetClassName, Attributes
from Common import logger


def get_internal_format(str_image_mode):
    if str_image_mode == "RGB":
        return GL_RGB
    elif str_image_mode == "RGBA":
        return GL_RGBA
    return GL_RGBA


def get_texture_format(str_image_mode):
    # R,G,B,A order. GL_BGRA is faster than GL_RGBA
    if str_image_mode == "RGB":
        return GL_RGB
    elif str_image_mode == "RGBA":
        return GL_BGRA
    return GL_BGRA


def get_image_mode(texture_internal_format):
    if texture_internal_format in (GL_RGB, GL_BGR):
        return "RGB"
    elif texture_internal_format in (GL_RGBA, GL_BGRA):
        return "RGBA"
    return "RGBA"


def CreateTextureFromFile(**texture_datas):
    texture_type = texture_datas.get('texture_type', Texture2D)
    if texture_type == Texture2D:
        return Texture2D(**texture_datas)
    elif texture_type == TextureCube:
        return TextureCube(**texture_datas)
    return None


class Texture:
    target = GL_TEXTURE_2D
    default_wrap = GL_REPEAT

    def __init__(self, **texture_data):
        self.name = texture_data.get('name')
        logger.info("Create " + GetClassName(self) + " : " + self.name)

        self.using = False  # texture using flag for temp rendertarget
        self.attachment = False
        self.image_mode = texture_data.get('image_mode')
        self.internal_format = texture_data.get('internal_format')
        self.texture_format = texture_data.get('texture_format')

        if self.image_mode:
            if self.internal_format is None:
                self.internal_format = get_internal_format(self.image_mode)
            if self.texture_format is None:
                self.texture_format = get_texture_format(self.image_mode)
        elif self.internal_format:
            self.image_mode = get_image_mode(self.internal_format)

        self.width = texture_data.get('width', 0)
        self.height = texture_data.get('height', 0)
        self.data_type = texture_data.get('data_type', GL_UNSIGNED_BYTE)
        self.min_filter = texture_data.get('min_filter', GL_LINEAR_MIPMAP_LINEAR)
        self.mag_filter = texture_data.get('mag_filter', GL_LINEAR)  # GL_LINEAR_MIPMAP_LINEAR, GL_LINEAR, GL_NEAREST
        self.wrap = texture_data.get('wrap', self.default_wrap)  # GL_REPEAT, GL_CLAMP

        self.buffer = None

        self.attribute = Attributes()

    def delete(self):
        glBindTexture(self.target, 0)
        glDeleteTextures(1, [self.buffer, ])

    def release(self):
        self.using = False

    def get_save_data(self):
        save_data = dict(
            texture_type=self.__class__,
            width=self.width,
            height=self.height,
            image_mode=self.image_mode,
            internal_format=self.internal_format,
            texture_format=self.texture_format,
            data_type=self.data_type,
            min_filter=self.min_filter,
            mag_filter=self.mag_filter,
            wrap=self.wrap
        )
        return save_data

    def get_image_data(self):
        glBindTexture(self.target, self.buffer)
        data = glGetTexImage(self.target, 0, self.texture_format, GL_UNSIGNED_BYTE)
        glBindTexture(self.target, 0)
        return data

    def bind_texture(self):
        glBindTexture(self.target, self.buffer)
        if self.attachment:
            error_msg = "%s was attached to framebuffer." % self.name
            logger.error(error_msg)
            raise BaseException(error_msg)

    def gen_mipmap(self):
        glGenerateMipmap(self.target)

    def is_depth_texture(self):
        return self.texture_format == GL_DEPTH_COMPONENT or self.texture_format == GL_DEPTH_STENCIL

    def is_attached(self):
        return self.attachment

    def set_attachment(self, attachment):
        self.attachment = attachment

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        self.attribute.setAttribute("image_mode", self.image_mode)
        self.attribute.setAttribute("internal_format", self.internal_format)
        self.attribute.setAttribute("texture_format", self.texture_format)
        self.attribute.setAttribute("data_type", self.data_type)
        self.attribute.setAttribute("min_filter", self.min_filter)
        self.attribute.setAttribute("mag_filter", self.mag_filter)
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

    def get_save_data(self):
        save_data = Texture.get_save_data(self)
        save_data['data'] = self.get_image_data()
        return save_data


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

    def get_save_data(self):
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
