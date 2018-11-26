import ctypes

import numpy as np

VIDEO_RESIZE_TIME = 0.5
GRAVITY = 980.0
MAX_POINT_LIGHTS = 10
NULL_POINTER = ctypes.c_void_p(0)
SHADOW_DISTANCE = 50.0
SHADOW_UPDATE_DIST = 10.0
WORK_GROUP_SIZE = 64

COLOR_BLACK = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
COLOR_BLACK_NO_ALPHA = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
COLOR_WHITE = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
COLOR_WHITE_NO_ALPHA = np.array([1.0, 1.0, 1.0, 0.0], dtype=np.float32)
