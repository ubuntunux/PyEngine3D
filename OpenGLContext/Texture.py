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
    texture_type = texture_datas.get('texture_type', 'Tex2D')  # texture_type: Tex1D, Tex2D, Tex3D, Cube
    image_mode = texture_datas.get('image_mode', 'RGBA')  # image_mode: "RGBA", "RGB"
    width = texture_datas.get('width', 0)
    height = texture_datas.get('height', 0)
    data = texture_datas.get('data')

    internal_format = get_texture_format(image_mode)
    texture_format = internal_format
    if texture_type == 'Tex2D':
        return Texture2D(name=texture_name,
                         internal_format=internal_format,
                         texture_format=texture_format,
                         width=width,
                         height=height,
                         data_type=GL_UNSIGNED_BYTE,
                         data=data)
    return None


class Texture2D:
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
        data = texture_data.get('data', c_void_p(0))
        min_filter = texture_data.get('min_filter', GL_LINEAR_MIPMAP_LINEAR)
        mag_filter = texture_data.get('mag_filter', GL_LINEAR)
        wrap = texture_data.get('wrap', GL_REPEAT)

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

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, min_filter)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, mag_filter)
        glBindTexture(GL_TEXTURE_2D, 0)

        self.attribute = Attributes()

    def __del__(self):
        pass

    def is_depth_texture(self):
        return self.texture_format == GL_DEPTH_COMPONENT or self.texture_format == GL_DEPTH_STENCIL

    def delete(self):
        glDeleteTextures(1, self.buffer)

    def set_attachment(self, attachment):
        self.attachment = attachment

    def bind_texture(self):
        glBindTexture(GL_TEXTURE_2D, self.buffer)
        if self.attachment:
            logger.error("%s was attached to framebuffer." % self.name)

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        return self.attribute
