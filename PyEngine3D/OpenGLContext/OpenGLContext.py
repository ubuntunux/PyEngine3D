import ctypes
import re
import traceback

import numpy as np
from OpenGL.GL import *
from OpenGL.raw.GL.VERSION import GL_1_1, GL_1_2, GL_3_0
from OpenGL.raw.GL import _types
from OpenGL import images, arrays

from PyEngine3D.Common import logger


# Function : IsExtensionSupported
# NeHe Tutorial Lesson: 45 - Vertex Buffer Objects
reCheckGLExtention = re.compile("GL_(.+?)_(.+)")


class OpenGLContext:
    last_vertex_array = -1
    last_program = 0
    gl_major_version = 0
    gl_minor_version = 0
    require_gl_major_version = 4
    require_gl_minor_version = 3
    GL_MAX_COMPUTE_WORK_GROUP_COUNT = None
    GL_MAX_COMPUTE_WORK_GROUP_SIZE = None
    GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS = None

    @staticmethod
    def initialize():
        def callglGetIntegeri_v(*args):
            try:
                return glGetIntegeri_v(*args)
            except:
                return [0, ]
                
        def callglGetIntegerv(*args):
            try:
                return glGetIntegerv(*args)
            except:
                return c_int(0)
                
        def callglGetString(*args):
            try:
                return glGetString(*args)
            except:
                return ""
                
        logger.info("=" * 30)

        infos = [GL_RENDERER, GL_VENDOR, GL_SHADING_LANGUAGE_VERSION]
        for info in infos:
            info_string = callglGetString(info)
            if type(info_string) == bytes:
                info_string = info_string.decode("utf-8")
            logger.info("%s : %s" % (info.name, info_string))
            # set value
            setattr(OpenGLContext, info.name, info_string)
            
        OpenGLContext.gl_major_version = callglGetIntegerv(GL_MAJOR_VERSION, GL_VERSION).value
        OpenGLContext.gl_minor_version = callglGetIntegerv(GL_MINOR_VERSION, GL_VERSION).value

        version_string = callglGetString(GL_VERSION)
        if type(version_string) == bytes:
            version_string = version_string.decode("utf-8")
        logger.info("%s : %s" % (GL_VERSION.name, version_string))

        infos = [GL_MAX_VERTEX_ATTRIBS, GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS, GL_MAX_VERTEX_UNIFORM_COMPONENTS,
                 GL_MAX_VERTEX_UNIFORM_BLOCKS, GL_MAX_GEOMETRY_UNIFORM_BLOCKS, GL_MAX_FRAGMENT_UNIFORM_BLOCKS,
                 GL_MAX_FRAGMENT_UNIFORM_COMPONENTS, GL_MAX_UNIFORM_BLOCK_SIZE, GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT,
                 GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS, GL_MAX_DRAW_BUFFERS, GL_MAX_TEXTURE_COORDS,
                 GL_MAX_TEXTURE_IMAGE_UNITS, GL_MAX_VARYING_FLOATS]
        for info in infos:
            logger.info("%s : %s" % (info.name, callglGetIntegerv(info)))
            # set value
            setattr(OpenGLContext, info.name, callglGetIntegerv(info))

        # shader storage
        infos = [GL_MAX_SHADER_STORAGE_BUFFER_BINDINGS, GL_MAX_SHADER_STORAGE_BLOCK_SIZE,
                 GL_MAX_VERTEX_SHADER_STORAGE_BLOCKS, GL_MAX_FRAGMENT_SHADER_STORAGE_BLOCKS,
                 GL_MAX_GEOMETRY_SHADER_STORAGE_BLOCKS, GL_MAX_TESS_CONTROL_SHADER_STORAGE_BLOCKS,
                 GL_MAX_TESS_EVALUATION_SHADER_STORAGE_BLOCKS, GL_MAX_COMPUTE_SHADER_STORAGE_BLOCKS,
                 GL_MAX_COMBINED_SHADER_STORAGE_BLOCKS]
        for info in infos:
            logger.info("%s : %s" % (info.name, callglGetIntegerv(info)))
            # set value
            setattr(OpenGLContext, info.name, callglGetIntegerv(info))

        # compute shader
        OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_COUNT = [callglGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_COUNT, i)[0] for i in range(3)]
        OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_SIZE = [callglGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_SIZE, i)[0] for i in range(3)]
        logger.info("%s : %s" % (GL_MAX_COMPUTE_WORK_GROUP_COUNT.name, OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_COUNT))
        logger.info("%s : %s" % (GL_MAX_COMPUTE_WORK_GROUP_SIZE.name, OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_SIZE))

        # OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS = callglGetIntegerv(GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS)
        # logger.info("%s : %s" % ( GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS.name, OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS ))

        logger.info("=" * 30)
    @staticmethod
    def check_gl_version():
        if OpenGLContext.require_gl_major_version < OpenGLContext.gl_major_version:
            return True
        elif OpenGLContext.require_gl_major_version == OpenGLContext.gl_major_version:
            return OpenGLContext.require_gl_major_version <= OpenGLContext.gl_major_version
        return False

    @staticmethod
    def get_gl_dtype(numpy_dtype):
        if np.float32 == numpy_dtype:
            return GL_FLOAT
        elif np.float64 == numpy_dtype or np.double == numpy_dtype:
            return GL_DOUBLE
        elif np.uint8 == numpy_dtype:
            return GL_UNSIGNED_BYTE
        elif np.uint16 == numpy_dtype:
            return GL_UNSIGNED_SHORT
        elif np.uint32 == numpy_dtype:
            return GL_UNSIGNED_INT
        elif np.uint64 == numpy_dtype:
            return GL_UNSIGNED_INT64
        elif np.int8 == numpy_dtype:
            return GL_BYTE
        elif np.int16 == numpy_dtype:
            return GL_SHORT
        elif np.int32 == numpy_dtype:
            return GL_INT
        elif np.int64 == numpy_dtype:
            return GL_INT64

    @staticmethod
    def get_depth_attachment(internal_format):
        if internal_format in (GL_DEPTH_STENCIL, GL_DEPTH24_STENCIL8, GL_DEPTH32F_STENCIL8):
            return GL_DEPTH_STENCIL_ATTACHMENT
        return GL_DEPTH_ATTACHMENT

    @staticmethod
    def get_last_program():
        return OpenGLContext.last_program

    @staticmethod
    def use_program(program):
        if program != OpenGLContext.last_program:
            OpenGLContext.last_program = program
            glUseProgram(program)
            return True
        return False

    @staticmethod
    def bind_vertex_array(vertex_array):
        if vertex_array != OpenGLContext.last_vertex_array:
            OpenGLContext.last_vertex_array = vertex_array
            glBindVertexArray(vertex_array)
            return True
        return False

    @staticmethod
    def present():
        OpenGLContext.use_program(0)
        OpenGLContext.last_vertex_array = -1
        glFlush()

    @staticmethod
    def _get_texture_level_dims(target, level):
        dim = _types.GLuint()
        GL_1_1.glGetTexLevelParameteriv(target, level, GL_1_1.GL_TEXTURE_WIDTH, dim)
        dims = [dim.value]
        if target != GL_1_1.GL_TEXTURE_1D:
            GL_1_1.glGetTexLevelParameteriv(target, level, GL_1_1.GL_TEXTURE_HEIGHT, dim)
            dims.append(dim.value)
            if target != GL_1_1.GL_TEXTURE_2D:
                # bug fixed : GL_1_1.GL_TEXTURE_DEPTH -> GL_1_2.GL_TEXTURE_DEPTH
                GL_1_1.glGetTexLevelParameteriv(target, level, GL_1_2.GL_TEXTURE_DEPTH, dim)
                dims.append(dim.value)
        return dims

    @staticmethod
    def glGetTexImage(target, level, format, type, array=None, outputType=bytes):
        """bug fixed overwirte version"""
        arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[images.TYPE_TO_ARRAYTYPE.get(type, type)]
        if array is None:
            dims = OpenGLContext._get_texture_level_dims(target, level)
            imageData = images.SetupPixelRead(format, tuple(dims), type)
            array = imageData
        else:
            if isinstance(array, integer_types):
                imageData = ctypes.c_void_p(array)
            else:
                array = arrayType.asArray(array)
                imageData = arrayType.voidDataPointer(array)

        GL_1_1.glGetTexImage(target, level, format, type, imageData)

        if outputType is bytes:
            return images.returnFormat(array, type)
        else:
            return array

    @staticmethod
    def IsExtensionSupported(TargetExtension):
        """ Accesses the rendering context to see if it supports an extension.
            Note, that this test only tells you if the OpenGL library supports
            the extension. The PyOpenGL system might not actually support the extension.
        """
        Extensions = glGetString(GL_EXTENSIONS)
        Extensions = Extensions.split()
        bTargetExtension = str.encode(TargetExtension)
        for extension in Extensions:
            if extension == bTargetExtension:
                break
        else:
            # not found surpport
            msg = "OpenGL rendering context does not support '%s'" % TargetExtension
            logger.error(msg)
            raise BaseException(msg)

        # Now determine if Python supports the extension
        # Exentsion names are in the form GL_<group>_<extension_name>
        # e.g.  GL_EXT_fog_coord
        # Python divides extension into modules
        # g_fVBOSupported = IsExtensionSupported ("GL_ARB_vertex_buffer_object")
        # from OpenGL.GL.EXT.fog_coord import *
        m = re.match(reCheckGLExtention, TargetExtension)
        if m:
            group_name = m.groups()[0]
            extension_name = m.groups()[1]
        else:
            msg = "GL unsupport error, %s" % TargetExtension
            logger.error(msg)
            raise BaseException(msg)

        extension_module_name = "OpenGL.GL.%s.%s" % (group_name, extension_name)

        try:
            __import__(extension_module_name)
            logger.info("PyOpenGL supports '%s'" % TargetExtension)
        except:
            msg = 'Failed to import', extension_module_name
            logger.error(msg)
            raise BaseException(msg)
        return True
