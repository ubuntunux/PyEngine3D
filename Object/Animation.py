from Common import logger
from Utilities import *


class Animation:
    def __init__(self, name, index, skeleton, animation_data):
        self.name = name
        self.index = index
        self.skeleton = skeleton
        self.frame_count = 0
        self.nodes = []  # order by bone index
        for i, animation_node_data in enumerate(animation_data):
            animation_node = AnimationNode(self.skeleton.bones[i], animation_node_data)
            self.frame_count = max(self.frame_count, len(animation_node.frame_times))
            self.nodes.append(animation_node)
        self.last_frame = -1.0
        self.animation_transforms = np.array([Matrix4() for i in range(len(self.nodes))], dtype=np.float32)
        # just update animation transforms
        self.get_animation_transforms(0.0)

    def get_animation_node_transform(self, bone_index, frame=0.0):
        return self.nodes[bone_index].get_transform(frame)

    def get_animation_transforms(self, frame=0.0):
        if self.last_frame == frame:
            return self.animation_transforms
        else:
            self.animation_transforms[...] = [node.get_transform(frame) for node in self.nodes]
            return self.animation_transforms


class AnimationNode:
    def __init__(self, bone, animation_node_data):
        self.name = animation_node_data.get('name', '')
        self.bone = bone
        self.target = animation_node_data.get('target', '')  # bone name
        self.frame_times = animation_node_data.get('times', [])
        # self.transforms = animation_node_data.get('transforms', [])
        self.locations = animation_node_data.get('locations', [])
        self.rotations = animation_node_data.get('rotations', [])
        self.scales = animation_node_data.get('scales', [])
        self.interpoations = animation_node_data.get('interpoations', [])
        self.in_tangents = animation_node_data.get('in_tangents', [])
        self.out_tangents = animation_node_data.get('out_tangents', [])

        self.frame_count = len(self.frame_times)
        self.last_frame = -1.0
        self.transform = MATRIX4_IDENTITY.copy()
        # just update transform
        self.get_transform(0.0)

    def get_transform(self, frame=0.0):
        if self.last_frame == frame or self.frame_count == 0:
            return self.transform
        else:
            self.last_frame = frame

            rate = frame - int(frame)
            frame = int(frame) % self.frame_count
            next_frame = (frame + 1) % self.frame_count
            
            setIdentityMatrix(self.transform)
            if frame < self.frame_count:
                rotation = slerp(self.rotations[frame], self.rotations[next_frame], rate)
                # rotation = normalize(lerp(self.rotations[frame], self.rotations[next_frame], rate))
                location = lerp(self.locations[frame], self.locations[next_frame], rate)
                scale = lerp(self.scales[frame], self.scales[next_frame], rate)
                quaternion_to_matrix(rotation, self.transform)
                matrix_scale(self.transform, *scale)
                self.transform[3, 0:3] = location
            self.transform[...] = np.dot(self.bone.inv_bind_matrix, self.transform)
            return self.transform

