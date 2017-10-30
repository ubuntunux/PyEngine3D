import math
import os
import io
import os
import ctypes

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import *

from PIL import Image, ImageDraw, ImageFont, ImageFilter

import pygame
from pygame.locals import *

import numpy as np

from Common import logger
from OpenGLContext import Texture2D
from Utilities import *


SIMPLE_VERTEX_SHADER = '''
#version 430 core

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec2 tex_coord;
};

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
};

in VERTEX_INPUT vs_input;
out VERTEX_OUTPUT vs_output;

void main() {
    vs_output.tex_coord = vs_input.tex_coord;
    vs_output.position = vs_input.position;
    gl_Position = vec4(vs_input.position, 1.0);
}'''

SIMPLE_PIXEL_SHADER = '''
#version 430 core

uniform sampler2D texture_font;

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
};

in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main(void)
{
    vec2 tex_coord = vs_output.tex_coord.xy;
    fs_output = texture(texture_font, tex_coord);
}
'''


def SDF(image):
    # width, height = 640, 480
    # pygame.init()
    # pygame.display.set_mode((width, height), OPENGL | DOUBLEBUF | RESIZABLE | HWPALETTE | HWSURFACE)

    width, height = image.size
    image_data = image.tobytes("raw", image.mode, 0, -1)

    glFrontFace(GL_CCW)
    glEnable(GL_TEXTURE_2D)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_CULL_FACE)
    glDisable(GL_LIGHTING)
    glDisable(GL_BLEND)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # Create Shader
    vertex_shader = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vertex_shader, SIMPLE_VERTEX_SHADER)
    glCompileShader(vertex_shader)

    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment_shader, SIMPLE_PIXEL_SHADER)
    glCompileShader(fragment_shader)

    program = glCreateProgram()

    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)

    # delete shader
    glDetachShader(program, vertex_shader)
    glDetachShader(program, fragment_shader)
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    # Create Vertex Array
    dtype = np.float32
    positions = np.array([(-1, 1, 0), (-1, -1, 0), (1, -1, 0), (1, 1, 0)], dtype=np.float32)
    texcoords = np.array([(0, 1), (0, 0), (1, 0), (1, 1)], dtype=np.float32)
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
    datas = [positions, texcoords]

    vertex_buffer_size = 0
    vertex_strides = []
    vertex_stride_points = []
    accStridePoint = 0

    for data in datas:
        stride = len(data[0]) if len(data) > 0 else 0
        vertex_strides.append(stride)
        vertex_stride_points.append(ctypes.c_void_p(accStridePoint))
        accStridePoint += stride * np.nbytes[dtype]
    vertex_buffer_size = accStridePoint
    vertex_stride_range = range(len(vertex_strides))

    vertex_array = glGenVertexArrays(1)
    glBindVertexArray(vertex_array)

    vertex_datas = np.hstack(datas).astype(dtype)
    vertex_buffer = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
    glBufferData(GL_ARRAY_BUFFER, vertex_datas, GL_STATIC_DRAW)

    index_buffer_size = indices.nbytes
    index_buffer = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, index_buffer)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_buffer_size, indices, GL_STATIC_DRAW)

    # Create Texture
    texture_buffer = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_buffer)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glBindTexture(GL_TEXTURE_2D, 0)

    render_target_buffer = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, render_target_buffer)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(0))
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glBindTexture(GL_TEXTURE_2D, 0)

    # frame buffer
    frame_buffer = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, frame_buffer)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, render_target_buffer, 0)
    glReadBuffer(GL_COLOR_ATTACHMENT0)
    glDrawBuffers(0, [GL_COLOR_ATTACHMENT0, ])
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_TEXTURE_2D, 0, 0)
    glViewport(0, 0, width, height)

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
    if gl_error != GL_FRAMEBUFFER_COMPLETE:
        logger.error("glCheckFramebufferStatus error %d." % gl_error)

    # bind program
    glUseProgram(program)

    # bind texture
    texture_location = glGetUniformLocation(program, "texture_font")
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture_buffer)
    glUniform1i(texture_location, 0)

    # Bind Vertex Array
    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)

    for layout_location in vertex_stride_range:
        glEnableVertexAttribArray(layout_location)
        glVertexAttribPointer(layout_location, vertex_strides[layout_location], GL_FLOAT, GL_FALSE,
                              vertex_buffer_size, vertex_stride_points[layout_location])

    # bind index buffer
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, index_buffer)

    # Draw Quad
    glDrawElements(GL_TRIANGLES, index_buffer_size, GL_UNSIGNED_INT, ctypes.c_void_p(0))

    # blit frame buffer
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)  # the default framebuffer active
    glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_LINEAR)

    # Save
    glBindTexture(GL_TEXTURE_2D, texture_buffer)
    save_image_data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_UNSIGNED_BYTE)
    glBindTexture(GL_TEXTURE_2D, 0)

    save_image_data = np.array(list(save_image_data), dtype=np.uint8)
    save_image_data = save_image_data.reshape(width * 3, height)

    # save_image = Image.fromarray(save_image_data, 'RGB')
    save_image = Image.fromarray(save_image_data)
    save_image.show()


