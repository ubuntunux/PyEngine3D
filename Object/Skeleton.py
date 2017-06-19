import numpy as np

from Common import logger
from Object import TransformObject


class Bone:
    def __init__(self, name, matrix):
        self.name = name
        self.matrix = matrix
        self.parent = None
        self.children = []


class Skeleton:
    def __init__(self, **skeleton_data):
        self.name = skeleton_data.get('name', '')
        self.bones = []
        self.bind_shape_matrix = skeleton_data.get('bind_shape_matrix', '')

        bone_names = skeleton_data.get('bone_names') or []
        bone_matrices = skeleton_data.get('bone_matrices') or []
        bone_count = len(bone_matrices)
        for i, bone_name in enumerate(bone_names):
            bone_matrix = np.array(bone_matrices[i], dtype=np.float32) if i < bone_count else Maxtrix4()
            bone = Bone(name=bone_name, matrix=bone_matrix)
            self.bones.append(bone)

