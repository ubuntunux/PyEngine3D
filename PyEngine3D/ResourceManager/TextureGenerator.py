import random

import numpy as np
from numpy import array, mod, floor, ceil, sin, cos, dot

from OpenGL.GL import *

from PyEngine3D.Utilities import normalize
from PyEngine3D.OpenGLContext import CreateTexture, Texture2D, Texture2DArray, Texture3D, TextureCube


def generate_3d_data(size):
    value = 255.0 / float(size)
    data = array([0, 0, 0, 255] * size * size * size, dtype=np.uint8)
    for z in range(size):
        for y in range(size):
            for x in range(size):
                index = (x + y * size + z * size * size) * 4
                data[index] = x * value
                data[index + 1] = y * value
                data[index + 2] = z * value
    return data


def generate_random_data(texture_size, data_type):
    texture_data = np.zeros((texture_size * texture_size, 4), dtype=data_type)
    for i in range(texture_size * texture_size):
        texture_data[i][0] = random.random()
        texture_data[i][1] = random.random()
        texture_data[i][2] = random.random()
        texture_data[i][3] = random.random()
    return texture_data


def generate_random_normal(texture_size, data_type):
    texture_data = np.zeros((texture_size * texture_size, 3), dtype=data_type)
    for i in range(texture_size * texture_size):
        texture_data[i][0] = random.uniform(-1.0, 1.0)
        texture_data[i][1] = 0.0
        texture_data[i][2] = random.uniform(-1.0, 1.0)
        texture_data[i][:] = normalize(texture_data[i])
    return texture_data


def generate_common_textures(texture_loader):
    resource_name = "common.default_3d"
    if not texture_loader.hasResource(resource_name):
        size = 64
        data = generate_3d_data(size)
        texture = CreateTexture(
            name=resource_name,
            texture_type=Texture3D,
            width=size,
            height=size,
            depth=size,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            data_type=GL_UNSIGNED_BYTE,
            wrap=GL_REPEAT,
            data=data,
        )
        texture_loader.create_resource(resource_name, texture)
        texture_loader.save_resource(resource_name)

    resource_name = "common.default_2d_array"
    if not texture_loader.hasResource(resource_name):
        size = 64
        data = generate_3d_data(size)
        texture = CreateTexture(
            name=resource_name,
            texture_type=Texture2DArray,
            width=size,
            height=size,
            depth=size,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            data_type=GL_UNSIGNED_BYTE,
            wrap=GL_REPEAT,
            data=data,
        )
        texture_loader.create_resource(resource_name, texture)
        texture_loader.save_resource(resource_name)

    resource_name = "common.random"
    if not texture_loader.hasResource(resource_name):
        size = 512
        data = generate_random_data(size, np.float16)
        texture = CreateTexture(
            name=resource_name,
            texture_type=Texture2D,
            width=size,
            height=size,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_REPEAT,
            data=data,
        )
        texture_loader.create_resource(resource_name, texture)
        texture_loader.save_resource(resource_name)

    resource_name = "common.random_normal"
    if not texture_loader.hasResource(resource_name):
        size = 4
        data = generate_random_normal(size, np.float16)
        texture = CreateTexture(
            name=resource_name,
            texture_type=Texture2D,
            width=size,
            height=size,
            internal_format=GL_RGB16F,
            texture_format=GL_RGB,
            data_type=GL_FLOAT,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_REPEAT,
            data=data
        )
        texture_loader.create_resource(resource_name, texture)
        texture_loader.save_resource(resource_name)

    def generate_color_texture(resource_name, size, color):
        if not texture_loader.hasResource(resource_name):
            data = array([color for i in range(size * size)], dtype=np.uint8)
            component_count = len(color)
            texture = CreateTexture(
                name=resource_name,
                texture_type=Texture2D,
                width=size,
                height=size,
                internal_format=GL_RGBA8 if component_count == 4 else GL_RGB8,
                texture_format=GL_RGBA if component_count == 4 else GL_RGB,
                min_filter=GL_NEAREST,
                mag_filter=GL_NEAREST,
                data_type=GL_UNSIGNED_BYTE,
                wrap=GL_CLAMP_TO_EDGE,
                data=data,
            )
            texture_loader.create_resource(resource_name, texture)
            texture_loader.save_resource(resource_name)

    generate_color_texture("common.flat_red", 2, [255, 0, 0, 255])
    generate_color_texture("common.flat_green", 2, [0, 255, 0, 255])
    generate_color_texture("common.flat_blue", 2, [0, 0, 255, 255])
    generate_color_texture("common.flat_black", 2, [0, 0, 0, 255])
    generate_color_texture("common.flat_gray", 2, [128, 128, 128, 255])
    generate_color_texture("common.flat_white", 2, [255, 255, 255, 255])
    generate_color_texture("common.flat_normal", 2, [128, 128, 255, 255])
    generate_color_texture("common.flat_black_no_alpha", 2, [0, 0, 0, 0])
    generate_color_texture("common.flat_white_no_alpha", 2, [255, 255, 255, 0])
    generate_color_texture("common.flat_normal_no_alpha", 2, [128, 128, 255, 0])
