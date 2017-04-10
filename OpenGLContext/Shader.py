# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import configparser
from collections import OrderedDict
import copy
import os
import re
import codecs
import traceback
import uuid

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader

from Core import logger
import Resource
from Utilities import GetClassName, Attributes
from .UniformBuffer import CreateUniformBuffer, UniformTexture2D

reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")  # [Variable Type, Variable Name]
reInclude = re.compile('\#include\s+[\"|\<](.+?)[\"|\>]')  # [include file name, ]
reVersion = re.compile("(\#version\s+.+)")  # [version code, ]
reComment = re.compile("\/\*.+?\*\/", re.DOTALL)

class ShaderCodeParser:
    def __init__(self):
        self.code_list = []
        self.include_files = dict()  # { 'filename':uuid }
        self.valid = True

    def get_final_code(self):
        return "\n".join(self.code_list)

    def parsing(self, shader_file_dir, code_lines, macros):
        # insert version as comment
        self.code_list.append("")
        # insert macros
        for macro in macros:
            self.code_list.append("#define %s %s" % (macro, macros[macro]))

        # parsing
        line_num = 0
        while line_num < len(code_lines):
            code = code_lines[line_num]
            line_num += 1

            # remove comment
            if "//" in code:
                code = code.split("//")[0]

            # is version code?
            m = re.search(reVersion, code)
            if m is not None:
                version_code = m.groups()[0].strip()
                if self.code_list[0] == "" or version_code > self.code_list[0]:
                    self.code_list[0] = version_code
                continue

            # find include block
            m = re.search(reInclude, code)
            if m is not None:
                include_file = os.path.join(shader_file_dir, m.groups()[0])

                # insert include code
                if os.path.exists(include_file):
                    try:
                        f = codecs.open(include_file, mode='r', encoding='utf-8')
                        include_source = f.read()
                        # remove comment block
                        include_source = re.sub(reComment, "", include_source)
                        include_code_lines = include_source.splitlines()
                        f.close()
                    except:
                        self.valid = False

                    if self.valid:
                        if include_file in self.include_files:
                            unique_id = self.include_files[include_file]
                        else:
                            unique_id = "UUID_" + str(uuid.uuid3(uuid.NAMESPACE_DNS, include_file)).replace("-", "_")
                        # insert included code
                        self.code_list.append("//------------ INCLUDE -------------//")
                        self.code_list.append("// " + code)  # include comment
                        include_code_lines.insert(0, "#ifndef %s" % unique_id)
                        include_code_lines.insert(1, "#define %s" % unique_id)
                        include_code_lines.append("#endif /* %s */" % unique_id)
                        code_lines = include_code_lines + code_lines[line_num:]
                        line_num = 0
                if not self.valid:
                    logger.error("Cannot open %s file." % include_file)
                continue

            # append code block
            self.code_list.append(code)


class Shader:
    def __init__(self, shaderName, file_path):
        logger.info("Create " + GetClassName(self) + " : " + shaderName)
        self.name = shaderName
        self.file_path = file_path

        # default shader macros
        self.macros = dict(MATERIAL_COMPONENTS=1)

        try:
            f = codecs.open(file_path, mode='r', encoding='utf-8')
            self.source = f.read()
            f.close()
        except:
            self.source = ""
            logger.info("Failed %s file open" % file_path)
        self.attribute = Attributes()

    def compile(self, shaderType, macros=None):
        """
        :param shaderType: GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
        :param macros: dictionary
        """
        if self.source == "" or self.source is None:
            return

        # combine macros
        combined_macros = OrderedDict()
        if shaderType == GL_VERTEX_SHADER:
            combined_macros['VERTEX_SHADER'] = "1"
        elif shaderType == GL_FRAGMENT_SHADER:
            combined_macros['FRAGMENT_SHADER'] = "1"
        else:
            raise BaseException("Error!! Set valid shaderType.")
            return None
        for macro in self.macros:
            combined_macros[macro] = self.macros[macro]

        shader = glCreateShader(shaderType)
        shader_file_dir = os.path.split(self.file_path)[0]

        # remove comment block
        shader_code = re.sub(reComment, "", self.source)

        # Shader source code parsing
        code_lines = shader_code.splitlines()
        shaderParser = ShaderCodeParser()
        shaderParser.parsing(shader_file_dir, code_lines, combined_macros)
        shader_code = shaderParser.get_final_code()
        # print("=" * 40)
        # print(self.file_path)
        # print(shader_code)
        # print("=" * 40)
        # print("")

        try:
            # Compile shaders
            glShaderSource(shader, shader_code)
            glCompileShader(shader)
            if glGetShaderiv(shader, GL_COMPILE_STATUS) != 1 or True:
                infoLog = glGetShaderInfoLog(shader)
                if infoLog:
                    if type(infoLog) == bytes:
                        infoLog = infoLog.decode("utf-8")
                    logger.error("%s %s shader compile error.\n%s" % (self.name, shaderType.name, infoLog))
                else:
                    # complete
                    logger.info("Complete %s %s compile." % (self.name, shaderType.name))
                    return shader
        except:
            logger.error(traceback.format_exc())
        return None

    def __del__(self):
        pass

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        return self.attribute


class Material:
    def __init__(self, combined_material_name, shader_name, macros=None):
        self.valid = False
        logger.info("Create %s material." % combined_material_name)
        self.name = combined_material_name
        self.program = -1
        self.uniform_buffers = OrderedDict({})  # Declaration order is important.
        self.Attributes = Attributes()

        # build and link the program
        resourceMgr = Resource.ResourceManager.instance()
        shader = resourceMgr.getShader(shader_name)
        vertexShader = shader.compile(GL_VERTEX_SHADER, macros) if shader else None
        fragmentShader = shader.compile(GL_FRAGMENT_SHADER, macros) if shader else None

        if vertexShader is None or fragmentShader is None:
            logger.error("%s material compile error." % shader_name)
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

        # material_contents = shader.get_material_contents()
        material_contents = '''
            uniform int enable_blend;
            uniform float brightness;
            uniform vec4 emissive_color;
            uniform vec4 diffuse_color;
            uniform sampler2D texture_diffuse;
            uniform sampler2D texture_normal;
                '''

        uniform_contents = re.findall(reFindUniform, material_contents)
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
