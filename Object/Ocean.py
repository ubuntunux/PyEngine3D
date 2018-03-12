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


def lrandom(seed):
    return (seed * 1103515245 + 12345) & 0x7FFFFFFF


def frandom(seed):
    r = lrandom(seed) >> (31 - 24)
    return r / float(1 << 24)


def getSpectrumSample(i, j, lengthScale, kMin):
    seed = 1234
    dk = 2.0 * M_PI / lengthScale
    kx = i * dk
    ky = j * dk
    if abs(kx) < kMin and abs(ky) < kMin:
        return 0.0, 0.0
    else:
        S = spectrum(kx, ky)
        h = sqrt(S / 2.0) * dk
        phi = frandom(seed) * 2.0 * M_PI
        return h * cos(phi), h * sin(phi)


def getSlopeVariance(kx, ky, spectrumSample):
    kSquare = kx * kx + ky * ky
    real = spectrumSample[0]
    img = spectrumSample[1]
    hSquare = real * real + img * img
    return kSquare * hSquare * 2.0


def bitReverse(i, N):
    j = i
    M = N
    Sum = 0
    W = 1
    M = M / 2
    while M != 0:
        j = (i & M) > (M - 1)
        Sum += j * W
        W *= 2
        M = M / 2
    return Sum


def computeWeight(N, k):
    return cosl(2.0 * M_PI * k / float(N)), sinl(2.0 * M_PI * k / float(N))


