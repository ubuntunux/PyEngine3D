import copy
import os
import re
import codecs
import traceback

reInclude = re.compile('\#include\s+[\"|\<](.+?)[\"|\>]')  # [include file name, ]
reDefine = re.compile('\#(define|undef)\s+(.+)')
reMacroStart = re.compile('(.*?)\#(ifdef\s+|ifndef\s+|if[\s+|\(])(.+)')  # [prev code, macro type, expression]
reMacroEnd = re.compile('(.*?)\#endif')  # [prev code, ]
reVersion = re.compile("(\#version\s+.+?\n)")  # [version, ]


class ShaderCode:
    type = "ShaderCode"

    def __init__(self):
        self.code_blocks = []
        self.include_blocks = []
        self.macro_blocks = []
        self.block_list = []
        self.valid = False

    def get_final_code_list(self):
        final_code_list = []
        # final_code_list.append("//-----------------------------------------------")
        # final_code_list.append("// Start : " + self.type)
        # final_code_list.append("//-----------------------------------------------")
        for block in self.block_list:
            if isinstance(block, CodeBlock):
                final_code_list.append(block.code)
            else:
                final_code_list += block.get_final_code()
        # final_code_list.append("//-----------------------------------------------")
        # final_code_list.append("// End : " + self.type)
        # final_code_list.append("//-----------------------------------------------")
        return final_code_list

    def append_code_block(self, code):
        code_block = CodeBlock(code)
        self.code_blocks.append(code_block)
        self.block_list.append(code_block)

    def parsing(self, shader_file_dir, code_lines):
        line_num = 0
        while line_num < len(code_lines):
            code = code_lines[line_num]
            line_num += 1
            # find include block
            m = re.search(reInclude, code)
            if m is not None:
                valid = False
                include_file = os.path.join(shader_file_dir, m.groups()[0])
                if os.path.exists(include_file):
                    try:
                        f = codecs.open(include_file, mode='r', encoding='utf-8')
                        include_source = f.read()
                        f.close()
                        include_code_lines = include_source.splitlines()
                        # create include block
                        include_block = IncludeBlock(include_file)
                        self.include_blocks.append(include_block)
                        self.block_list.append(include_block)
                        # parsing include file
                        include_block.parsing(shader_file_dir, include_code_lines)
                        valid = True
                    except:
                        pass
                if not valid:
                    logger.error("Cannot open %s file." % include_file)
                continue

            # find macro block
            m = re.search(reMacroStart, code)
            if m is not None:
                # start/end of macro block code.
                start_of_macro_block_code = code.strip()
                end_of_macro_block_code = ""
                # fetch
                prev_code, macro_type, expression = m.groups()
                macro_type = macro_type.strip()
                expression = expression.strip()
                # append previous code
                if prev_code:
                    self.append_code_block(prev_code)
                # create macro block
                macro_block = MacroBlock(macro_type, expression)
                self.macro_blocks.append(macro_block)
                self.block_list.append(macro_block)
                # insert start of macro block code.
                macro_block.append_code_block(start_of_macro_block_code)
                # gather macro block
                macro_code_lines = []
                macro_depth = 1
                while line_num < len(code_lines):
                    code = code_lines[line_num]
                    line_num += 1
                    m = re.search(reMacroStart, code)
                    # start other macro block start
                    if m is not None:
                        macro_depth += 1
                    else:
                        # find end of macro block
                        m = re.search(reMacroEnd, code)
                        if m is not None:
                            macro_depth -= 1
                            # end of macro block
                            if macro_depth == 0:
                                # end of macro block code.
                                end_of_macro_block_code = code.strip()
                                break
                    # append code in macro block
                    macro_code_lines.append(code)
                # parsing macro block
                macro_block.parsing(shader_file_dir, macro_code_lines)
                # insert end of macro block code
                macro_block.append_code_block(end_of_macro_block_code)
                continue
            # append code block
            self.append_code_block(code)
        self.valid = True


class CodeBlock:
    def __init__(self, code):
        self.code = code


class MacroBlock(ShaderCode):
    type = "MacroBlock"

    def __init__(self, macro_type, expression):
        ShaderCode.__init__(self)
        self.macro_type = macro_type
        self.expression = expression


class IncludeBlock(ShaderCode):
    type = "IncludeBlock"

    def __init__(self, include_file):
        ShaderCode.__init__(self)
        self.filename = include_file


def shader_parsing(shader_file_dir, shader_source, macros=None):
    macros = copy.copy(macros) if macros is not None else dict()
    final_code = copy.copy(shader_source)
    code_lines = final_code.splitlines()
    shader_code = ShaderCode()
    shader_code.parsing(shader_file_dir, code_lines)
    final_code_list = shader_code.get_final_code_list()
    final_code = "\n".join(final_code_list)

    # version directive must be first statement and may not be repeated
    versions = re.findall(reVersion, final_code)
    if versions:
        versions.sort()
        # first, remove all version macro
        final_code = re.sub(reVersion, "", final_code)
        # second, insert highest version at first line.
        final_code = versions[-1] + final_code
    # logger.info(final_code)
    return final_code