import traceback

import numpy as np
from OpenGL.GL import *

from Common import logger
from Utilities import Singleton


class OpenGLContext(Singleton):
    def __init__(self):
        self.GL_MAX_COMPUTE_WORK_GROUP_COUNT = None
        self.GL_MAX_COMPUTE_WORK_GROUP_SIZE = None
        self.GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS = None

    def initialize(self):
        try:
            logger.info("=" * 30)

            infos = [GL_VERSION, GL_RENDERER, GL_VENDOR, GL_SHADING_LANGUAGE_VERSION]
            for info in infos:
                info_string = glGetString(info)
                if type(info_string) == bytes:
                    info_string = info_string.decode("utf-8")
                logger.info("%s : %s" % (info.name, info_string))
                # set value
                setattr(self, info.name, info_string)

            infos = [GL_MAX_VERTEX_ATTRIBS, GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS, GL_MAX_VERTEX_UNIFORM_COMPONENTS,
                     GL_MAX_VERTEX_UNIFORM_BLOCKS, GL_MAX_GEOMETRY_UNIFORM_BLOCKS, GL_MAX_FRAGMENT_UNIFORM_BLOCKS,
                     GL_MAX_FRAGMENT_UNIFORM_COMPONENTS, GL_MAX_UNIFORM_BLOCK_SIZE, GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT,
                     GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS, GL_MAX_DRAW_BUFFERS, GL_MAX_TEXTURE_COORDS,
                     GL_MAX_TEXTURE_IMAGE_UNITS, GL_MAX_VARYING_FLOATS]
            for info in infos:
                logger.info("%s : %s" % (info.name, glGetIntegerv(info)))
                # set value
                setattr(self, info.name, glGetIntegerv(info))

            # compute shader
            self.GL_MAX_COMPUTE_WORK_GROUP_COUNT = [glGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_COUNT, i)[0] for i in range(3)]
            self.GL_MAX_COMPUTE_WORK_GROUP_SIZE = [glGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_SIZE, i)[0] for i in range(3)]
            logger.info("%s : %s" % (GL_MAX_COMPUTE_WORK_GROUP_COUNT.name, self.GL_MAX_COMPUTE_WORK_GROUP_COUNT))
            logger.info("%s : %s" % (GL_MAX_COMPUTE_WORK_GROUP_SIZE.name, self.GL_MAX_COMPUTE_WORK_GROUP_SIZE))

            # self.GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS = glGetIntegerv(GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS)
            # logger.info(
            #     "%s : %s" % (GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS.name, self.GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS))

            logger.info("=" * 30)

        except BaseException:
            logger.error(traceback.format_exc())
