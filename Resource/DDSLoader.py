import ctypes
import os
import struct

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import *
from OpenGL.arrays.arraydatatype import *
from OpenGL.raw.GL.EXT.texture_compression_s3tc import *

from Common import logger


dxgi_pixel_or_block_size = [
	0,
	16, 16, 16, 16,
	12, 12, 12, 12,
	8, 8, 8, 8, 8, 8,
	8, 8, 8, 8,
	8, 8, 8, 8,
	4, 4, 4, 4,
	4, 4, 4, 4, 4, 4,
	4, 4, 4, 4, 4, 4,
	4, 4, 4, 4, 4,
	4,
	4, 4, 4,
	2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
	1, 1, 1, 1, 1, 1,
	0, # DXGI_FORMAT_R1_UNORM ehm >.< ( TODO )
	4, 4, 4,
	8, 8, 8,    # BC1
	16, 16, 16, # BC2
	16, 16, 16, # BC3
	8, 8, 8, 	# BC4
	16, 16, 16, # BC5
	2, 2,
	4, 4, 4, 4, 4, 4, 4,
	16, 16, 16, # BC6
	16, 16, 16, # BC7
	# TODO Complete the rest
]

dxgi_compressed_formats = [
	70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84,
	94, 95, 96, 97, 98, 99
]


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
        # buffer = np.asarray(buffer)
        buffer = np.fromstring(buffer, dtype=np.ubyte)

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
                # glCompressedTexImage2D(GL_TEXTURE_2D, level, format, width, height, 0, size, buffer.ctypes.data)
                glCompressedTexImage2D(GL_TEXTURE_2D, level, format, width, height, 0, buffer)
                offset += size
                width /= 2
                height /= 2
            else:
                break
        return textureID
    return None


