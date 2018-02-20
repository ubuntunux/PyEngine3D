import numpy as np

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

        self.material_instance = resource_manager.getMaterialInstance('ocean')

        self.mesh = Plane(width=100, height=100)
        self.geometry = self.mesh.get_geometry()
        self.geometry.vertex_buffer.create_instance_buffer(instance_name="offset",
                                                           layout_location=5,
                                                           element_data=FLOAT2_ZERO)
        self.grid_size = Float2(100.0, 100.0)
        self.grid_count = 10
        self.offsets = np.array(
            [Float2(i % self.grid_count, i // self.grid_count) for i in range(self.grid_count * self.grid_count)],
            dtype=np.float32)

    def update(self, delta):
        pass

    def render_ocean(self):
        self.material_instance.use_program()
        self.material_instance.bind_material_instance()
        self.material_instance.bind_uniform_data('grid_size', self.grid_size)
        self.geometry.bind_instance_buffer(instance_name="offset",
                                           instance_data=self.offsets,
                                           divisor=1)
        self.geometry.bind_vertex_buffer()
        self.geometry.draw_elements_instanced(len(self.offsets))
