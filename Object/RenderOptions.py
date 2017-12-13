from Common import logger
from Utilities import *


class RenderOption:
    RENDER_LIGHT_PROBE = False
    RENDER_FONT = True
    RENDER_STATIC_ACTOR = True
    RENDER_SKELETON_ACTOR = True


class RenderingType(AutoEnum):
    DEFERRED_RENDERING = ()
    FORWARD_RENDERING = ()
    LIGHT_PRE_PASS = ()
    COUNT = ()


class RenderGroup(AutoEnum):
    STATIC_ACTOR = ()
    SKELETON_ACTOR = ()
    COUNT = ()


class RenderMode(AutoEnum):
    PRE_PASS = ()
    GBUFFER = ()
    SHADING = ()
    SHADOW = ()
    COUNT = ()


class RenderOptionManager(Singleton):
    def __init__(self):
        logger.info("Create " + GetClassName(self))
        self.rendering_type = RenderingType.DEFERRED_RENDERING

        self.core_manager = None

    def initialize(self, core_manager):
        self.core_manager = core_manager

    def set_rendering_type(self, rendering_type):
        print(rendering_type)
        self.rendering_type = RenderingType.convert_index_to_enum(rendering_type)
