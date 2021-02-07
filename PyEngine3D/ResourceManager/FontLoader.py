import math
import os
import io
import os
from ctypes import c_void_p

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import *

from PIL import Image, ImageDraw, ImageFont, ImageFilter

import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.Common.Constants import *
from PyEngine3D.Utilities import *

SIMPLE_VERTEX_SHADER = '''
#version 430 core

layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec2 vs_in_texCoord;

layout (location = 0) out vec3 vs_out_position;
layout (location = 1) out vec2 vs_out_texCoord;

void main() {
    vs_out_texCoord = vs_in_texCoord;
    vs_out_position = vs_in_position;
    gl_Position = vec4(vs_in_position, 1.0);
}'''

SIMPLE_PIXEL_SHADER = '''
#version 430 core

uniform sampler2D texture_font;
uniform float font_size;

layout (location = 0) in vec3 vs_out_position;
layout (location = 1) in vec2 vs_out_texCoord;
layout (location = 0) out vec4 fs_output;

void main(void)
{
    vec2 texture_font_size = textureSize(texture_font, 0);
    float min_dist = 1.0;
    vec2 font_count = ceil(texture_font_size / font_size);
    vec2 start_tex_coord = floor(vs_out_texCoord.xy * font_count) / font_count;

    const float diff = 0.9;
    float value = texture(texture_font, vs_out_texCoord.xy).x;

    if(value < diff)
    {
        for(float y=0.0; y<font_size; y+=1.0)
        {
            for(float x=0.0; x<font_size; x+=1.0)
            {
                vec2 other_tex_coord = start_tex_coord + vec2(x, y) / texture_font_size;
                float other_value = texture(texture_font, other_tex_coord).x;

                if((other_value - value) > (1.0 - diff))
                {
                    float dist = length(other_tex_coord - vs_out_texCoord.xy);
                    if(dist < min_dist)
                    {
                        min_dist = dist;
                    }
                }
            }
        }
    }
    else
    {
        min_dist = 0.0;
    }

    //fs_output.xyz = vec3(1.0 - min_dist * max(font_count.x, font_count.y));
    fs_output.xyz = vec3(1.0 - min_dist);
    fs_output.w = 1.0;
}
'''


def DistanceField(font_size, image_width, image_height, image_mode, image_data):
    # GL setting
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

    if glGetShaderiv(vertex_shader, GL_COMPILE_STATUS) != 1 or True:
        infoLogs = glGetShaderInfoLog(vertex_shader)
        if infoLogs:
            if type(infoLogs) == bytes:
                infoLogs = infoLogs.decode("utf-8")
            print(infoLogs)

    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment_shader, SIMPLE_PIXEL_SHADER)
    glCompileShader(fragment_shader)

    if glGetShaderiv(fragment_shader, GL_COMPILE_STATUS) != 1 or True:
        infoLogs = glGetShaderInfoLog(fragment_shader)
        if infoLogs:
            if type(infoLogs) == bytes:
                infoLogs = infoLogs.decode("utf-8")
            print(infoLogs)

    # Create Program
    program = glCreateProgram()

    # Link Shaders
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)

    # delete shader
    glDetachShader(program, vertex_shader)
    glDetachShader(program, fragment_shader)
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    # Vertex Array Data
    dtype = np.float32
    positions = np.array([(-1, 1, 0), (-1, -1, 0), (1, -1, 0), (1, 1, 0)], dtype=np.float32)
    texcoords = np.array([(0, 1), (0, 0), (1, 0), (1, 1)], dtype=np.float32)
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)

    # data serialize
    vertex_datas = np.hstack([positions, texcoords]).astype(dtype)

    # crate vertex array
    vertex_array = glGenVertexArrays(1)
    glBindVertexArray(vertex_array)

    vertex_buffer = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
    glBufferData(GL_ARRAY_BUFFER, vertex_datas, GL_STATIC_DRAW)

    index_buffer_size = indices.nbytes
    index_buffer = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, index_buffer)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_buffer_size, indices, GL_STATIC_DRAW)

    # Create Texture
    texture_format = GL_RGBA
    if image_mode == 'RGB':
        texture_format = GL_RGB
    texture_buffer = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_buffer)
    glTexImage2D(GL_TEXTURE_2D, 0, texture_format, image_width, image_height, 0, texture_format, GL_UNSIGNED_BYTE,
                 image_data)
    glGenerateMipmap(GL_TEXTURE_2D)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glBindTexture(GL_TEXTURE_2D, 0)

    # Create RenderTarget
    render_target_buffer = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, render_target_buffer)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL_POINTER)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glBindTexture(GL_TEXTURE_2D, 0)

    # Create FrameBuffer
    frame_buffer = glGenFramebuffers(1)

    gl_error = glCheckFramebufferStatus(GL_FRAMEBUFFER)
    if gl_error != GL_FRAMEBUFFER_COMPLETE:
        logger.error("glCheckFramebufferStatus error %d." % gl_error)

    # Bind Frame Buffer
    glBindFramebuffer(GL_FRAMEBUFFER, frame_buffer)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, render_target_buffer, 0)
    glReadBuffer(GL_COLOR_ATTACHMENT0)
    glDrawBuffers(1, [GL_COLOR_ATTACHMENT0, ])
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_TEXTURE_2D, 0, 0)

    glViewport(0, 0, image_width, image_height)
    glClearColor(1.0, 1.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    # bind program
    glUseProgram(program)

    font_size_location = glGetUniformLocation(program, "font_size")
    glUniform1f(font_size_location, font_size)

    # bind texture
    texture_location = glGetUniformLocation(program, "texture_font")
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture_buffer)
    glUniform1i(texture_location, 0)

    # Bind Vertex Array
    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)

    vertex_position_size = positions[0].nbytes
    vertex_texcoord_size = texcoords[0].nbytes
    vertex_buffer_size = vertex_position_size + vertex_texcoord_size

    location = 0
    offset = 0
    stride = len(positions[0])
    glEnableVertexAttribArray(location)
    glVertexAttribPointer(location, stride, GL_FLOAT, GL_FALSE, vertex_buffer_size, c_void_p(offset))

    location = 1
    offset += vertex_position_size
    stride = len(texcoords[0])
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(location, stride, GL_FLOAT, GL_FALSE, vertex_buffer_size, c_void_p(offset))

    # bind index buffer
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, index_buffer)

    # Draw Quad
    glDrawElements(GL_TRIANGLES, index_buffer_size, GL_UNSIGNED_INT, NULL_POINTER)

    # Save
    glBindTexture(GL_TEXTURE_2D, render_target_buffer)
    save_image_data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_UNSIGNED_BYTE)
    glBindTexture(GL_TEXTURE_2D, 0)

    return save_image_data


