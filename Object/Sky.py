from App import CoreManager


class Sky:
    def __init__(self, **sky_datas):
        self.material_instance = None
        self.initialize()

    def initialize(self):
        core_manager = CoreManager.instance()
        resource_manager = core_manager.resource_manager

    def render(self):
        pass