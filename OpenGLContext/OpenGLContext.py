import traceback

import numpy as np
from OpenGL.GL import *

from Common import logger


class OpenGLContext:
    last_vertex_array = -1
    GL_MAX_COMPUTE_WORK_GROUP_COUNT = None
    GL_MAX_COMPUTE_WORK_GROUP_SIZE = None
    GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS = None

    @staticmethod
    def initialize():
        try:
            logger.info("=" * 30)

            infos = [GL_VERSION, GL_RENDERER, GL_VENDOR, GL_SHADING_LANGUAGE_VERSION]
            for info in infos:
                info_string = glGetString(info)
                if type(info_string) == bytes:
                    info_string = info_string.decode("utf-8")
                logger.info("%s : %s" % (info.name, info_string))
                # set value
                setattr(OpenGLContext, info.name, info_string)

            infos = [GL_MAX_VERTEX_ATTRIBS, GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS, GL_MAX_VERTEX_UNIFORM_COMPONENTS,
                     GL_MAX_VERTEX_UNIFORM_BLOCKS, GL_MAX_GEOMETRY_UNIFORM_BLOCKS, GL_MAX_FRAGMENT_UNIFORM_BLOCKS,
                     GL_MAX_FRAGMENT_UNIFORM_COMPONENTS, GL_MAX_UNIFORM_BLOCK_SIZE, GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT,
                     GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS, GL_MAX_DRAW_BUFFERS, GL_MAX_TEXTURE_COORDS,
                     GL_MAX_TEXTURE_IMAGE_UNITS, GL_MAX_VARYING_FLOATS]
            for info in infos:
                logger.info("%s : %s" % (info.name, glGetIntegerv(info)))
                # set value
                setattr(OpenGLContext, info.name, glGetIntegerv(info))

            # shader storage
            infos = [GL_MAX_SHADER_STORAGE_BUFFER_BINDINGS, GL_MAX_SHADER_STORAGE_BLOCK_SIZE,
                     GL_MAX_VERTEX_SHADER_STORAGE_BLOCKS, GL_MAX_FRAGMENT_SHADER_STORAGE_BLOCKS,
                     GL_MAX_GEOMETRY_SHADER_STORAGE_BLOCKS, GL_MAX_TESS_CONTROL_SHADER_STORAGE_BLOCKS,
                     GL_MAX_TESS_EVALUATION_SHADER_STORAGE_BLOCKS, GL_MAX_COMPUTE_SHADER_STORAGE_BLOCKS,
                     GL_MAX_COMBINED_SHADER_STORAGE_BLOCKS]
            for info in infos:
                logger.info("%s : %s" % (info.name, glGetIntegerv(info)))
                # set value
                setattr(OpenGLContext, info.name, glGetIntegerv(info))

            # compute shader
            OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_COUNT = [glGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_COUNT, i)[0] for i in range(3)]
            OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_SIZE = [glGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_SIZE, i)[0] for i in range(3)]
            logger.info("%s : %s" % (GL_MAX_COMPUTE_WORK_GROUP_COUNT.name, OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_COUNT))
            logger.info("%s : %s" % (GL_MAX_COMPUTE_WORK_GROUP_SIZE.name, OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_SIZE))

            # OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS = glGetIntegerv(GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS)
            # logger.info(
            #     "%s : %s" % (GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS.name, OpenGLContext.GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS))

            logger.info("=" * 30)

        except BaseException:
            logger.error(traceback.format_exc())

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
    def end_render():
        OpenGLContext.last_vertex_array = -1

    @staticmethod
    def need_to_bind_vertex_array(vertex_array):
        if OpenGLContext.last_vertex_array == vertex_array:
            return False
        OpenGLContext.last_vertex_array = vertex_array
        return True

    @staticmethod
    def dispatch_compute(num_groups_x, num_groups_y, num_groups_z, barrier_mask=GL_ALL_BARRIER_BITS):
        glDispatchCompute(num_groups_x, num_groups_y, num_groups_z)
        # barrier_mask : GL_ALL_BARRIER_BITS, GL_SHADER_STORAGE_BARRIER_BIT, GL_SHADER_IMAGE_ACCESS_BARRIER_BIT...
        glMemoryBarrier(barrier_mask)

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
