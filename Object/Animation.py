from Common import logger
from Utilities import *


class AnimationNode:
    def __init__(self, **animation_data):
        self.name = animation_data.get('name', '')
        self.target = animation_data.get('target', '')
        self.times = animation_data.get('times', [])
        self.transform = Matrix4()
        self.transforms = animation_data.get('transforms', [])
        self.locations = animation_data.get('locations', [])
        self.rotations = animation_data.get('rotations', [])
        self.scales = animation_data.get('scales', [])
        self.interpoations = animation_data.get('interpoations', [])
        self.in_tangents = animation_data.get('in_tangents', [])
        self.out_tangents = animation_data.get('out_tangents', [])

    def get_transform(self, frame=0):
        setIdentityMatrix(self.transform)
        if frame < len(self.times):
            # quaternion_to_matrix(self.rotations[frame], self.transform)
            # matrix_scale(self.transform, *self.scales[frame])
            # self.transform[3, 0:3] = self.locations[frame]
            self.transform[...] = self.transforms[frame][...]
        return self.transform


