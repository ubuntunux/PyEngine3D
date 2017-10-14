from App import CoreManager
from .RenderTarget import RenderTargets


class Fog:
    def __init__(self, **sky_datas):
        self.quad = None
        self.material_instance = None
        self.rendertarget_manager = None
        self.initialize()

    def initialize(self):
        core_manager = CoreManager.instance()
        resource_manager = core_manager.resource_manager
        self.rendertarget_manager = core_manager.rendertarget_manager

        self.quad = resource_manager.getMesh("Quad")
        self.material_instance = resource_manager.getMaterialInstance("fog")

    def render(self):
        self.quad.bind_vertex_buffer()
        self.material_instance.use_program()
        texture_linear_depth = self.rendertarget_manager.get_rendertarget(RenderTargets.LINEAR_DEPTH)
        self.material_instance.bind_uniform_data('texture_linear_depth', texture_linear_depth)
        self.quad.draw_elements()
