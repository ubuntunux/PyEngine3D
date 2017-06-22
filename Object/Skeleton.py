import numpy as np

from Common import logger
from Object import TransformObject


class Bone:
    def __init__(self, name, index, depth, bone_matrix, inv_bind_matrix):
        self.name = name
        print("Bone", self.name)
        self.transform = TransformObject.TransformObject()
        self.matrix = bone_matrix
        self.inv_bind_matrix = inv_bind_matrix
        self.parent = None
        self.children = []
        self.index = index
        self.depth = depth
        # print("\t" * depth, self.name, self.index)

    def set_parent(self, parent_bone):
        self.parent = parent_bone

    def add_child(self, child_bone):
        child_bone.set_parent(self)
        self.children.append(child_bone)


class Skeleton:
    def __init__(self, **skeleton_data):
        self.name = skeleton_data.get('name', '')
        self.bind_shape_matrix = skeleton_data.get('bind_shape_matrix', '')
        print("Skeleton", self.name)

        self.bones = []
        self.bone_names = skeleton_data.get('bone_names', [])
        self.inv_bind_matrices = skeleton_data.get('inv_bind_matrices', [])
        self.bone_matrices = skeleton_data.get('bone_matrices', [])

        def build_bone(hierachy, parent_bone, depth):
            for bone_name in hierachy:
                if bone_name in self.bone_names:
                    index = self.bone_names.index(bone_name)
                    inv_bind_matrix = self.inv_bind_matrices[index] if index < len(self.inv_bind_matrices) else Matrix4()
                    bone_matrix = self.bone_matrices[index] if index < len(self.bone_matrices) else Matrix4()
                    bone = Bone(name=bone_name, index=index, depth=depth, bone_matrix=bone_matrix,
                                inv_bind_matrix=inv_bind_matrix)
                    if parent_bone is None:
                        self.bones.append(bone)  # root bone
                    else:
                        parent_bone.add_child(bone)
                    build_bone(hierachy[bone_name], bone, depth+1)

        build_bone(skeleton_data.get('hierachy', {}), None, 0)


