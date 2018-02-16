from Common import logger
from App import CoreManager

from Object import Plane
from Utilities import *


class Ocean:
    name = 'Ocean'

    def __init__(self):
        logger.info("Create %s : %s" % (GetClassName(self), self.name))
        resource_manager = CoreManager.instance().resource_manager
        self.is_render_ocean = True
        self.height = 0.0
        self.mesh = Plane(width=10, height=10)
        self.geometry = self.mesh.get_geometry()
        self.material_instance = resource_manager.getMaterialInstance('ocean')

    def update(self, delta):
        pass

    def render_ocean(self):
        self.material_instance.use_program()
        self.material_instance.bind_uniform_data('height', self.height)
        self.geometry.bind_vertex_buffer()
        self.geometry.draw_elements()
