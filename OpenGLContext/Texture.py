from ctypes import c_void_p

from OpenGL.GL import *

from Utilities import Singleton, GetClassName, Attributes
from Common import logger


def get_texture_format(str_image_mode):
    if str_image_mode == "RGB":
        return GL_RGB
    elif str_image_mode == "RGBA":
        return GL_RGBA
    return GL_RGBA


def CreateTextureFromFile(texture_name, texture_datas: dict):
    texture_type = texture_datas.get('texture_type', Texture2D)
    image_mode = texture_datas.get('image_mode', 'RGBA')  # image_mode: "RGBA", "RGB"
    width = texture_datas.get('width', 0)
    height = texture_datas.get('height', 0)
    data = texture_datas.get('data')

    internal_format = get_texture_format(image_mode)
    texture_format = internal_format
    if texture_type == Texture2D:
        return Texture2D(name=texture_name,
                         internal_format=internal_format,
                         texture_format=texture_format,
                         width=width,
                         height=height,
                         data_type=GL_UNSIGNED_BYTE,
                         data=data)
    elif texture_type == TextureCube:
        return TextureCube(name=texture_name,
                           internal_format=internal_format,
                           texture_format=texture_format,
                           width=width,
                           height=height,
                           data_type=GL_UNSIGNED_BYTE,
                           data=data)
    return None


class Texture:
    target = GL_TEXTURE_2D

    def __init__(self, **texture_data):
        self.name = texture_data.get('name')
        logger.info("Load " + GetClassName(self) + " : " + self.name)

        self.attachment = False

        self.width = texture_data.get('width', 1024)
        self.height = texture_data.get('height', 1024)
        # The number of channels and the data type
        self.internal_format = texture_data.get('internal_format', GL_RGBA)
        # R,G,B,A order. GL_BGRA is faster than GL_RGBA
        self.texture_format = texture_data.get('texture_format', GL_BGRA)
        self.data_type = texture_data.get('data_type', GL_UNSIGNED_BYTE)
        self.min_filter = texture_data.get('min_filter', GL_LINEAR_MIPMAP_LINEAR)
        self.mag_filter = texture_data.get('mag_filter', GL_LINEAR)  # GL_LINEAR, GL_NEAREST
        self.wrap = texture_data.get('wrap', GL_REPEAT)  # GL_REPEAT, GL_CLAMP

        self.buffer = None

        self.attribute = Attributes()

    def delete(self):
        glDeleteTextures(1, self.buffer)

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

    def set_attachment(self, attachment):
        self.attachment = attachment

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
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


class TextureCube(Texture):
    target = GL_TEXTURE_CUBE_MAP

    def __init__(self, **texture_data):
        Texture.__init__(self, **texture_data)

        # TEST_CODE
        data_test = texture_data.get('data', c_void_p(0))

        data_positive_x = texture_data.get('data_positive_x', c_void_p(0))
        data_negative_x = texture_data.get('data_negative_x', c_void_p(0))
        data_positive_y = texture_data.get('data_positive_y', c_void_p(0))
        data_negative_y = texture_data.get('data_negative_y', c_void_p(0))
        data_positive_z = texture_data.get('data_positive_z', c_void_p(0))
        data_negative_z = texture_data.get('data_negative_z', c_void_p(0))

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.buffer)

        def createTexImage2D(cube_index, data):
            glTexImage2D(cube_index,
                         0,
                         self.internal_format,
                         self.width,
                         self.height,
                         0,
                         self.texture_format,
                         self.data_type,
                         data)

        createTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X, data_test)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_X, data_test)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Y, data_test)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, data_test)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Z, data_test)
        createTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, data_test)

        glGenerateMipmap(GL_TEXTURE_CUBE_MAP)

        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, self.wrap)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, self.wrap)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, self.wrap)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