class FFTOcean:
    def __init__(self, **object_data):
        self.name = object_data.get('name', 'fft_ocean')
        self.height = object_data.get('height', 0.0)
        self.is_render_ocean = True
        self.attributes = Attributes()

        resource_manager = CoreManager.instance().resource_manager
        self.framebuffer_manager = CoreManager.instance().renderer.framebuffer_manager

        self.fft_init = resource_manager.getMaterialInstance('fft_init')
        self.fft_ocean = resource_manager.getMaterialInstance('fft_ocean')
        self.fft_variance = resource_manager.getMaterialInstance('fft_variance')
        self.fft_x = resource_manager.getMaterialInstance('fft_x')
        self.fft_y = resource_manager.getMaterialInstance('fft_y')

        self.quad = resource_manager.getMesh("Quad")
        self.quad_geometry = self.quad.get_geometry()

        self.mesh = Plane(width=200, height=200)
        self.geometry = self.mesh.get_geometry()
        self.geometry.vertex_buffer.create_instance_buffer(instance_name="offset",
                                                           layout_location=5,
                                                           element_data=FLOAT2_ZERO)

        # create render targets
        print(1)
        data_spectrum12, data_spectrum34 = self.generateWavesSpectrum()
        print(2)
        self.texture_spectrum_1_2 = CreateTexture(
            name='spectrum_1_2',
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
            data=data_spectrum12,
        )

        self.texture_spectrum_3_4 = CreateTexture(
            name='spectrum_3_4',
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
            data=data_spectrum34,
        )

        self.texture_slope_variance = CreateTexture(
            name='slope_variance',
            texture_type=Texture3D,
            image_mode='RGBA',
            width=N_SLOPE_VARIANCE,
            height=N_SLOPE_VARIANCE,
            depth=N_SLOPE_VARIANCE,
            internal_format=GL_LUMINANCE16,
            texture_format=GL_LUMINANCE,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP_TO_EDGE,
            data_type=GL_FLOAT,
        )

        self.texture_fft_a = CreateTexture(
            name='fft_a',
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
            name='fft_b',
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

        data = self.computeButterflyLookupTexture()
        print(3)
        self.texture_butterfly = CreateTexture(
            name='butterfly',
            texture_type=Texture2D,
            image_mode='RGBA',
            width=FFT_SIZE,
            height=FFT_SIZE,
            depth=PASSES,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP_TO_EDGE,
            data_type=GL_FLOAT,
            data=data,
        )

        self.computeSlopeVarianceTex()
        print(4)

    def computeButterflyLookupTexture(self):
        data = np.array(FFT_SIZE * PASSES * 4, dtype=np.float32)

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
                    data[offset1 + 0] = (j1 + 0.5) / FFT_SIZE
                    data[offset1 + 1] = (j2 + 0.5) / FFT_SIZE
                    data[offset1 + 2] = wr
                    data[offset1 + 3] = wi

                    offset2 = 4 * (i2 + i * FFT_SIZE)
                    data[offset2 + 0] = (j1 + 0.5) / FFT_SIZE
                    data[offset2 + 1] = (j2 + 0.5) / FFT_SIZE
                    data[offset2 + 2] = -wr
                    data[offset2 + 3] = -wi
        return data

    def generateWavesSpectrum(self):
        spectrum12 = np.zeros(FFT_SIZE * FFT_SIZE * 4, dtype=np.float32)
        spectrum34 = np.zeros(FFT_SIZE * FFT_SIZE * 4, dtype=np.float32)

        for y in range(FFT_SIZE):
            print(y)
            for x in range(FFT_SIZE):
                offset = 4 * (x + y * FFT_SIZE)
                i = (x - FFT_SIZE) if (x >= FFT_SIZE / 2) else x
                j = (y - FFT_SIZE) if (y >= FFT_SIZE / 2) else y
                spectrum12[offset: offset+2] = getSpectrumSample(i, j, GRID1_SIZE, M_PI / GRID1_SIZE)
                spectrum12[offset+2: offset + 4] = getSpectrumSample(i, j, GRID2_SIZE, M_PI * FFT_SIZE / GRID1_SIZE)
                spectrum34[offset: offset + 2] = getSpectrumSample(i, j, GRID3_SIZE, M_PI * FFT_SIZE / GRID2_SIZE)
                spectrum34[offset + 2: offset + 4] = getSpectrumSample(i, j, GRID4_SIZE, M_PI * FFT_SIZE / GRID3_SIZE)
        return spectrum12, spectrum34

    def computeSlopeVarianceTex(self):
        theoreticSlopeVariance = 0.0
        k = 5e-3
        while k < 1e3:
            nextK = k * 1.001
            theoreticSlopeVariance += k * k * spectrum(k, 0, true) * (nextK - k)
            k = nextK

        totalSlopeVariance = 0.0
        for y in range(FFT_SIZE):
            for x in range(FFT_SIZE):
                offset = 4 * (x + y * FFT_SIZE)
                i = 2.0 * M_PI * ((x - FFT_SIZE) if (x >= FFT_SIZE / 2) else x)
                j = 2.0 * M_PI * ((y - FFT_SIZE) if (y >= FFT_SIZE / 2) else y)
                totalSlopeVariance += getSlopeVariance(i / GRID1_SIZE, j / GRID1_SIZE, spectrum12 + offset)
                totalSlopeVariance += getSlopeVariance(i / GRID2_SIZE, j / GRID2_SIZE, spectrum12 + offset + 2)
                totalSlopeVariance += getSlopeVariance(i / GRID3_SIZE, j / GRID3_SIZE, spectrum34 + offset)
                totalSlopeVariance += getSlopeVariance(i / GRID4_SIZE, j / GRID4_SIZE, spectrum34 + offset + 2)

        self.fft_variance.use_program()
        self.fft_variance.bind_uniform("GRID_SIZES", [GRID1_SIZE, GRID2_SIZE, GRID3_SIZE, GRID4_SIZE])
        self.fft_variance.bind_uniform("slopeVarianceDelta", (theoreticSlopeVariance - totalSlopeVariance) * 0.5)
        self.quad_geometry.bind_vertex_buffer()

        for layer in range(N_SLOPE_VARIANCE):
            self.framebuffer_manager.bind_framebuffer(self.texture_slope_variance, target_layer=layer)
            self.fft_variance.bind_uniform("c", layer)
            self.quad_geometry.draw_elements()

    def simulateFFTWaves(self, t):
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fftFbo1)
        glViewport(0, 0, FFT_SIZE, FFT_SIZE)
        # glUseProgram(init->program)
        # glUniform1f(glGetUniformLocation(init->program, "FFT_SIZE"), FFT_SIZE)
        # glUniform4f(glGetUniformLocation(init->program, "INVERSE_GRID_SIZES"),
        # 2.0 * M_PI * FFT_SIZE / GRID1_SIZE,
        # 2.0 * M_PI * FFT_SIZE / GRID2_SIZE,
        # 2.0 * M_PI * FFT_SIZE / GRID3_SIZE,
        # 2.0 * M_PI * FFT_SIZE / GRID4_SIZE)
        # glUniform1f(glGetUniformLocation(init->program, "t"), t)
        # drawQuad()
        #
        # # fft passes
        # glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fftFbo2)
        # glUseProgram(fftx->program)
        # glUniform1i(glGetUniformLocation(fftx->program, "nLayers"), choppy ? 5: 3)
        # for i in range(PASSES):
        #     glUniform1f(glGetUniformLocation(fftx->program, "pass"), float(i + 0.5) / PASSES)
        #     if i % 2 == 0:
        #         glUniform1i(glGetUniformLocation(fftx->program, "imgSampler"), FFT_A_UNIT)
        #         glDrawBuffer(GL_COLOR_ATTACHMENT1_EXT)
        #     else:
        #         glUniform1i(glGetUniformLocation(fftx->program, "imgSampler"), FFT_B_UNIT)
        #         glDrawBuffer(GL_COLOR_ATTACHMENT0_EXT)
        #     drawQuad()
        #
        # glUseProgram(ffty->program)
        # glUniform1i(glGetUniformLocation(ffty->program, "nLayers"), choppy ? 5: 3)
        # for i in range(PASSES, 2 * PASSES):
        #     glUniform1f(glGetUniformLocation(ffty->program, "pass"), float(i - PASSES + 0.5) / PASSES)
        #     if i % 2 == 0:
        #         glUniform1i(glGetUniformLocation(ffty->program, "imgSampler"), FFT_A_UNIT)
        #         glDrawBuffer(GL_COLOR_ATTACHMENT1_EXT)
        #     else:
        #         glUniform1i(glGetUniformLocation(ffty->program, "imgSampler"), FFT_B_UNIT)
        #         glDrawBuffer(GL_COLOR_ATTACHMENT0_EXT)
        #     drawQuad()
        #
        # glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
        # glActiveTexture(GL_TEXTURE0 + FFT_A_UNIT)
        # glGenerateMipmapEXT(GL_TEXTURE_2D_ARRAY_EXT)

    def update(self, delta):
        self.t += delta
        simulateFFTWaves(self.t)

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
        # glUniform2f(glGetUniformLocation(render->program, "gridSize"), gridSize / float(width), gridSize / float(
        #     height))
        # glUniform1f(glGetUniformLocation(render->program, "choppy"), choppy)


class Ocean:
    def __init__(self, **object_data):
        # self.fft_ocean = FFTOcean()

        self.name = object_data.get('name', 'ocean')
        self.height = object_data.get('height', 0.0)
        self.is_render_ocean = True
        self.attributes = Attributes()

        resource_manager = CoreManager.instance().resource_manager
        self.material_instance = resource_manager.getMaterialInstance('ocean')

        self.mesh = Plane(width=200, height=200)
        self.geometry = self.mesh.get_geometry()
        self.geometry.vertex_buffer.create_instance_buffer(instance_name="offset",
                                                           layout_location=5,
                                                           element_data=FLOAT2_ZERO)
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
        pass

    def render_ocean(self, atmoshpere, texture_depth, texture_probe, texture_shadow, texture_scene_reflect):
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
