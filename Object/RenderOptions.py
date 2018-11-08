from enum import Enum

from Common import logger
from Utilities import *


class BlendMode(Enum):
    BLEND = 0
    ADDITIVE = 1
    MULTIPLY = 2
    SUBTRACT = 3


class RenderOption:
    RENDER_LIGHT_PROBE = False
    RENDER_ONLY_ATMOSPHERE = False
    RENDER_FONT = True
    RENDER_STATIC_ACTOR = True
    RENDER_SKELETON_ACTOR = True
    RENDER_ATMOSPHERE = True
    RENDER_OCEAN = True
    RENDER_EFFECT = True


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
    GBUFFER = ()
    FORWARD_SHADING = ()
    SHADOW = ()
    SELECTED_OBJECT = ()
    COUNT = ()


class RenderOptionManager(Singleton):
    def __init__(self):
        logger.info("Create " + GetClassName(self))
        self.rendering_type = RenderingType.DEFERRED_RENDERING

        self.core_manager = None

    def initialize(self, core_manager):
        self.core_manager = core_manager

    def set_rendering_type(self, rendering_type):
        self.rendering_type = RenderingType.convert_index_to_enum(rendering_type)
