# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import configparser
from collections import OrderedDict
import os
import re
import codecs
import traceback

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader

from Core import logger
import Resource
from Utilities import GetClassName, Attributes
from .UniformBuffer import CreateUniformBuffer, UniformTexture2D


"""
example) re.sub(reInsertMaterialBlock,
    "\n\n/* Begin : Material Template */\n" + material + "\n/* End : Material Template */\n\nvoid main()", shader, 1)
"""
reInsertMaterialBlock = re.compile("void\s*main\s*\(\s*\)")
reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")
reInclude = re.compile('\#include\s+[\"|\<](.+?)[\"|\>]')
reVersion = re.compile("(\#version\s+.+?\n)")


def shader_parsing(shader_file_dir, shader_source, material_template, macros={}):
    # Insert material template
    final_code = re.sub(reInsertMaterialBlock,
                        "\n/* Begin : Material Template */\n" +
                        material_template +
                        "\n/* End : Material Template */\n\nvoid main()",
                        shader_source, 1)
    # Insert macros
    macro_str = ""
    for macro in macros:
        macro_str += "#define %s %d\n" % (macro, macros[macro])
        final_code = macro_str + final_code

    # include command
    while True:
        m = re.search(reInclude, final_code)
        if m:
            include_file = os.path.join(shader_file_dir, m.groups()[0])
            if os.path.exists(include_file):
                try:
                    f = codecs.open(include_file, mode='r', encoding='utf-8')
                    include_source = f.read()
                    f.close()
                    # OK : replace include statement to source code
                    final_code = re.sub(reInclude, include_source, final_code, 1)
                    continue
                except:
                    pass
            # remove include statement
            final_code = re.sub(reInclude, "", final_code, 1)
            logger.error("Cannot open %s file." % include_file)
            continue
        break

    # version directive must be first statement and may not be repeated
    versions = re.findall(reVersion, final_code)
    if versions:
        versions.sort()
        # first, remove all version macro
        final_code = re.sub(reVersion, "", final_code)
        # second, insert highest version at first line.
        final_code = versions[-1] + final_code
    return final_code


class Shader:
    shaderType = None
    macros = dict()

    def __init__(self, shaderName, file_path):
        logger.info("Create " + GetClassName(self) + " : " + shaderName)
        self.name = shaderName
        self.file_path = file_path
        try:
            f = codecs.open(file_path, mode='r', encoding='utf-8')
            self.source = f.read()
            f.close()
        except:
            self.source = ""
            logger.info("Failed %s file open" % file_path)
        self.attribute = Attributes()

    def compile(self, material_template):
        if self.source == "" or self.source is None:
            return

        shader = glCreateShader(self.shaderType)
        shader_file_dir = os.path.split(self.file_path)[0]
        shader_code = shader_parsing(shader_file_dir, self.source, material_template, self.macros)

        try:
            # Compile shaders
            glShaderSource(shader, shader_code)
            glCompileShader(shader)
            if glGetShaderiv(shader, GL_COMPILE_STATUS) != 1 or True:
                infoLog = glGetShaderInfoLog(shader)
                if infoLog:
                    if type(infoLog) == bytes:
                        infoLog = infoLog.decode("utf-8")
                    logger.error("%s %s shader compile error.\n%s" % (self.name, self.shaderType.name, infoLog))
                else:
                    # complete
                    logger.info("Complete %s %s compile." % (self.name, self.shaderType.name))
                    return shader
            return None

        except:
            logger.error(traceback.format_exc())
        return None

    def __del__(self):
        pass

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        return self.attribute


class VertexShader(Shader):
    shaderType = GL_VERTEX_SHADER
    macros = dict(VERTEX_SHADER=1)


class FragmentShader(Shader):
    shaderType = GL_FRAGMENT_SHADER
    macros = dict(FRAGMENT_SHADER=1)


class Material:
    def __init__(self, mat_name, vs_name, fs_name, material_template):
        self.valid = False
        logger.info("%s material is combined : vs(%s), fs(%s)" % (mat_name, vs_name, fs_name))
        self.name = mat_name
        self.program = -1
        self.uniform_buffers = OrderedDict({})  # Declaration order is important.
        self.Attributes = Attributes()

        # build and link the program
        resourceMgr = Resource.ResourceManager.instance()
        vs = resourceMgr.getVertexShader(vs_name)
        fs = resourceMgr.getFragmentShader(fs_name)
        vertexShader = vs.compile(material_template) if vs else None
        fragmentShader = fs.compile(material_template) if fs else None

        if vertexShader is None or fragmentShader is None:
            logger.error("%s material compile error." % mat_name)
            return

        # create program
        self.program = glCreateProgram()
        glAttachShader(self.program, vertexShader)
        glAttachShader(self.program, fragmentShader)
        glLinkProgram(self.program)

        # delete shader
        glDetachShader(self.program, vertexShader)
        glDetachShader(self.program, fragmentShader)
        glDeleteShader(vertexShader)
        glDeleteShader(fragmentShader)

        # build uniform buffer variable
        textureIndex = 0
        uniform_contents = re.findall(reFindUniform, material_template)
        for uniform_type, uniform_name in uniform_contents:
            uniform_buffer = CreateUniformBuffer(self.program, uniform_type, uniform_name)
            # Important : set texture binding index
            if uniform_buffer.__class__ == UniformTexture2D:
                uniform_buffer.set_texture_index(textureIndex)
                textureIndex += 1
            self.uniform_buffers[uniform_name] = uniform_buffer
        self.valid = True

    def __del__(self):
        pass

    def delete(self):
        glDeleteProgram(self.program)

    def useProgram(self):
        glUseProgram(self.program)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('type', type(self))
        return self.Attributes
