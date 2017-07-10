from Common import logger
from Utilities import *


class AnimationNode:
    def __init__(self, **animation_data):
        self.name = animation_data.get('name', '')
        self.target = animation_data.get('target', '')
        self.times = animation_data.get('times', [])
        self.transform = Matrix4()
        # self.transforms = animation_data.get('transforms', [])
        self.locations = animation_data.get('locations', [])
        self.rotations = animation_data.get('rotations', [])
        self.scales = animation_data.get('scales', [])
        self.interpoations = animation_data.get('interpoations', [])
        self.in_tangents = animation_data.get('in_tangents', [])
        self.out_tangents = animation_data.get('out_tangents', [])

    def get_transform(self, frame=0.0):
        rate = frame - int(frame)
        frame = int(frame)
        next_frame = frame + 1 if frame + 1 < len(self.times) else 0
        setIdentityMatrix(self.transform)
        if frame < len(self.times):
            rotation = slerp(self.rotations[frame], self.rotations[next_frame], rate)
            # rotation = normalize(lerp(self.rotations[frame], self.rotations[next_frame], rate))
            location = lerp(self.locations[frame], self.locations[next_frame], rate)
            scale = lerp(self.scales[frame], self.scales[next_frame], rate)

            quaternion_to_matrix(rotation, self.transform)
            matrix_scale(self.transform, *scale)
            self.transform[3, 0:3] = location
        return self.transform


