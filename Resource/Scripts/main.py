from PyEngine3D.Common import logger
from PyEngine3D.Utilities import Singleton, Float3, Float4
from PyEngine3D.App.GameBackend import Keyboard


class ScriptManager(Singleton):
    def __init__(self):
        logger.info("ScriptManager::__init__")
        self.core_manager = None
        self.renderer = None
        self.debug_line_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.scene_manager = None
        self.viewport_manager = None
        self.main_viewport = None
        self.sphere = None
        self.suzan = None
        self.skeletal = None

    def initialize(self, core_manager):
        logger.info("ScriptManager::initialize")

        self.core_manager = core_manager
        self.renderer = core_manager.renderer
        self.debug_line_manager = core_manager.debug_line_manager
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.scene_manager
        self.viewport_manager = core_manager.viewport_manager
        self.main_viewport = core_manager.viewport_manager.main_viewport

        self.scene_manager.clear_actors()

        camera_transform = self.scene_manager.main_camera.transform
        camera_transform.set_pos([4.5, 4.5, 6.8])
        camera_transform.set_pitch(5.92)
        camera_transform.set_yaw(0.67)

        self.sphere = self.resource_manager.get_model("sphere")
        self.scene_manager.add_object(model=self.sphere, pos=[2.0, 1.0, 0.5])

        self.suzan = self.resource_manager.get_model("suzan")
        self.scene_manager.add_object(model=self.suzan, pos=[-1.0, 0.5, 2.0])

        if not self.core_manager.is_basic_mode:
            self.skeletal = self.resource_manager.get_model("skeletal")
            self.scene_manager.add_object(model=self.skeletal, pos=[2.0, 1.0, 3.0], scale=[0.01, 0.01, 0.01])

    def exit(self):
        logger.info("ScriptManager::exit")
        if self.sphere is not None:
            self.scene_manager.delete_object(self.sphere.name)
            self.sphere = None

        if self.suzan is not None:
            self.scene_manager.delete_object(self.suzan.name)
            self.suzan = None

        if self.skeletal is not None:
            self.scene_manager.delete_object(self.skeletal.name)
            self.skeletal = None

    def update_camera(self, delta):
        keydown = self.game_backend.get_keyboard_pressed()
        mouse_delta = self.game_backend.mouse_delta
        btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()

        # get camera
        camera = self.scene_manager.main_camera
        camera_transform = camera.transform
        move_speed = camera.move_speed * delta
        pan_speed = camera.pan_speed * delta

        if keydown[Keyboard.LSHIFT]:
            move_speed *= 4.0
            pan_speed *= 4.0

        # camera move pan
        if btn_left and btn_right or btn_middle:
            camera_transform.move_left(-mouse_delta[0] * pan_speed)
            camera_transform.move_up(-mouse_delta[1] * pan_speed)

        # camera rotation
        elif btn_left or btn_right:
            camera_transform.rotation_pitch(mouse_delta[1] * camera.rotation_speed)
            camera_transform.rotation_yaw(-mouse_delta[0] * camera.rotation_speed)

        if keydown[Keyboard.Z]:
            camera_transform.rotation_roll(-camera.rotation_speed * delta)
        elif keydown[Keyboard.C]:
            camera_transform.rotation_roll(camera.rotation_speed * delta)

        # move to view direction ( inverse front of camera matrix )
        if keydown[Keyboard.W] or self.game_backend.wheel_up:
            camera_transform.move_front(-move_speed)
        elif keydown[Keyboard.S] or self.game_backend.wheel_down:
            camera_transform.move_front(move_speed)

        # move to side
        if keydown[Keyboard.A]:
            camera_transform.move_left(-move_speed)
        elif keydown[Keyboard.D]:
            camera_transform.move_left(move_speed)

        # move to up
        if keydown[Keyboard.Q]:
            camera_transform.move_up(move_speed)
        elif keydown[Keyboard.E]:
            camera_transform.move_up(-move_speed)

        if keydown[Keyboard.SPACE]:
            camera_transform.reset_transform()

    def update(self, delta):
        self.update_camera(delta)

        self.debug_line_manager.draw_debug_line_3d(Float3(0.0, 0.0, 0.0), Float3(3.0, 0.0, 0.0), Float4(1.0, 0.0, 0.0, 1.0), width=3.0)
        self.debug_line_manager.draw_debug_line_3d(Float3(0.0, 0.0, 0.0), Float3(0.0, 3.0, 0.0), Float4(0.0, 1.0, 0.0, 1.0), width=3.0)
        self.debug_line_manager.draw_debug_line_3d(Float3(0.0, 0.0, 0.0), Float3(0.0, 0.0, 3.0), Float4(0.0, 0.0, 1.0, 1.0), width=3.0)

