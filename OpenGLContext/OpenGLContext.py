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
