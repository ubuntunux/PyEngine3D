# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import configparser
from collections import OrderedDict
import copy
import os
import re
import codecs
import traceback
import uuid

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader

from Core import logger
import Resource
from Utilities import GetClassName, Attributes

reInclude = re.compile('\#include\s+[\"|\<](.+?)[\"|\>]')  # [include file name, ]
reVersion = re.compile("(\#version\s+.+)")  # [version code, ]
reComment = re.compile("\/\*.+?\*\/", re.DOTALL)
reMacroStart = re.compile('\#(define|undef|ifdef|ifndef|if|elif|else)\s*(.*)')  # [macro type, expression]
reMacroEnd = re.compile('\#endif')


class Shader:
    default_macros = dict(MATERIAL_COMPONENTS=1)

    def __init__(self, shaderName, file_path):
        logger.info("Create " + GetClassName(self) + " : " + shaderName)
        self.name = shaderName
        self.file_path = file_path
        self.shader_code = ""

        try:
            f = codecs.open(file_path, mode='r', encoding='utf-8')
            self.shader_code = f.read()
            f.close()
        except:
            self.shader_code = ""
            logger.info("Failed %s file open" % file_path)
        self.attribute = Attributes()

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        return self.attribute

    def parsing_final_code(self, shaderType, external_macros):
        if self.shader_code == "" or self.shader_code is None:
            return

        # remove comment block
        shader_code = re.sub(reComment, "", self.shader_code)
        code_lines = shader_code.splitlines()

        # combine macro
        combined_macros = OrderedDict()
        # default macro
        for macro in self.default_macros:
            combined_macros[macro] = self.default_macros[macro]
        # shader type macro
        if shaderType == GL_VERTEX_SHADER:
            combined_macros['VERTEX_SHADER'] = "1"
        elif shaderType == GL_FRAGMENT_SHADER:
            combined_macros['FRAGMENT_SHADER'] = "1"
        else:
            raise BaseException("Error!! Set valid shaderType.")
            return ""
        # external macro
        if external_macros is not None:
            for macro in external_macros:
                combined_macros[macro] = external_macros[macro]

        # insert defines to final code
        final_code_lines = ["", ]  # for version define
        for macro in combined_macros:
            final_code_lines.append("#define %s %s" % (macro, combined_macros[macro]))

        # insert version as comment
        include_files = dict()  # { 'filename': uuid }
        shader_file_dir = os.path.split(self.file_path)[0]

        # do parsing
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
                if final_code_lines[0] == "" or version_code > final_code_lines[0]:
                    final_code_lines[0] = version_code
                continue

            # find include block
            m = re.search(reInclude, code)
            if m is not None:
                valid = True
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
                        valid = False

                    if valid:
                        if include_file in include_files:
                            unique_id = include_files[include_file]
                        else:
                            unique_id = "UUID_" + str(uuid.uuid3(uuid.NAMESPACE_DNS, include_file)).replace("-", "_")
                        # insert included code
                        final_code_lines.append("//------------ INCLUDE -------------//")
                        final_code_lines.append("// " + code)  # include comment
                        include_code_lines.insert(0, "#ifndef %s" % unique_id)
                        include_code_lines.insert(1, "#define %s" % unique_id)
                        include_code_lines.append("#endif /* %s */" % unique_id)
                        code_lines = include_code_lines + code_lines[line_num:]
                        line_num = 0
                if not valid:
                    logger.error("Cannot open %s file." % include_file)
                continue
            # append code block
            final_code_lines.append(code)
        return '\n'.join(final_code_lines)
