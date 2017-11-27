# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import configparser
from collections import OrderedDict
import copy
import os
import re
import codecs
import traceback
import uuid

from Utilities import GetClassName, Attributes, Logger
from Common import logger

reInclude = re.compile('\#include\s+[\"|\<](.+?)[\"|\>]')  # [include file name, ]
reVersion = re.compile("(\#version\s+.+)")  # [version code, ]
reComment = re.compile("\/\*.+?\*\/", re.DOTALL)
reMacroStart = re.compile('\#(define|undef|endif|ifdef|ifndef|if|elif|else)\s*(.*)')  # [macro type, expression]
reDefineMacro = re.compile('\#define\s*(.*)')  # [macro type, expression]
reVariable = re.compile('[a-z|A-Z|_]+[a-z|A-Z|_|0-9]*')

reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")  # [Variable Type, Variable Name]
reMacro = re.compile('\#(ifdef|ifndef|if|elif|else|endif)\s*(.*)')  # [macro type, expression]


class Shader:
    default_macros = dict(MATERIAL_COMPONENTS=1)

    def __init__(self, shaderName, file_path):
        logger.info("Load " + GetClassName(self) + " : " + shaderName)
        self.name = shaderName
        self.file_path = file_path
        self.shader_code = ""
        self.include_files = []

        try:
            f = codecs.open(file_path, mode='r', encoding='utf-8')
            self.shader_code = f.read()
            f.close()
        except:
            self.shader_code = ""
            logger.error("Failed %s file open" % file_path)
        self.attribute = Attributes()

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        return self.attribute

    def get_vertex_shader_code(self, shader_version, external_macros={}):
        return self.__parsing_final_code__('VERTEX_SHADER', shader_version, external_macros)

    def get_fragment_shader_code(self, shader_version, external_macros={}):
        return self.__parsing_final_code__('FRAGMENT_SHADER', shader_version, external_macros)

    def __parsing_final_code__(self, shaderType, shader_version, external_macros):
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
        combined_macros[shaderType] = "1"

        # external macro
        for macro in external_macros:
            if external_macros[macro] is None or external_macros[macro] is '':
                combined_macros[macro] = 0
            else:
                combined_macros[macro] = external_macros[macro]

        # insert shader version - ex) #version 430 core
        final_code_lines = [shader_version, ]

        # insert defines to final code
        for macro in combined_macros:
            final_code_lines.append("#define %s %s" % (macro, str(combined_macros[macro])))

        # insert version as comment
        include_files = dict()  # { 'filename': uuid }
        shader_file_dir = os.path.split(self.file_path)[0]

        # do parsing
        line_num = 0
        macro_depth = 0
        macro_result = [True, ]
        macro_code_remove = True
        while line_num < len(code_lines):
            code = code_lines[line_num]
            line_num += 1

            # remove comment
            if "//" in code:
                code = code.split("//")[0]

            # macro parsing
            m = re.search(reMacroStart, code)
            if m is not None:
                macro, expression = m.groups()
                expression = expression.strip()
                if macro == 'define' or macro == 'undef':
                    define_expression = expression.split('(')[0].strip()
                    if ' ' in define_expression:
                        define_name, define_value = define_expression.split(' ', 1)
                    else:
                        define_name, define_value = define_expression, None

                    # check external macro
                    if macro == 'define' and define_name in external_macros:
                        continue  # ignore legacy macro

                    if macro == 'define' and define_name not in combined_macros:
                        combined_macros[define_name] = define_value
                    elif macro == 'undef' and define_name in combined_macros:
                        combined_macros.pop(define_name)
                elif macro == 'ifdef':
                    macro_depth += 1
                    if expression in combined_macros:
                        macro_result.append(True)
                    else:
                        macro_result.append(False)
                elif macro == 'ifndef':
                    macro_depth += 1
                    if expression not in combined_macros:
                        macro_result.append(True)
                    else:
                        macro_result.append(False)
                elif macro == 'if' or macro == 'elif' and not macro_result[macro_depth]:
                    variables = re.findall(reVariable, expression)
                    variables.sort(key=lambda x: len(x), reverse=True)
                    for variable in variables:
                        if variable in combined_macros:
                            while True:
                                final_value = combined_macros[variable]
                                if final_value not in combined_macros:
                                    break
                                variable = final_value
                            expression = re.sub(reVariable, str(final_value), expression, 1)
                    expression = expression.replace('&&', ' and ')
                    expression = expression.replace('||', ' or ')
                    # expression = re.sub('\!?!\=', 'not ', expression)
                    # Important : To avoid errors, convert the undecalred variables to zero.
                    expression = re.sub(reVariable, '0', expression)
                    result = True if eval(expression) else False
                    if macro == 'if':
                        macro_depth += 1
                        macro_result.append(result)
                    elif macro == 'elif':
                        macro_result[macro_depth] = result
                elif macro == 'else':
                    macro_result[macro_depth] = not macro_result[macro_depth]
                elif macro == 'endif':
                    macro_depth -= 1
                    macro_result.pop()
            # be in failed macro block. continue
            elif not macro_result[macro_depth]:
                if not macro_code_remove:
                    # make comment
                    final_code_lines.append("// " + code)
                continue

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
                            include_files[include_file] = unique_id

                            if include_file not in self.include_files:
                                self.include_files.append(include_file)
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

    def parsing_macros(self, vertexShaderCode, fragmentShaderCode):
        vextex_macros = re.findall(reDefineMacro, vertexShaderCode)
        fragment_macros = re.findall(reDefineMacro, fragmentShaderCode)
        macros = OrderedDict()

        def is_reserved_word(define_name):
            return define_name in ('MATERIAL_COMPONENTS', 'VERTEX_SHADER', 'FRAGMENT_SHADER') or \
                   define_name.startswith('UUID_')

        for expression in vextex_macros + fragment_macros:
            define_expression = expression.split('(')[0].strip()
            if ' ' in define_expression:
                define_name, define_value = define_expression.split(' ', 1)
            else:
                define_name, define_value = define_expression, ''

            define_name = define_name.strip()
            define_value = define_value.strip()
            try:
                define_value = eval(define_value)
            except:
                pass

            if not is_reserved_word(define_name):
                macros[define_name] = define_value

        all_variables = re.findall(reVariable, re.sub(reDefineMacro, '', vertexShaderCode))
        all_variables += re.findall(reVariable, re.sub(reDefineMacro, '', fragmentShaderCode))
        final_macros = {}
        for macro in macros:
            if macro in all_variables:
                final_macros[macro] = macros[macro]
        return final_macros

    def parsing_uniforms(self, vertexShaderCode, fragmentShaderCode):
        vextex_uniforms = re.findall(reFindUniform, vertexShaderCode)
        fragment_uniforms = re.findall(reFindUniform, fragmentShaderCode)
        uniforms = []
        for uniform in vextex_uniforms + fragment_uniforms:
            uniform_type, uniform_name = uniform
            if '[' in uniform_name:
                uniform = (uniform_type, uniform_name[:uniform_name.find('[')])
            if uniform not in uniforms:
                uniforms.append(uniform)
        return uniforms

    def parsing_material_components(self, vertexShaderCode, fragmentShaderCode):
        material_components = []
        code_list = [vertexShaderCode, fragmentShaderCode]
        for code in code_list:
            depth = 0
            is_in_material_block = False

            # remove comment block
            code = re.sub(reComment, "", code)
            code_lines = code.splitlines()

            for code_line in code_lines:
                # remove comment
                if "//" in code_line:
                    code_line = code_line.split("//")[0]

                m = re.search(reMacro, code_line)
                # find macro
                if m is not None:
                    macro_type, macro_value = [group.strip() for group in m.groups()]
                    if macro_type in ('ifdef', 'ifndef', 'if'):
                        # increase depth
                        if is_in_material_block:
                            depth += 1
                        # start material block
                        elif macro_type == 'ifdef' and 'MATERIAL_COMPONENTS' == macro_value.split(" ")[0]:
                            is_in_material_block = True
                            depth = 1
                    elif macro_type == 'endif' and is_in_material_block:
                        depth -= 1
                        if depth == 0:
                            # exit material block
                            is_in_material_block = False
                # gather common code in material component
                elif is_in_material_block:
                    material_components.append(code_line)
        return re.findall(reFindUniform, "\n".join(material_components))
