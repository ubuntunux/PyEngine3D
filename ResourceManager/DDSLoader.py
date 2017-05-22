import ctypes
import os
import struct

import numpy
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import *
from OpenGL.raw.GL.EXT.texture_compression_s3tc import *

from Common import logger


def loadDDS(imagepath):
    if not os.path.exists(imagepath):
        logger.error("Cannot open %s file" % imagepath)
        return None

    with open(imagepath, "rb") as fp:
        filecode = struct.unpack("4s", fp.read(4))[0]

        if filecode.decode('ascii') != "DDS ":
            logger.error("%s is not dds file." % imagepath)
            return None

        # read header
        header = struct.unpack("124s", fp.read(124))[0]
        height = struct.unpack("I", header[8:12])[0]
        width = struct.unpack("I", header[12:16])[0]
        linearSize = struct.unpack("I", header[16:20])[0]
        mipMapCount = struct.unpack("I", header[24:28])[0]
        fourCC = struct.unpack("4s", header[80:84])[0]
        fourCC = fourCC.decode('ascii')

        # read buffer
        bufsize = (linearSize * 2) if mipMapCount > 1 else linearSize
        buffer = fp.read(bufsize)
        buffer = numpy.asarray(buffer)

        # texture desc
        components = 4
        blockSize = 16
        format = GL_COMPRESSED_RGBA_S3TC_DXT1_EXT
        if fourCC == "DXT1":
            format = GL_COMPRESSED_RGBA_S3TC_DXT1_EXT
            components = 3
            blockSize = 8
        elif fourCC == "DXT3":
            format = GL_COMPRESSED_RGBA_S3TC_DXT3_EXT
        elif fourCC == "DXT5":
            format = GL_COMPRESSED_RGBA_S3TC_DXT5_EXT
        else:
            logger.error("not support %s format" % fourCC)
            return None

        # Create one OpenGL texture
        offset = 0
        textureID = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textureID)
        for level in range(mipMapCount):
            if width > 0 and height > 0:
                size = int((width + 3)/4) * int((height + 3)/4) * blockSize
                # TODO : implement glCompressedTexImage2D
                glCompressedTexImage2D(GL_TEXTURE_2D, level, format, width, height, 0, size, buffer.ctypes.data_as(ctypes.c_void_p))
                offset += size
                width /= 2
                height /= 2
            else:
                break
        return textureID
    return None


if __name__ == "__main__":
    loadDDS("Textures/dds_test.dds")