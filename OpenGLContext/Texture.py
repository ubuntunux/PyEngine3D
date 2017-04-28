from ctypes import c_void_p

from OpenGL.GL import *

from Core import logger
from Utilities import Singleton, GetClassName, Attributes


def get_texture_format(str_image_mode):
    if str_image_mode == "RGB":
        return GL_RGB
    elif str_image_mode == "RGBA":
        return GL_RGBA
    return GL_RGBA


def CreateTextureFromFile(texture_name, texture_datas: dict):
    texture_type = texture_datas.get('texture_type', 'Tex2D')  # texture_type: Tex1D, Tex2D, Tex3D, Cube
    image_mode = texture_datas.get('image_mode', 'RGBA')  # image_mode: "RGBA", "RGB"
    width = texture_datas.get('width', 0)
    height = texture_datas.get('height', 0)
    data = texture_datas.get('data')

    internal_format = get_texture_format(image_mode)
    texture_format = internal_format
    if texture_type == 'Tex2D':
        return Texture2D(texture_name, internal_format, width, height, texture_format, GL_UNSIGNED_BYTE, data)
    return None


class Texture2D:
    def __init__(self, texture_name, internal_format=GL_RGBA, width=1024, height=1024, texture_format=GL_BGRA,
                 data_type=GL_UNSIGNED_BYTE, data=c_void_p(0)):
        logger.info("Create " + GetClassName(self) + " : " + texture_name)

        self.name = texture_name
        self.width = width
        self.height = height
        self.attribute = Attributes()
        self.internal_format = internal_format  # The number of channels and the data type
        self.buffer_format = texture_format  # R,G,B,A order. GL_BGRA is faster than GL_RGBA

        self.buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.buffer)

        glTexImage2D(GL_TEXTURE_2D, 0, internal_format, width, height, 0, texture_format, data_type, data)
        glGenerateMipmap(GL_TEXTURE_2D)

        # create indivisual mipmapThis creates a texture with a single mipmap level.
        # You will also need separate glTexSubImage2D calls to upload each mipmap
        # glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, width, height)
        # glTexSubImage2D(GL_TEXTURE_2D, 0​, 0, 0, width​, height​, GL_BGRA, GL_UNSIGNED_BYTE, pixels)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

    def __del__(self):
        pass

    def delete(self):
        glDeleteTextures(1, self.buffer)

    def bind_texture(self):
        glBindTexture(GL_TEXTURE_2D, self.buffer)

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        return self.attribute