"""
Copyright (c) 2015 Edoardo "sparkon" Dominici
Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""




# Win32 following : https://msdn.microsoft.com/en-us/library/windows/desktop/aa383751(v=vs.85).aspx
class Win32Types:
    DWORD = ctypes.c_ulong
    UINT = ctypes.c_uint


# DDS types
DDSEnumType = ctypes.c_ulong
DDSMagicNumber = Win32Types.DWORD
DDSFormatCC = Win32Types.DWORD


# Contains all default values used for validation
class DDSValues:
    MIN_FILE_SIZE = 128
    MAGIC_NUMBER = 0x20534444

    HEADER_SIZE = 124
    PIXELFORMAT_SIZE = 32


# Values used for flagging
class DDSEnums:
    # Complexity of stores resources DDS_HEADER::dwCaps
    DDSCAPS_COMPLEX = 0x8
    DDSCAPS_MIPMAP = 0x400000
    DDSCAPS_TEXTURE = 0x1000

    # Additional detail on surface DDS_HEADER::dwCaps2
    DDSCAPS2_CUBEMAP = 0x200
    DDSCAPS2_VOLUME = 0x200000

    # Flags to indicate what is stored inside the texture, they
    # are ignored for the most part since pitch and size are
    # calculated manually, they are used for structure validation
    DDSD_CAPS = 0x1
    DDSD_HEIGHT = 0x2
    DDSD_WIDTH = 0x4
    DDSD_PITCH = 0x8
    DDSD_PIXELFORMAT = 0x1000
    DDSD_MIPMAPCOUNT = 0x20000
    DDSD_LINEARSIZE = 0x80000
    DDSD_DEPTH = 0x800000

    # Only flag we are interested in DDS_PIXELFORMAT::dwFlags, is needed
    # to make sure the extended header is included
    DDPF_FOURCC = 0x4

    # Only value we are interested in DDS_PIXELFORMAT::dwFourCC, is needed
    # to make sure the extended header is included
    DX10_CC = int.from_bytes(bytearray(b"DX10"), byteorder="little", signed="false")

    # Misc flag in the DDS_HEADER_DXT10, flags the resource as cubemap
    DDS_RESOURCE_MISC_TEXTURECUBE = 0x4


# 1-to-1 mapping of DDS_PIXELFORMAT https://msdn.microsoft.com/en-us/library/windows/desktop/bb943984(v=vs.85).aspx
class DDSPixelFormat(ctypes.Structure):
    _fields_ = [
        ("dwSize", Win32Types.DWORD),
        ("dwFlags", Win32Types.DWORD),
        ("dwFourCC", DDSFormatCC),
        ("dwRGBBitCount", Win32Types.DWORD),
        ("dwRBitMask", Win32Types.DWORD),
        ("dwGBitMask", Win32Types.DWORD),
        ("dwBBitMask", Win32Types.DWORD),
        ("dwABitMask", Win32Types.DWORD)
    ]


# 1-to-1 mapping of DDS_HEADER https://msdn.microsoft.com/en-us/library/windows/desktop/bb943982(v=vs.85).aspx
class DDSHeader(ctypes.Structure):
    _fields_ = [
        ("dwSize", Win32Types.DWORD),
        ("dwFlags", Win32Types.DWORD),
        ("dwHeight", Win32Types.DWORD),
        ("dwWidth", Win32Types.DWORD),
        ("dwPitchOrLinearSize", Win32Types.DWORD),
        ("dwDepth", Win32Types.DWORD),
        ("dwMipMapCount", Win32Types.DWORD),
        ("dwReserved", Win32Types.DWORD * 11),
        ("ddspf", DDSPixelFormat),
        ("dwCaps", Win32Types.DWORD),
        ("dwCaps2", Win32Types.DWORD),
        ("dwCaps3", Win32Types.DWORD),
        ("dwCaps4", Win32Types.DWORD),
        ("dwReserved2", Win32Types.DWORD)
    ]


# 1-to-1 mapping of DDS_HEADER_DXT10 https://msdn.microsoft.com/en-us/library/windows/desktop/bb943983(v=vs.85).aspx
class DDSExtHeader(ctypes.Structure):
    _fields_ = [
        ("dxgiFormat", DDSEnumType),
        ("resourceDimension", DDSEnumType),
        ("miscFlag", Win32Types.UINT),
        ("arraySize", Win32Types.UINT),
        ("miscFlags2", Win32Types.UINT)
    ]


# FormatNotValid is raised when the file provided is not valid, more information in the message
class FormatNotValid(Exception):
    pass


# FormatNotSupported is raised when the file has some feature that is not supported by this implementation
class FormatNotSupported(Exception):
    pass


# Represents a single surface of any kind, depending on its position and the DDSTexture info the
# mipleve or array index can be deduced
class DDSSurface:
    def __init__(self, width, height, pitch, size):
        self.width = width
        self.height = height
        self.pitch = pitch
        self.size = size

    def __str__(self):
        return "Width: {0} Height: {1} Pitch: {2} Size: {3}".format(self.width, self.height, self.pitch, self.size)


# Represents a loaded DDSFile, the name might be misleading since multiple textures or texturecubes can be
# contained inside here
class DDSTexture:
    # Type of the DDSTexture, volume texture is not supported, and 1D textures should be mapped
    # to 2D textures with height == 1, but this hasn't been tested yet ( TODO )
    class Type:
        Texture2D = 0
        TextureCube = 1
        Texture2DArray = 2
        TextureCubeArray = 3

        names = [
            "Texture2D",
            "TextureCube",
            "Texture2DArray",
            "TextureCubeArray"
        ]

    def __init__(self):
        self.real_size = 0
        self.calculated_size = 0

        # File format
        self.name = None
        self.magic_number = DDSMagicNumber()
        self.header = DDSHeader()
        self.ext_header = DDSExtHeader()

        # Type information
        self.type = None
        self.array_size = None

        # List of surfaces that contain info on how to read raw data
        self.surfaces = []

        # Raw data
        self.data = None

        # Format information
        self.dxgi_format = None
        self.is_compressed = None
        self.bpp_or_block_size = None
        self.mipmap_count = None

    def __str__(self):
        return "{0} | Type={1} ArraySize={2} MipMapCount={3} Format={4} BPP={5}".format(self.name,
                                                                                        self.Type.names[self.type],
                                                                                        self.array_size,
                                                                                        self.mipmap_count,
                                                                                        self.dxgi_format,
                                                                                        self.bpp_or_block_size)

    # Used internally to validate information contained inside the headers to make sure reading
    # or writing was successful. This test could be removed, but files that do not pass this *NOT COMPLETE*
    # validation phase are not following the specification
    def _validate_structures(self):
        if self.header.dwSize != DDSValues.HEADER_SIZE:
            raise FormatNotValid("File not formatted correctly, header size not matching")

        if self.header.ddspf.dwSize != DDSValues.PIXELFORMAT_SIZE:
            raise FormatNotValid("File not formatted correctly, extended header size not matching")

        if not (self.header.dwFlags & DDSEnums.DDSD_CAPS) or \
                not (self.header.dwFlags & DDSEnums.DDSD_WIDTH) or \
                not (self.header.dwFlags & DDSEnums.DDSD_HEIGHT) or \
                not (self.header.dwFlags & DDSEnums.DDSD_PIXELFORMAT) or \
                not (self.header.dwFlags & DDSEnums.DDSD_CAPS) or \
                not (self.header.dwFlags & DDSEnums.DDSD_CAPS):
            raise FormatNotValid("File not formatted correctly, required flags not present")

        if not (self.header.dwCaps & DDSEnums.DDSCAPS_TEXTURE):
            raise FormatNotValid("File not formatted correctly, required flags not present")

    # Fills in information regarding the pixel format
    def _compute_format(self):
        self.dxgi_format = self.ext_header.dxgiFormat

        # If the texture is compressed
        self.bpp_or_block_size = dxgi_values.dxgi_pixel_or_block_size[self.dxgi_format]

        # Checking if the texture is compressed or not ( we need it to calculate pitch )
        self.is_compressed = self.dxgi_format in dxgi_values.dxgi_compressed_formats

        # Checking if there are mipmaps
        self.mipmap_count = self.header.dwMipMapCount

    # Computes the type of the DDSTexture
    def _compute_type(self):
        if not (self.header.dwCaps & DDSEnums.DDSCAPS_TEXTURE):
            raise FormatNotValid("Invalid format file not tagged as texture")

        if self.header.dwCaps2 & DDSEnums.DDSCAPS2_CUBEMAP:
            if self.ext_header.arraySize > 1:
                self.type = DDSTexture.Type.TextureCubeArray
                self.array_size = self.ext_header.arraySize
            else:
                self.type = DDSTexture.Type.TextureCube
                self.array_size = 1
        # We either have a single texture or a texture array ( 2D )
        else:
            if self.format_code == DDSEnums.DX10_CC and \
                            self.ext_header.arraySize > 1:
                self.type = DDSTexture.Type.Texture2DArray
                self.array_size = self.ext_header.arraySize
            else:
                self.type = DDSTexture.Type.Texture2D
                self.array_size = 1

    # Loads the texture from the filename, obtaining
    # data - array of c_byte containing untouched texture data formatted matching the surfaces data
    # surfaces - metadata for the raw texture data that describes how it can be read, its valued are ready for DirectX11 creation ( Pitch, width, height, size )
    # format - DXGI compatible format the integer self.format can be safely static_cast<DXGI_FORMAT> to obtain the C++ enumerator counterpart
    def load(self, filename):
        self.name = filename

        # Making sure the file is big enough to contain the magic number + default header
        self.real_size = os.path.getsize(filename)
        if self.real_size < DDSValues.MIN_FILE_SIZE:
            raise FormatNotValid("File is too small")

        with open(filename, "rb") as file_stream:
            # Reading magic number and making sure is valid
            bytes_read = file_stream.readinto(self.magic_number)
            if bytes_read < ctypes.sizeof(self.magic_number):
                raise FormatNotValid("Failed to read magic number")

            if self.magic_number.value != DDSValues.MAGIC_NUMBER:
                raise FormatNotValid("Invalid magic number")

            # Reading header
            bytes_read = file_stream.readinto(self.header)
            if bytes_read < ctypes.sizeof(self.header):
                raise FormatNotValid("Failed to read header")

            # TODO : Add support for non-squared textures
            assert self.header.dwWidth == self.header.dwHeight

            # Reading extended header
            if self.header.ddspf.dwFlags & DDSEnums.DDPF_FOURCC and self.header.ddspf.dwFourCC == DDSEnums.DX10_CC:
                bytes_read = file_stream.readinto(self.ext_header)
                if bytes_read < ctypes.sizeof(self.ext_header):
                    raise FormatNotValid("Failed to read extended header")
            else:
                raise FormatNotSupported(
                    "Sorry we only support DDS texture with DX10 extended header, if you are using texconv tools use the -dx10 flag")

            # Validating the DDS_HEADER and DX10_DDS_HEADER to make sure they comply to specification
            # or supported features
            self._validate_structures()

            # Calculates the compression / format and bpp
            self._compute_format()
            # Computes the type of this DDSTexture instance
            self._compute_type()

            total_data_size = 0

            # Looping through all the textures and saving surface data
            elements = self.array_size
            if self.type == self.Type.TextureCube or self.type == self.Type.TextureCubeArray:
                elements *= 6

            for i in range(elements):
                next_width = self.header.dwWidth
                next_height = self.header.dwHeight
                if self.is_compressed:
                    next_size = self.header.dwPitchOrLinearSize
                else:
                    next_size = next_height * self.header.dwPitchOrLinearSize

                for mipmap in range(self.header.dwMipMapCount):
                    total_data_size += next_size
                    if self.is_compressed:
                        pitch = max(1, int(((next_width + 3) / 4))) * self.bpp_or_block_size
                    else:
                        pitch = (next_width * self.bpp_or_block_size + 7) / 8

                    self.surfaces.append(DDSSurface(next_width, next_height, pitch, next_size))
                    # TODO When working with non-squared non-power of two textures check this divisions
                    next_width = int(next_width / 2)
                    next_height = int(next_height / 2)
                    next_size = max(8, int(next_size / 4))

            self.data = (ctypes.c_byte * total_data_size)()
            bytes_read = file_stream.readinto(self.data)
            if bytes_read < total_data_size:
                raise FormatNotValid("Metadata doesn't match actual data")

if __name__ == "__main__":
    # 1
    loadDDS("Externals/Textures/dds_test.dds")

    # 2
    dds_texture = DDSTexture()
    dds_texture.load("Externals/Textures/dds_test.dds")

    for surface in dds_texture.surfaces:
        print(surface)