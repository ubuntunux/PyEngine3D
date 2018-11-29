import numpy as np

from PyEngine3D.Utilities import TransformObject


class Bone:
    def __init__(self, name, index, depth, inv_bind_matrix):
        # v += {[(v * BindShapeMatrix) * InvBindMatrix * JointMatrix(animation)] * JointWeight}
        self.name = name
        self.transform = TransformObject()
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
    def __init__(self, index, **skeleton_data):
        self.name = skeleton_data.get('name', '')
        self.index = index

        self.bone_names = skeleton_data.get('bone_names', [])
        self.bones = [None, ] * len(self.bone_names)
        self.hierachy = []

        inv_bind_matrices = skeleton_data.get('inv_bind_matrices', [])

        def build_bone(hierachy, parent_bone, depth):
            for bone_name in hierachy:
                if bone_name in self.bone_names:
                    index = self.bone_names.index(bone_name)
                    bone = Bone(
                        name=bone_name,
                        index=index,
                        depth=depth,
                        inv_bind_matrix=inv_bind_matrices[index]
                    )
                    self.bones[index] = bone
                    if parent_bone is None:
                        # add root
                        self.hierachy.append(bone)
                    else:
                        parent_bone.add_child(bone)
                    # recursive build bone
                    build_bone(hierachy[bone_name], bone, depth+1)
        build_bone(skeleton_data.get('hierachy', {}), None, 0)
