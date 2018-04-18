from math import log, exp, sqrt, tanh, sin, cos, tan, atan2, ceil, pi
import numpy as np

from OpenGL.GL import *

from Common import logger
from App import CoreManager
from OpenGLContext import CreateTexture, Texture2D, Texture2DArray, Texture3D, VertexArrayBuffer, FrameBuffer
from Utilities import *
from Object.Mesh import Plane
from Object import RenderTarget
from .Constants import *


def sqr(x):
    return x * x


def omega(k):
    return math.sqrt(9.81 * k * (1.0 + sqr(k / km)))


def frandom(seed_data):
    return (seed_data >> (31 - 24)) / float(1 << 24)


def bitReverse(i, N):
    i = int(i)
    N = int(N)
    j = i
    M = N
    Sum = 0
    W = 1
    M = int(M / 2)
    while M != 0:
        j = (i & M) > (M - 1)
        Sum += j * W
        W *= 2
        M = int(M / 2)
    return int(Sum)


def computeWeight(N, k):
    return cos(2.0 * pi * k / float(N)), sin(2.0 * pi * k / float(N))


class Ocean:
    def __init__(self, **object_data):
        self.name = object_data.get('name', 'ocean')
        self.height = object_data.get('height', 0.0)
        self.wind = object_data.get('wind', WIND)
        self.omega = object_data.get('omega', OMEGA)
        self.amplitude = object_data.get('amplitude', AMPLITUDE)

        self.simulation_wind = object_data.get('simulation_wind', 1.0)
        self.simulation_amplitude = object_data.get('simulation_amplitude', 3.0)
        self.simulation_scale = object_data.get('simulation_scale', 1.0)

        self.is_render_ocean = True
        self.attributes = Attributes()

        self.acc_time = 0.0
        self.fft_seed = Data(data=1234)

        self.renderer = CoreManager.instance().renderer
        self.scene_manager = CoreManager.instance().scene_manager
        self.resource_manager = CoreManager.instance().resource_manager

        self.fft_init = self.resource_manager.getMaterialInstance('fft_ocean.init')
        self.fft_x = self.resource_manager.getMaterialInstance('fft_ocean.fft_x')
        self.fft_y = self.resource_manager.getMaterialInstance('fft_ocean.fft_y')
        self.fft_render = self.resource_manager.getMaterialInstance('fft_ocean.render')
        self.fft_variance = self.resource_manager.getMaterialInstance('fft_ocean.fft_variance')

        self.quad = self.resource_manager.getMesh("Quad")
        self.quad_geometry = self.quad.get_geometry()

        self.grid_size = 200
        self.cell_size = np.array([1.0 / float(self.grid_size), 1.0 / float(self.grid_size)], dtype=np.float32)
        self.simulation_size = GRID_SIZES * self.simulation_scale

        self.mesh = Plane(width=self.grid_size, height=self.grid_size, xz_plane=False)
        self.geometry = self.mesh.get_geometry()

        self.texture_spectrum_1_2 = self.resource_manager.getTexture("fft_ocean.spectrum_1_2")
        self.texture_spectrum_3_4 = self.resource_manager.getTexture("fft_ocean.spectrum_3_4")
        self.texture_slope_variance = self.resource_manager.getTexture("fft_ocean.slope_variance")
        self.texture_butterfly = self.resource_manager.getTexture("fft_ocean.butterfly")

        if None in (self.texture_spectrum_1_2,
                    self.texture_spectrum_3_4,
                    self.texture_slope_variance,
                    self.texture_butterfly):
            self.generate_texture()

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
        self.attributes.setAttribute('is_render_ocean', self.is_render_ocean)
        self.attributes.setAttribute('height', self.height)
        self.attributes.setAttribute('wind', self.wind)
        self.attributes.setAttribute('omega', self.omega)
        self.attributes.setAttribute('amplitude', self.amplitude)
        self.attributes.setAttribute('simulation_wind', self.simulation_wind)
        self.attributes.setAttribute('simulation_amplitude', self.simulation_amplitude)
        self.attributes.setAttribute('simulation_scale', self.simulation_scale)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)
            # recreate resources
            if attributeName in ('amplitude', 'wind', 'omega'):
                self.generate_texture()
            elif attributeName == 'simulation_scale':
                self.simulation_size = GRID_SIZES * self.simulation_scale
        return self.attributes

    def get_save_data(self):
        save_data = dict(
            texture_type=self.__class__.__name__,
            height=self.height,
            wind=self.wind,
            omega=self.omega,
            amplitude=self.amplitude,
        )
        return save_data

    def getSlopeVariance(self, kx, ky, spectrumSample0, spectrumSample1):
        kSquare = kx * kx + ky * ky
        real = spectrumSample0
        img = spectrumSample1
        hSquare = real * real + img * img
        return kSquare * hSquare * 2.0

    def spectrum(self, kx, ky, omnispectrum=False):
        U10 = max(0.001, self.wind)
        Omega = self.omega
        Amp = self.amplitude

        k = sqrt(kx * kx + ky * ky)
        c = omega(k) / k

        # spectral peak
        kp = 9.81 * sqr(Omega / U10)
        cp = omega(kp) / kp

        # friction velocity
        z0 = 3.7e-5 * sqr(U10) / 9.81 * pow(U10 / cp, 0.9)
        u_star = 0.41 * U10 / log(10.0 / z0)

        Lpm = exp(- 5.0 / 4.0 * sqr(kp / k))
        gamma = 1.7 if Omega < 1.0 else 1.7 + 6.0 * log(Omega)
        sigma = 0.08 * (1.0 + 4.0 / pow(Omega, 3.0))
        Gamma = exp(-1.0 / (2.0 * sqr(sigma)) * sqr(sqrt(k / kp) - 1.0))
        Jp = pow(gamma, Gamma)
        Fp = Lpm * Jp * exp(- Omega / sqrt(10.0) * (sqrt(k / kp) - 1.0))
        alphap = 0.006 * sqrt(Omega)
        Bl = 0.5 * alphap * cp / c * Fp

        alpham = 0.01
        if u_star < cm:
            alpham *= (1.0 + log(u_star / cm))
        else:
            alpham *= (1.0 + 3.0 * log(u_star / cm))
        Fm = exp(-0.25 * sqr(k / km - 1.0))
        Bh = 0.5 * alpham * cm / c * Fm * Lpm

        if omnispectrum:
            return Amp * (Bl + Bh) / (k * sqr(k))

        a0 = log(2.0) / 4.0
        ap = 4.0
        am = 0.13 * u_star / cm
        Delta = tanh(a0 + ap * pow(c / cp, 2.5) + am * pow(cm / c, 2.5))
        phi = atan2(ky, kx)

        if kx < 0.0:
            return 0.0
        else:
            Bl *= 2.0
            Bh *= 2.0
        return Amp * (Bl + Bh) * (1.0 + Delta * cos(2.0 * phi)) / (2.0 * pi * sqr(sqr(k)))

    def getSpectrumSample(self, i, j, lengthScale, kMin):
        dk = 2.0 * pi / lengthScale
        kx = i * dk
        ky = j * dk
        if abs(kx) < kMin and abs(ky) < kMin:
            return 0.0, 0.0
        else:
            S = self.spectrum(kx, ky)
            h = sqrt(S / 2.0) * dk
            self.fft_seed.data = (self.fft_seed.data * 1103515245 + 12345) & 0x7FFFFFFF
            phi = frandom(self.fft_seed.data) * 2.0 * pi
            return h * cos(phi), h * sin(phi)

    def computeButterflyLookupTexture(self, butterfly_data):
        for i in range(PASSES):
            nBlocks = int(pow(2.0, float(PASSES - 1 - i)))
            nHInputs = int(pow(2.0, float(i)))
            for j in range(nBlocks):
                for k in range(nHInputs):
                    i1, i2, j1, j2 = 0, 0, 0, 0
                    if i == 0:
                        i1 = j * nHInputs * 2 + k
                        i2 = j * nHInputs * 2 + nHInputs + k
                        j1 = bitReverse(i1, FFT_SIZE)
                        j2 = bitReverse(i2, FFT_SIZE)
                    else:
                        i1 = j * nHInputs * 2 + k
                        i2 = j * nHInputs * 2 + nHInputs + k
                        j1 = i1
                        j2 = i2

                    wr, wi = computeWeight(FFT_SIZE, k * nBlocks)

                    offset1 = 4 * (i1 + i * FFT_SIZE)
                    butterfly_data[offset1 + 0] = (j1 + 0.5) / FFT_SIZE
                    butterfly_data[offset1 + 1] = (j2 + 0.5) / FFT_SIZE
                    butterfly_data[offset1 + 2] = wr
                    butterfly_data[offset1 + 3] = wi

                    offset2 = 4 * (i2 + i * FFT_SIZE)
                    butterfly_data[offset2 + 0] = (j1 + 0.5) / FFT_SIZE
                    butterfly_data[offset2 + 1] = (j2 + 0.5) / FFT_SIZE
                    butterfly_data[offset2 + 2] = -wr
                    butterfly_data[offset2 + 3] = -wi

    def generateWavesSpectrum(self, spectrum12_data, spectrum34_data):
        for y in range(FFT_SIZE):
            for x in range(FFT_SIZE):
                offset = 4 * (x + y * FFT_SIZE)
                i = (x - FFT_SIZE) if (x >= FFT_SIZE / 2) else x
                j = (y - FFT_SIZE) if (y >= FFT_SIZE / 2) else y
                s12_0, s12_1 = self.getSpectrumSample(i, j, GRID1_SIZE, pi / GRID1_SIZE)
                s12_2, s12_3 = self.getSpectrumSample(i, j, GRID2_SIZE, pi * FFT_SIZE / GRID1_SIZE)
                s34_0, s34_1 = self.getSpectrumSample(i, j, GRID3_SIZE, pi * FFT_SIZE / GRID2_SIZE)
                s34_2, s34_3 = self.getSpectrumSample(i, j, GRID4_SIZE, pi * FFT_SIZE / GRID3_SIZE)
                spectrum12_data[offset: offset+4] = s12_0, s12_1, s12_2, s12_3
                spectrum34_data[offset: offset+4] = s34_0, s34_1, s34_2, s34_3

    def computeSlopeVarianceTex(self, spectrum12_data, spectrum34_data):
        theoreticSlopeVariance = 0.0
        k = 5e-3
        while k < 1e3:
            nextK = k * 1.001
            theoreticSlopeVariance += k * k * self.spectrum(k, 0, True) * (nextK - k)
            k = nextK

        totalSlopeVariance = 0.0
        for y in range(FFT_SIZE):
            for x in range(FFT_SIZE):
                offset = 4 * (x + y * FFT_SIZE)
                i = 2.0 * pi * ((x - FFT_SIZE) if (x >= FFT_SIZE / 2) else x)
                j = 2.0 * pi * ((y - FFT_SIZE) if (y >= FFT_SIZE / 2) else y)
                s12_0, s12_1, s12_2, s12_3 = spectrum12_data[offset: offset + 4]
                s34_0, s34_1, s34_2, s34_3 = spectrum34_data[offset: offset + 4]
                totalSlopeVariance += self.getSlopeVariance(i/GRID1_SIZE, j/GRID1_SIZE, s12_0, s12_1)
                totalSlopeVariance += self.getSlopeVariance(i/GRID2_SIZE, j/GRID2_SIZE, s12_2, s12_3)
                totalSlopeVariance += self.getSlopeVariance(i/GRID3_SIZE, j/GRID3_SIZE, s34_0, s34_1)
                totalSlopeVariance += self.getSlopeVariance(i/GRID4_SIZE, j/GRID4_SIZE, s34_2, s34_3)

        self.fft_variance.use_program()
        self.fft_variance.bind_uniform_data("GRID_SIZES", GRID_SIZES)
        self.fft_variance.bind_uniform_data("slopeVarianceDelta", (theoreticSlopeVariance - totalSlopeVariance) * 0.5)
        self.fft_variance.bind_uniform_data("N_SLOPE_VARIANCE", N_SLOPE_VARIANCE)
        self.fft_variance.bind_uniform_data("spectrum_1_2_Sampler", self.texture_spectrum_1_2)
        self.fft_variance.bind_uniform_data("spectrum_3_4_Sampler", self.texture_spectrum_3_4)
        self.fft_variance.bind_uniform_data("FFT_SIZE", FFT_SIZE)
        self.quad_geometry.bind_vertex_buffer()

        for layer in range(N_SLOPE_VARIANCE):
            self.renderer.framebuffer_manager.bind_framebuffer(self.texture_slope_variance, target_layer=layer)
            self.fft_variance.bind_uniform_data("c", layer)
            self.quad_geometry.draw_elements()

    def save_texture(self, texture):
        resource = self.resource_manager.texture_loader.getResource(texture.name)
        if resource is None:
            resource = self.resource_manager.texture_loader.create_resource(texture.name, texture)
            self.resource_manager.texture_loader.save_resource(resource.name)
        else:
            old_texture = resource.get_data()
            old_texture.delete()
            resource.set_data(texture)

    def generate_texture(self):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CCW)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(True)
        glDisable(GL_BLEND)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        spectrum12_data = np.zeros(FFT_SIZE * FFT_SIZE * 4, dtype=np.float32)
        spectrum34_data = np.zeros(FFT_SIZE * FFT_SIZE * 4, dtype=np.float32)
        butterfly_data = np.zeros(FFT_SIZE * PASSES * 4, dtype=np.float32)

        self.generateWavesSpectrum(spectrum12_data, spectrum34_data)
        self.computeButterflyLookupTexture(butterfly_data)

        # create render targets
        self.texture_spectrum_1_2 = CreateTexture(
            name='fft_ocean.spectrum_1_2',
            texture_type=Texture2D,
            image_mode='RGBA',
            width=FFT_SIZE,
            height=FFT_SIZE,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            data_type=GL_FLOAT,
            wrap=GL_REPEAT,
            data=spectrum12_data,
        )

        self.texture_spectrum_3_4 = CreateTexture(
            name='fft_ocean.spectrum_3_4',
            texture_type=Texture2D,
            image_mode='RGBA',
            width=FFT_SIZE,
            height=FFT_SIZE,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            data_type=GL_FLOAT,
            wrap=GL_REPEAT,
            data=spectrum34_data,
        )

        self.texture_slope_variance = CreateTexture(
            name='fft_ocean.slope_variance',
            texture_type=Texture3D,
            image_mode='RGBA',
            width=N_SLOPE_VARIANCE,
            height=N_SLOPE_VARIANCE,
            depth=N_SLOPE_VARIANCE,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP_TO_EDGE,
            data_type=GL_FLOAT,
        )

        self.texture_butterfly = CreateTexture(
            name='fft_ocean.butterfly',
            texture_type=Texture2D,
            image_mode='RGBA',
            width=FFT_SIZE,
            height=PASSES,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP_TO_EDGE,
            data_type=GL_FLOAT,
            data=butterfly_data,
        )

        self.computeSlopeVarianceTex(spectrum12_data, spectrum34_data)

        self.save_texture(self.texture_spectrum_1_2)
        self.save_texture(self.texture_spectrum_3_4)
        self.save_texture(self.texture_slope_variance)
        self.save_texture(self.texture_butterfly)

    def update(self, delta):
        self.acc_time += delta

    def simulateFFTWaves(self):
        framebuffer_manager = CoreManager.instance().renderer.framebuffer_manager
        RenderTargets = RenderTarget.RenderTargets

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
        fft_a_framebuffer.run_bind_framebuffer()
        glClear(GL_COLOR_BUFFER_BIT)

        self.fft_init.use_program()
        self.fft_init.bind_uniform_data("FFT_SIZE", FFT_SIZE)
        self.fft_init.bind_uniform_data("INVERSE_GRID_SIZES", INVERSE_GRID_SIZES)
        self.fft_init.bind_uniform_data("spectrum_1_2_Sampler", self.texture_spectrum_1_2)
        self.fft_init.bind_uniform_data("spectrum_3_4_Sampler", self.texture_spectrum_3_4)
        self.fft_init.bind_uniform_data("t", self.acc_time * self.simulation_wind)

        self.quad_geometry.bind_vertex_buffer()
        self.quad_geometry.draw_elements()

        # # fft passes
        self.fft_x.use_program()
        self.fft_x.bind_uniform_data("butterflySampler", self.texture_butterfly)
        for i in range(PASSES):
            self.fft_x.bind_uniform_data("pass", float(i + 0.5) / PASSES)
            if i % 2 == 0:
                self.fft_x.bind_uniform_data("imgSampler", RenderTargets.FFT_A)
                fft_b_framebuffer.run_bind_framebuffer()
            else:
                self.fft_x.bind_uniform_data("imgSampler", RenderTargets.FFT_B)
                fft_a_framebuffer.run_bind_framebuffer()
            self.quad_geometry.draw_elements()

        self.fft_y.use_program()
        self.fft_y.bind_uniform_data("butterflySampler", self.texture_butterfly)
        for i in range(PASSES, PASSES * 2, 1):
            self.fft_y.bind_uniform_data("pass", float(i - PASSES + 0.5) / PASSES)
            if i % 2 == 0:
                self.fft_y.bind_uniform_data("imgSampler", RenderTargets.FFT_A)
                fft_b_framebuffer.run_bind_framebuffer()
            else:
                self.fft_y.bind_uniform_data("imgSampler", RenderTargets.FFT_B)
                fft_a_framebuffer.run_bind_framebuffer()
            self.quad_geometry.draw_elements()

        RenderTargets.FFT_A.generate_mipmap()

    def render_ocean(self, atmosphere, texture_linear_depth, texture_probe, texture_shadow):
        self.fft_render.use_program()
        self.fft_render.bind_material_instance()
        self.fft_render.bind_uniform_data("height", self.height)
        self.fft_render.bind_uniform_data("simulation_wind", self.simulation_wind)
        self.fft_render.bind_uniform_data("simulation_amplitude", self.simulation_amplitude)
        self.fft_render.bind_uniform_data("simulation_size", self.simulation_size)
        self.fft_render.bind_uniform_data("cell_size", self.cell_size)

        self.fft_render.bind_uniform_data("fftWavesSampler", RenderTarget.RenderTargets.FFT_A)
        self.fft_render.bind_uniform_data("slopeVarianceSampler", self.texture_slope_variance)
        self.fft_render.bind_uniform_data('texture_linear_depth', texture_linear_depth)
        self.fft_render.bind_uniform_data('texture_probe', texture_probe)
        self.fft_render.bind_uniform_data('texture_shadow', texture_shadow)

        # Bind Atmosphere
        atmosphere.bind_precomputed_atmosphere(material_instance=self.fft_render)

        self.geometry.bind_vertex_buffer()
        self.geometry.draw_elements()

        # instanced grid
        # self.material_instance.bind_uniform_data('grid_size', self.grid_size)
        # self.geometry.bind_instance_buffer(instance_name="offset",
        #                                    instance_data=self.offsets,
        #                                    divisor=1)
        # self.geometry.bind_vertex_buffer()
        # self.geometry.draw_elements_instanced(len(self.offsets))
