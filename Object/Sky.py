from App import CoreManager


class Sky:
    def __init__(self, **sky_datas):
        self.quad = None
        self.material_instance = None
        self.initialize()

    def initialize(self):
        core_manager = CoreManager.instance()
        resource_manager = core_manager.resource_manager

        self.quad = resource_manager.getMesh("Quad")
        self.material_instance = resource_manager.getMaterialInstance("sky")

    def render(self):
        self.quad.bind_vertex_buffer()
        self.material_instance.use_program()
        self.material_instance.bind_material_instance()
        self.quad.draw_elements()