def generate_font_data(resource_name, unicode_name, range_min, range_max, source_filepath, preview_path=''):
    logger.info("Convert Font %s %s : %s" % (resource_name, unicode_name, source_filepath))

    back_ground_color = (0, 0, 0)
    font_color = (255, 255, 255)
    font_size = 36
    padding = 8
    count = abs(range_max - range_min) + 1
    count_horizontal = int(math.ceil(math.sqrt(count)))
    texture_size = font_size * count_horizontal
    # texture_size = (2 ** math.ceil(math.log2(texture_size))) if 4 < texture_size else 4

    if texture_size > 8096:
        logger.error("%s texture size is too large. %d" % (unicode_name, texture_size))
        return None

    try:
        unicode_font = ImageFont.truetype(source_filepath, font_size - padding * 2)
    except:
        logger.error(traceback.format_exc())
        return None

    image = Image.new("RGB", (texture_size, texture_size), back_ground_color)
    draw = ImageDraw.Draw(image)
    # draw.fontmode = "1"  # "1":aliasing, "L":anti aliasing

    unicode_index = range_min
    for y in range(count_horizontal):
        for x in range(count_horizontal):
            unicode_text = chr(unicode_index)  # u"\u2605" + u"\u2606" + u"Текст на русском" + u"파이썬"
            draw.text((x * font_size + padding, y * font_size + padding), unicode_text, font=unicode_font, fill=font_color)
            unicode_index += 1
            if unicode_index >= range_max:
                break
        else:
            continue
        break

    # save for preview
    if preview_path:
        texture_name = "_".join([resource_name, unicode_name])
        image.save(os.path.join(preview_path, texture_name + ".png"))

    data = image.tobytes("raw", image.mode, 0, -1)
    texture_datas = dict(
        texture_type=Texture2D,
        image_mode=image.mode,
        width=image.size[0],
        height=image.size[1],
        data=data
    )

    font_data = dict(
        unicode_name=unicode_name,
        unicode_range=(range_min, range_max),
        text_count=count,
        font_size=font_size,
        texture=texture_datas
    )

    # SDF(image)

    return font_data


if __name__ == '__main__':
    language_infos = dict(
        ascii=('Basic Latin', 0x20, 0x7F),  # 32 ~ 127
        korean=('Hangul Syllables', 0xAC00, 0xD7AF),  # 44032 ~ 55215
    )

    resource_name = 'NanumBarunGothic'
    font_filepath = 'Resource/Externals/Fonts/NanumBarunGothic.ttf'
    preview_save_path = 'Resource/Fonts'

    for language in language_infos:
        unicode_name, range_min, range_max = language_infos[language]
        font_data = generate_font_data(
            resource_name,
            unicode_name,
            range_min,
            range_max,
            font_filepath,
            preview_save_path
        )
