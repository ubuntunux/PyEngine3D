from math import log, exp, sqrt, tanh, sin, cos, atan2
import numpy as np

from OpenGL.GL import *

from Common import logger
from App import CoreManager
from Object import Plane
from OpenGLContext import CreateTexture, Texture2D, Texture2DArray, Texture3D, VertexArrayBuffer, FrameBuffer
from Utilities import *


M_PI = 3.14159265
octaves = 10.0
lacunarity = 2.2
gain = 0.7
norm = 0.5
clamp1 = -0.15
clamp2 = 0.2
sunTheta = M_PI / 2.0 - 0.05
gridSize = 8.0
hdrExposure = 0.4
choppy = True

N_SLOPE_VARIANCE = 10
GRID1_SIZE = 5488.0
GRID2_SIZE = 392.0
GRID3_SIZE = 28.0
GRID4_SIZE = 2.0
WIND = 5.0
OMEGA = 0.84
A = 1.0
cm = 0.23
km = 370.0
PASSES = 8  # number of passes needed for the FFT 6 -> 64, 7 -> 128, 8 -> 256, etc
FFT_SIZE = 1 << PASSES  # size of the textures storing the waves in frequency and spatial domains


def sqr(x):
    return x * x


def omega(k):
    return math.sqrt(9.81 * k * (1.0 + sqr(k / km)))


def spectrum(kx, ky, omnispectrum=False):
    U10 = WIND
    Omega = OMEGA

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
        return A * (Bl + Bh) / (k * sqr(k))

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
    return A * (Bl + Bh) * (1.0 + Delta * cos(2.0 * phi)) / (2.0 * M_PI * sqr(sqr(k)))


def frandom(seed_data):
    return (seed_data >> (31 - 24)) / float(1 << 24)


def getSlopeVariance(kx, ky, spectrumSample0, spectrumSample1):
    kSquare = kx * kx + ky * ky
    real = spectrumSample0
    img = spectrumSample1
    hSquare = real * real + img * img
    return kSquare * hSquare * 2.0


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
    return cos(2.0 * M_PI * k / float(N)), sin(2.0 * M_PI * k / float(N))


