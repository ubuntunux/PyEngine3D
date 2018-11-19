from OpenGL.GL import *
from OpenGL.GLU import *

from ..Common import logger
from ..Utilities import *
from ..OpenGLContext import FrameBufferManager, UniformBlock
from ..OpenGLContext import OpenGLContext
from ..Object.RenderTarget import RenderTargets
from ..Object.Mesh import ScreenQuad


class Renderer(Singleton):
    def __init__(self):
        self.core_manager = None
        self.resource_manager = None
        self.font_manager = None
        self.rendertarget_manager = None
        self.framebuffer_manager = None

        self.width = -1
        self.height = -1
        self.aspect = 0.0
        self.fov = 90.0
        self.near = 1.0
        self.far = 1000.0

        self.view_mode = GL_FILL

        self.projection = None

        self.quad = None

        self.blend_enable = False
        self.blend_equation = GL_FUNC_ADD
        self.blend_func_src = GL_SRC_ALPHA
        self.blend_func_dst = GL_ONE_MINUS_SRC_ALPHA

        self.blend_enable_prev = self.blend_enable
        self.blend_equation_prev = self.blend_equation
        self.blend_func_src_prev = self.blend_func_src
        self.blend_func_dst_prev = self.blend_func_dst

        # scene constants uniform buffer
        self.uniform_scene_buffer = None
        self.uniform_scene_data = None

        # material instances
        self.scene_constants_material = None

    def destroyScreen(self):
        self.core_manager.game_backend.quit()

    def initialize(self, core_manager):
        logger.info("Initialize Renderer")
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.font_manager = core_manager.font_manager
        self.rendertarget_manager = core_manager.rendertarget_manager

        self.framebuffer_manager = FrameBufferManager.instance()

        self.quad = ScreenQuad.get_vertex_array_buffer()

        # material instances
        self.scene_constants_material = self.resource_manager.get_material_instance('scene_constants_main')

        # scene constants uniform buffer
        program = self.scene_constants_material.get_program()

        self.uniform_scene_data = np.zeros(1, dtype=[('TIME', np.float32),
                                                     ('JITTER_FRAME', np.float32),
                                                     ('RENDER_SSR', np.int32),
                                                     ('RENDER_SSAO', np.int32),
                                                     ('BACKBUFFER_SIZE', np.float32, 2),
                                                     ('MOUSE_POS', np.float32, 2),
                                                     ('SCENECONSTANTS_DUMMY_0', np.float32, 3),
                                                     ('DELTA_TIME', np.float32)])
        self.uniform_scene_buffer = UniformBlock("scene_constants", program, 0, self.uniform_scene_data)

        # set gl hint
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    def close(self):
        pass

    def set_blend_state(self, blend_enable=True, equation=GL_FUNC_ADD, func_src=GL_SRC_ALPHA,
                        func_dst=GL_ONE_MINUS_SRC_ALPHA):
        self.blend_enable_prev = self.blend_enable
        self.blend_equation_prev = self.blend_equation
        self.blend_func_src_prev = self.blend_func_src
        self.blend_func_dst_prev = self.blend_func_dst

        self.blend_enable = blend_enable
        if blend_enable:
            self.blend_equation = equation
            self.blend_func_src = func_src
            self.blend_func_dst = func_dst
            glEnable(GL_BLEND)
            glBlendEquation(equation)
            glBlendFunc(func_src, func_dst)
        else:
            glDisable(GL_BLEND)

    def restore_blend_state_prev(self):
        self.set_blend_state(self.blend_enable_prev,
                             self.blend_equation_prev,
                             self.blend_func_src_prev,
                             self.blend_func_dst_prev)

    def resizeScene(self, width=0, height=0, clear_rendertarget=False):
        changed = False

        if 0 < width != self.width:
            self.width = width
            changed = True

        if 0 < height != self.height:
            self.height = height
            changed = True

        self.aspect = float(self.width) / float(self.height)

        self.projection = perspective(self.fov, self.aspect, self.near, self.far)

        # recreate render targets and framebuffer
        if changed or clear_rendertarget:
            self.framebuffer_manager.clear_framebuffer()
            self.rendertarget_manager.create_rendertargets()

        self.core_manager.gc_collect()

    def ortho_view(self, look_at=True):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        if look_at:
            self.look_at()

    def perspective_view(self, look_at=True):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.aspect, self.near, self.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        if look_at:
            self.look_at()

    def look_at(self):
        glScalef(1.0, 1.0, 1.0)
        gluLookAt(0.0, 0.0, 0.0, (0.0, 0.0, 1.0), (0.0, 1.0, 0.0))
        glTranslatef(0.0, 0.0, 0.0)

    def bind_uniform_blocks(self):
        pass
        # uniform_data = self.uniform_scene_data
        # uniform_data['TIME'] = self.core_manager.current_time
        # uniform_data['JITTER_FRAME'] = frame_count
        # uniform_data['RENDER_SSR'] = False
        # uniform_data['RENDER_SSAO'] = False
        # uniform_data['BACKBUFFER_SIZE'] = (RenderTargets.BACKBUFFER.width, RenderTargets.BACKBUFFER.height)
        # uniform_data['MOUSE_POS'] = self.core_manager.get_mouse_pos()
        # uniform_data['DELTA_TIME'] = self.core_manager.delta
        # self.uniform_scene_buffer.bind_uniform_block(data=uniform_data)

    def render_font(self):
        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        self.font_manager.render_font(self.width, self.height)

    def renderScene(self):
        # bind scene constants uniform blocks
        self.bind_uniform_blocks()

        self.set_blend_state(False)
        glPolygonMode(GL_FRONT_AND_BACK, self.view_mode)
        # glEnable(GL_FRAMEBUFFER_SRGB)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_TEXTURE_CUBE_MAP_SEAMLESS)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CCW)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(True)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)

        self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.render_font()

        material_instance = self.resource_manager.get_default_material_instance()
        material_instance.use_program()
        self.quad.draw_elements()

        # end of render scene
        OpenGLContext.end_render()

        # blit frame buffer
        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        self.framebuffer_manager.blit_framebuffer(self.width, self.height)
        self.framebuffer_manager.unbind_framebuffer()

        glFlush()

        # swap buffer
        self.core_manager.game_backend.flip()
