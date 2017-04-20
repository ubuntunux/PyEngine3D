from Core import logger, CoreManager
from Object import BaseObject


# ------------------------------ #
# CLASS : Camera
# ------------------------------ #
class Camera(BaseObject):
    def __init__(self, name):
        BaseObject.__init__(self, name, (0, 0, 0), None)

        self.fov = None
        self.near = None
        self.far = None
        self.move_speed = None
        self.pan_speed = None
        self.rotation_speed = None

    def initialize(self):
        config = CoreManager.CoreManager.instance().config
        # get properties
        self.fov = config.Camera.fov
        self.near = config.Camera.near
        self.far = config.Camera.far
        self.move_speed = config.Camera.move_speed
        self.pan_speed = config.Camera.pan_speed
        self.rotation_speed = config.Camera.rotation_speed

    # override : draw
    def draw(self, *args, **kargs):
        pass

    def update(self):
        self.transform.updateTransform()
        self.transform.updateInverseTransform()  # update view matrix