def generate_font_data(resource_name, distance_field_font, anti_aliasing, font_size, padding, unicode_block_name,
                       range_min, range_max, source_filepath, preview_path=''):
    logger.info("Convert Font %s %s : %s" % (resource_name, unicode_block_name, source_filepath))

    back_ground_color = (0, 0, 0)
    font_color = (255, 255, 255)
    count = abs(range_max - range_min) + 1
    count_of_side = int(math.ceil(math.sqrt(count)))
    # make texture size to power of 2.
    # texture_size = (2 ** math.ceil(math.log2(texture_size))) if 4 < texture_size else 4

    try:
        unicode_font = ImageFont.truetype(source_filepath, font_size - padding * 2)
    except:
        logger.error(traceback.format_exc())
        return None

    max_font_size = font_size
    for unicode_index in range(range_min, range_max + 1):
        unicode_text = chr(unicode_index)  # u"\u2605" + u"\u2606" + u"Текст на русском" + u"파이썬"
        width, height = unicode_font.getsize(unicode_text)
        max_font_size = max(max_font_size, max(width, height))

    font_size = max_font_size

    texture_size = font_size * count_of_side

    if texture_size > 8096:
        logger.error("%s texture size is too large. %d" % (unicode_block_name, texture_size))
        return None

    image = Image.new("RGB", (texture_size, texture_size), back_ground_color)
    draw = ImageDraw.Draw(image)

    if anti_aliasing:
        draw.fontmode = "L"
    else:
        draw.fontmode = "1"

    unicode_index = range_min
    for y in range(count_of_side):
        for x in range(count_of_side):
            unicode_text = chr(unicode_index)  # u"\u2605" + u"\u2606" + u"Текст на русском" + u"파이썬"

            draw.text((x * font_size, y * font_size), unicode_text, font=unicode_font, fill=font_color)
            unicode_index += 1
            if unicode_index >= range_max:
                break
        else:
            continue
        break

    # Flip Vertical
    # image = image.transpose(Image.FLIP_TOP_BOTTOM)

    image_data = image.tobytes("raw", image.mode, 0, -1)

    if distance_field_font:
        image_data = DistanceField(font_size, image.size[0], image.size[1], image.mode, image_data)

    # save for preview
    if preview_path:
        texture_name = "_".join([resource_name, unicode_block_name])
        image = Image.frombytes(image.mode, image.size, image_data)
        image.save(os.path.join(preview_path, texture_name + ".png"))
        # image.show()

    font_data = dict(
        unicode_block_name=unicode_block_name,
        range_min=range_min,
        range_max=range_max,
        text_count=count,
        font_size=font_size,
        count_of_side=count_of_side,
        image_mode=image.mode,
        image_width=image.size[0],
        image_height=image.size[1],
        image_data=image_data,
        texture=None
    )

    return font_data
