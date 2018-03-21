import numpy as np

from OpenGL.GL import *

from Common import logger
from App import CoreManager
from OpenGLContext import CreateTexture, Texture2D, Texture2DArray, Texture3D, VertexArrayBuffer, FrameBuffer
from Utilities import *
from .Mesh import Plane
from .RenderTarget import RenderTargets
from .ProceduralTexture.FFTOceanConstants import *


class Ocean:
    def __init__(self, **object_data):
        self.name = object_data.get('name', 'ocean')
        self.height = object_data.get('height', 0.0)
        self.is_render_ocean = True
        self.attributes = Attributes()

        self.acc_time = 0.0

        resource_manager = CoreManager.instance().resource_manager

        self.fft_ocean = resource_manager.proceduralTextureLoader.getResourceData("FFTOceanTexture")

        self.fft_init = resource_manager.getMaterialInstance('fft_ocean.init')
        self.fft_x = resource_manager.getMaterialInstance('fft_ocean.fft_x')
        self.fft_y = resource_manager.getMaterialInstance('fft_ocean.fft_y')
        self.fft_render = resource_manager.getMaterialInstance('fft_ocean.render')

        self.quad = resource_manager.getMesh("Quad")
        self.quad_geometry = self.quad.get_geometry()

        self.grid_size = 200
        self.cell_size = np.array([1.0 / float(self.grid_size), 1.0 / float(self.grid_size)], dtype=np.float32)

        self.mesh = Plane(width=self.grid_size, height=self.grid_size, xz_plane=False)
        self.geometry = self.mesh.get_geometry()

        # self.geometry.vertex_buffer.create_instance_buffer(instance_name="offset",
        #                                                    layout_location=5,
        #                                                    element_data=FLOAT2_ZERO)

        # instanced grid
        # self.grid_size = Float2(100.0, 100.0)
        # self.grid_count = 1
        # self.offsets = np.array(
        #     [Float2(i % self.grid_count, i // self.grid_count) for i in range(self.grid_count * self.grid_count)],
        #     dtype=np.float32)

    def getAttribute(self):
        self.attributes.setAttribute('height', self.height)
        self.attributes.setAttribute('is_render_ocean', self.is_render_ocean)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)

    def get_save_data(self):
        save_data = dict()
        save_data['height'] = self.height
        return save_data

    def update(self, delta):
        self.simulateFFTWaves(delta)

    def simulateFFTWaves(self, delta):
        self.acc_time += delta

        framebuffer_manager = CoreManager.instance().renderer.framebuffer_manager

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

        fft_a_framebuffer = framebuffer_manager.get_framebuffer(RenderTargets.FFT_A,
                                                                RenderTargets.FFT_A,
                                                                RenderTargets.FFT_A,
                                                                RenderTargets.FFT_A,
                                                                RenderTargets.FFT_A)

        fft_b_framebuffer = framebuffer_manager.get_framebuffer(RenderTargets.FFT_B,
                                                                RenderTargets.FFT_B,
                                                                RenderTargets.FFT_B,
                                                                RenderTargets.FFT_B,
                                                                RenderTargets.FFT_B)

        # initialize
        self.fft_init.use_program()
        self.fft_init.bind_uniform_data("FFT_SIZE", FFT_SIZE)
        self.fft_init.bind_uniform_data("INVERSE_GRID_SIZES", INVERSE_GRID_SIZES)
        self.fft_init.bind_uniform_data("spectrum_1_2_Sampler", self.fft_ocean.texture_spectrum_1_2)
        self.fft_init.bind_uniform_data("spectrum_3_4_Sampler", self.fft_ocean.texture_spectrum_3_4)
        self.fft_init.bind_uniform_data("t", self.acc_time)

        self.quad_geometry.bind_vertex_buffer()
        fft_a_framebuffer.bind_framebuffer()
        glClear(GL_COLOR_BUFFER_BIT)
        self.quad_geometry.draw_elements()

        # # fft passes
        self.fft_x.use_program()
        self.fft_x.bind_uniform_data("butterflySampler", self.fft_ocean.texture_butterfly)
        for i in range(PASSES):
            self.fft_x.bind_uniform_data("pass", float(i + 0.5) / PASSES)
            if i % 2 == 0:
                self.fft_x.bind_uniform_data("imgSampler", RenderTargets.FFT_A)
                fft_b_framebuffer.bind_framebuffer()
            else:
                self.fft_x.bind_uniform_data("imgSampler", RenderTargets.FFT_B)
                fft_a_framebuffer.bind_framebuffer()
            self.quad_geometry.draw_elements()

        self.fft_y.use_program()
        self.fft_y.bind_uniform_data("butterflySampler", self.fft_ocean.texture_butterfly)
        for i in range(PASSES, PASSES * 2, 1):
            self.fft_y.bind_uniform_data("pass", float(i - PASSES + 0.5) / PASSES)
            if i % 2 == 0:
                self.fft_y.bind_uniform_data("imgSampler", RenderTargets.FFT_A)
                fft_b_framebuffer.bind_framebuffer()
            else:
                self.fft_y.bind_uniform_data("imgSampler", RenderTargets.FFT_B)
                fft_a_framebuffer.bind_framebuffer()
            self.quad_geometry.draw_elements()

        RenderTargets.FFT_A.generate_mipmap()

    def render_ocean(self, atmoshpere, texture_depth, texture_probe, texture_shadow, texture_scene_reflect):
        self.fft_render.use_program()
        self.fft_render.bind_material_instance()
        self.fft_render.bind_uniform_data("height", self.height)
        self.fft_render.bind_uniform_data("cellSize", self.cell_size)
        self.fft_render.bind_uniform_data("GRID_SIZES", GRID_SIZES)

        self.fft_render.bind_uniform_data("fftWavesSampler", RenderTargets.FFT_A)
        self.fft_render.bind_uniform_data("slopeVarianceSampler", self.fft_ocean.texture_slope_variance)
        self.geometry.bind_vertex_buffer()
        self.geometry.draw_elements()
        return

        self.material_instance.use_program()
        self.material_instance.bind_material_instance()
        self.material_instance.bind_uniform_data('height', self.height)

        self.material_instance.bind_uniform_data('texture_depth', texture_depth)
        self.material_instance.bind_uniform_data('texture_probe', texture_probe)
        self.material_instance.bind_uniform_data('texture_shadow', texture_shadow)
        self.material_instance.bind_uniform_data('texture_scene_reflect', texture_scene_reflect)

        # Bind Atmosphere
        atmoshpere.bind_precomputed_atmosphere(self.material_instance)

        self.geometry.bind_vertex_buffer()
        self.geometry.draw_elements()

        # instanced grid
        # self.material_instance.bind_uniform_data('grid_size', self.grid_size)
        # self.geometry.bind_instance_buffer(instance_name="offset",
        #                                    instance_data=self.offsets,
        #                                    divisor=1)
        # self.geometry.bind_vertex_buffer()
        # self.geometry.draw_elements_instanced(len(self.offsets))
