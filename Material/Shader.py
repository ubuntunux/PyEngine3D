# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import re
import traceback

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader

from Core import logger
from Utilities import getClassName, Attributes

"""
example) re.sub(reInsertMaterialBlock,
    "\n\n/* Begin : Material Template */\n" + material + "\n/* End : Material Template */\n\nvoid main()", shader, 1)
"""
reInsertMaterialBlock = re.compile("void\s*main\s*\(\s*\)")


class Shader:
    shaderType = None

    def __init__(self, shaderName, shaderSource):
        logger.info("Create " + getClassName(self) + " : " + shaderName)
        self.name = shaderName
        self.source = shaderSource
        self.attribute = Attributes()

    def compile(self, material_template):
        shader = glCreateShader(self.shaderType)

        shader_code = re.sub(reInsertMaterialBlock,
                             "\n\n/* Begin : Material Template */\n" +
                             material_template +
                             "\n/* End : Material Template */\n\nvoid main()",
                             self.source, 1)
        # Compile shaders
        try:
            glShaderSource(shader, shader_code)
            glCompileShader(shader)
            if glGetShaderiv(shader, GL_COMPILE_STATUS) != 1 or True:
                infoLog = glGetShaderInfoLog(shader)
                if infoLog:
                    if type(infoLog) == bytes:
                        infoLog = infoLog.decode("utf-8")
                    logger.error("%s shader error!!!\n" % self.name + infoLog)
                else:
                    logger.info("%s shader complete." % self.name)
        except:
            logger.error(traceback.format_exc())
        return shader

    def __del__(self):
        pass

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        return self.attribute


class VertexShader(Shader):
    shaderType = GL_VERTEX_SHADER


class FragmentShader(Shader):
    shaderType = GL_FRAGMENT_SHADER