class FFTOceanTexture:
    def __init__(self, **object_data):
        self.name = self.__class__.__name__

        self.height = object_data.get('height', 0.0)
        self.is_render_ocean = True
        self.attribute = Attributes()

        self.renderer = CoreManager.instance().renderer
        self.resource_manager = CoreManager.instance().resource_manager

        self.acc_time = 0.0

        self.fft_seed = Data(data=1234)

        self.fft_init = self.resource_manager.getMaterialInstance('fft_ocean.init')
        self.fft_ocean = self.resource_manager.getMaterialInstance('fft_ocean.render')
        self.fft_variance = self.resource_manager.getMaterialInstance('fft_ocean.fft_variance')
        self.fft_x = self.resource_manager.getMaterialInstance('fft_ocean.fft_x')
        self.fft_y = self.resource_manager.getMaterialInstance('fft_ocean.fft_y')

        self.spectrum12_data = None
        self.spectrum34_data = None
        self.variance_data = None

        self.texture_spectrum_1_2 = self.resource_manager.getTexture("fft_ocean.spectrum_1_2")
        self.texture_spectrum_3_4 = self.resource_manager.getTexture("fft_ocean.spectrum_3_4")
        self.texture_slope_variance = self.resource_manager.getTexture("fft_ocean.slope_variance")
        self.texture_fft_a = self.resource_manager.getTexture("fft_ocean.fft_a")
        self.texture_fft_b = self.resource_manager.getTexture("fft_ocean.fft_b")
        self.texture_butterfly = self.resource_manager.getTexture("fft_ocean.butterfly")

        self.quad = self.resource_manager.getMesh("Quad")
        self.quad_geometry = self.quad.get_geometry()

        self.mesh = Plane(width=200, height=200)
        self.geometry = self.mesh.get_geometry()
        self.geometry.vertex_buffer.create_instance_buffer(instance_name="offset",
                                                           layout_location=5,
                                                           element_data=FLOAT2_ZERO)

    def get_save_data(self):
        save_data = dict(
            texture_type=self.__class__.__name__,
        )
        return save_data

    def getAttribute(self):
        return self.attribute

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)
        return self.attribute

    def getSpectrumSample(self, i, j, lengthScale, kMin):
        dk = 2.0 * M_PI / lengthScale
        kx = i * dk
        ky = j * dk
        if abs(kx) < kMin and abs(ky) < kMin:
            return 0.0, 0.0
        else:
            S = spectrum(kx, ky)
            h = sqrt(S / 2.0) * dk
            self.fft_seed.data = (self.fft_seed.data * 1103515245 + 12345) & 0x7FFFFFFF
            phi = frandom(self.fft_seed.data) * 2.0 * M_PI
            return h * cos(phi), h * sin(phi)

    def computeButterflyLookupTexture(self):
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
                    self.variance_data[offset1 + 0] = (j1 + 0.5) / FFT_SIZE
                    self.variance_data[offset1 + 1] = (j2 + 0.5) / FFT_SIZE
                    self.variance_data[offset1 + 2] = wr
                    self.variance_data[offset1 + 3] = wi

                    offset2 = 4 * (i2 + i * FFT_SIZE)
                    self.variance_data[offset2 + 0] = (j1 + 0.5) / FFT_SIZE
                    self.variance_data[offset2 + 1] = (j2 + 0.5) / FFT_SIZE
                    self.variance_data[offset2 + 2] = -wr
                    self.variance_data[offset2 + 3] = -wi

    def generateWavesSpectrum(self):
        for y in range(FFT_SIZE):
            for x in range(FFT_SIZE):
                offset = 4 * (x + y * FFT_SIZE)
                i = (x - FFT_SIZE) if (x >= FFT_SIZE / 2) else x
                j = (y - FFT_SIZE) if (y >= FFT_SIZE / 2) else y
                s12_0, s12_1 = self.getSpectrumSample(i, j, GRID1_SIZE, M_PI / GRID1_SIZE)
                s12_2, s12_3 = self.getSpectrumSample(i, j, GRID2_SIZE, M_PI * FFT_SIZE / GRID1_SIZE)
                s34_0, s34_1 = self.getSpectrumSample(i, j, GRID3_SIZE, M_PI * FFT_SIZE / GRID2_SIZE)
                s34_2, s34_3 = self.getSpectrumSample(i, j, GRID4_SIZE, M_PI * FFT_SIZE / GRID3_SIZE)
                self.spectrum12_data[offset: offset+4] = s12_0, s12_1, s12_2, s12_3
                self.spectrum34_data[offset: offset+4] = s34_0, s34_1, s34_2, s34_3

    def computeSlopeVarianceTex(self):
        theoreticSlopeVariance = 0.0
        k = 5e-3
        while k < 1e3:
            nextK = k * 1.001
            theoreticSlopeVariance += k * k * spectrum(k, 0, True) * (nextK - k)
            k = nextK

        totalSlopeVariance = 0.0
        for y in range(FFT_SIZE):
            for x in range(FFT_SIZE):
                offset = 4 * (x + y * FFT_SIZE)
                i = 2.0 * M_PI * ((x - FFT_SIZE) if (x >= FFT_SIZE / 2) else x)
                j = 2.0 * M_PI * ((y - FFT_SIZE) if (y >= FFT_SIZE / 2) else y)
                s12_0, s12_1, s12_2, s12_3 = self.spectrum12_data[offset: offset + 4]
                s34_0, s34_1, s34_2, s34_3 = self.spectrum34_data[offset: offset + 4]
                totalSlopeVariance += getSlopeVariance(i/GRID1_SIZE, j/GRID1_SIZE, s12_0, s12_1)
                totalSlopeVariance += getSlopeVariance(i/GRID2_SIZE, j/GRID2_SIZE, s12_2, s12_3)
                totalSlopeVariance += getSlopeVariance(i/GRID3_SIZE, j/GRID3_SIZE, s34_0, s34_1)
                totalSlopeVariance += getSlopeVariance(i/GRID4_SIZE, j/GRID4_SIZE, s34_2, s34_3)

        self.fft_variance.use_program()
        self.fft_variance.bind_uniform_data("GRID_SIZES", np.array([GRID1_SIZE, GRID2_SIZE, GRID3_SIZE, GRID4_SIZE],
                                                                   dtype=np.float32))
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

    def simulateFFTWaves(self):
        # initialize
        INVERSE_GRID_SIZES = np.array([2.0 * M_PI * FFT_SIZE / GRID1_SIZE,
                                       2.0 * M_PI * FFT_SIZE / GRID2_SIZE,
                                       2.0 * M_PI * FFT_SIZE / GRID3_SIZE,
                                       2.0 * M_PI * FFT_SIZE / GRID4_SIZE], dtype=np.float32)

        self.fft_init.use_program()
        self.fft_init.bind_uniform_data("FFT_SIZE", FFT_SIZE)
        self.fft_init.bind_uniform_data("INVERSE_GRID_SIZES", INVERSE_GRID_SIZES)
        self.fft_init.bind_uniform_data("spectrum_1_2_Sampler", self.texture_spectrum_1_2)
        self.fft_init.bind_uniform_data("spectrum_3_4_Sampler", self.texture_spectrum_3_4)
        self.fft_init.bind_uniform_data("t", self.acc_time)

        self.quad_geometry.bind_vertex_buffer()
        self.renderer.framebuffer_manager.bind_framebuffer(self.texture_fft_a,
                                                           self.texture_fft_a,
                                                           self.texture_fft_a,
                                                           self.texture_fft_a,
                                                           self.texture_fft_a)
        self.quad_geometry.draw_elements()

        # # fft passes
        self.fft_x.use_program()
        # self.fft_x.bind_uniform_data("nLayers", 5 if choppy else 3)
        self.fft_x.bind_uniform_data("butterflySampler", self.texture_butterfly)
        for i in range(PASSES):
            self.fft_x.bind_uniform_data("pass", float(i + 0.5) / PASSES)
            if i % 2 == 0:
                self.renderer.framebuffer_manager.bind_framebuffer(self.texture_fft_b,
                                                                   self.texture_fft_b,
                                                                   self.texture_fft_b,
                                                                   self.texture_fft_b,
                                                                   self.texture_fft_b)
                self.fft_x.bind_uniform_data("imgSampler", self.texture_fft_a)
            else:
                self.renderer.framebuffer_manager.bind_framebuffer(self.texture_fft_a,
                                                                   self.texture_fft_a,
                                                                   self.texture_fft_a,
                                                                   self.texture_fft_a,
                                                                   self.texture_fft_a)
                self.fft_x.bind_uniform_data("imgSampler", self.texture_fft_b)
            self.quad_geometry.draw_elements()

        self.fft_y.use_program()
        # self.fft_y.bind_uniform_data("nLayers", 5 if choppy else 3)
        self.fft_y.bind_uniform_data("butterflySampler", self.texture_butterfly)
        for i in range(PASSES):
            self.fft_y.bind_uniform_data("pass", float(i - PASSES + 0.5) / PASSES)
            if i % 2 == 0:
                self.renderer.framebuffer_manager.bind_framebuffer(self.texture_fft_b,
                                                                   self.texture_fft_b,
                                                                   self.texture_fft_b,
                                                                   self.texture_fft_b,
                                                                   self.texture_fft_b)
                self.fft_x.bind_uniform_data("imgSampler", self.texture_fft_a)
            else:
                self.renderer.framebuffer_manager.bind_framebuffer(self.texture_fft_a,
                                                                   self.texture_fft_a,
                                                                   self.texture_fft_a,
                                                                   self.texture_fft_a,
                                                                   self.texture_fft_a)
                self.fft_x.bind_uniform_data("imgSampler", self.texture_fft_b)
            self.quad_geometry.draw_elements()

        self.texture_fft_a.generate_mipmap()

    def update(self, delta):
        self.acc_time += delta
        # self.simulateFFTWaves()

        # glUseProgram(render->program)
        # glUniformMatrix4fv(
        #     glGetUniformLocation(render->program, "screenToCamera"), 1, true, proj.inverse().coefficients())
        # glUniformMatrix4fv(
        #     glGetUniformLocation(render->program, "cameraToWorld"), 1, true, view.inverse().coefficients())
        # glUniformMatrix4fv(glGetUniformLocation(render->program, "worldToScreen"), 1, true, (
        #         proj * view).coefficients())
        # glUniform3f(glGetUniformLocation(render->program, "worldCamera"), 0.0, 0.0, ch)
        # glUniform3f(glGetUniformLocation(render->program, "worldSunDir"), sun.x, sun.y, sun.z)
        # glUniform1f(glGetUniformLocation(render->program, "hdrExposure"), hdrExposure)
        # glUniform3f(glGetUniformLocation(render->program, "seaColor"), seaColor[0] * seaColor[3], seaColor[1] *
        #                                                                seaColor[3], seaColor[2] * seaColor[3])
        # glUniform1i(glGetUniformLocation(render->program, "spectrum_1_2_Sampler"), SPECTRUM_1_2_UNIT)
        # glUniform1i(glGetUniformLocation(render->program, "spectrum_3_4_Sampler"), SPECTRUM_3_4_UNIT)
        # glUniform1i(glGetUniformLocation(render->program, "fftWavesSampler"), FFT_A_UNIT)
        # glUniform1i(glGetUniformLocation(render->program, "slopeVarianceSampler"), SLOPE_VARIANCE_UNIT)
        # glUniform4f(glGetUniformLocation(render->program, "GRID_SIZES"), GRID1_SIZE, GRID2_SIZE, GRID3_SIZE, GRID4_SIZE)
        # glUniform2f(glGetUniformLocation(render->program, "gridSize"), gridSize / float(width), gridSize / float(height))
        # glUniform1f(glGetUniformLocation(render->program, "choppy"), choppy)

    def set_resource_data(self, texture):
        resource = self.resource_manager.textureLoader.getResource(texture.name)
        if resource is None:
            resource = self.resource_manager.textureLoader.create_resource(texture.name, texture)
            self.resource_manager.textureLoader.save_resource(resource.name)
        else:
            old_texture = resource.get_data()
            old_texture.delete()
            resource.set_data(texture)

    def render(self):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CCW)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(True)
        glDisable(GL_BLEND)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        self.spectrum12_data = np.zeros(FFT_SIZE * FFT_SIZE * 4, dtype=np.float32)
        self.spectrum34_data = np.zeros(FFT_SIZE * FFT_SIZE * 4, dtype=np.float32)
        self.variance_data = np.zeros(FFT_SIZE * PASSES * 4, dtype=np.float32)

        self.generateWavesSpectrum()
        self.computeButterflyLookupTexture()

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
            data=self.spectrum12_data,
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
            data=self.spectrum34_data,
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

        self.texture_fft_a = CreateTexture(
            name='fft_ocean.fft_a',
            texture_type=Texture2DArray,
            image_mode='RGBA',
            width=FFT_SIZE,
            height=FFT_SIZE,
            depth=5,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR_MIPMAP_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_REPEAT,
            data_type=GL_FLOAT,
        )

        self.texture_fft_b = CreateTexture(
            name='fft_ocean.fft_b',
            texture_type=Texture2DArray,
            image_mode='RGBA',
            width=FFT_SIZE,
            height=FFT_SIZE,
            depth=5,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR_MIPMAP_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_REPEAT,
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
            data=self.variance_data,
        )

        self.computeSlopeVarianceTex()

        self.set_resource_data(self.texture_spectrum_1_2)
        self.set_resource_data(self.texture_spectrum_3_4)
        self.set_resource_data(self.texture_slope_variance)
        self.set_resource_data(self.texture_fft_a)
        self.set_resource_data(self.texture_fft_b)
        self.set_resource_data(self.texture_butterfly)

