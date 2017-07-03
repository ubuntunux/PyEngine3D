# https://www.khronos.org/collada/

import os
import io
import re
import traceback
import copy
from collections import OrderedDict

import numpy as np

from Common import logger
from Utilities import *


def convert_float(data, default=0.0):
    try:
        return float(data)
    except:
        pass
    return default


def convert_int(data, default=0):
    try:
        return int(data)
    except:
        pass
    return default


def convert_list(data, data_type=float, stride=1):
    if data:
        data_list = [data_type(x) for x in data.strip().split()]
    else:
        return []
    if stride < 2:
        return data_list
    else:
        return [data_list[i * stride:i * stride + stride] for i in range(int(len(data_list) / stride))]


def parsing_source_data(xml_element):
    sources = {}
    for xml_source in xml_element.findall('source'):
        source_id = get_xml_attrib(xml_source, 'id')
        stride = get_xml_attrib(xml_source.find('technique_common/accessor'), 'stride')
        stride = convert_int(stride, 0)
        source_data = None
        for tag, data_type in [('float_array', float), ('Name_array', str)]:
            xml_array = xml_source.find(tag)
            if xml_array is not None:
                source_text = get_xml_text(xml_array)
                if source_text:
                    source_data = convert_list(source_text, data_type, stride)
                break
        sources[source_id] = source_data
    return sources


def parsing_sematic(xml_element):
    # parse semantic
    semantics = {}
    for xml_semantic in xml_element.findall('input'):
        set_number = get_xml_attrib(xml_semantic, 'set', '0')
        semantic = get_xml_attrib(xml_semantic, 'semantic') + set_number  # ex) VERTEX0, TEXCOORD0
        source = get_xml_attrib(xml_semantic, 'source')
        if source.startswith("#"):
            source = source[1:]
        offset = convert_int(get_xml_attrib(xml_semantic, 'offset'), 0)
        semantics[semantic] = dict(source=source, offset=offset, set=set_number)
    return semantics


class ColladaNode:
    def __init__(self, xml_node, parent=None, depth=0):
        self.valid = False
        self.name = get_xml_attrib(xml_node, 'name').replace('.', '_')
        self.id = get_xml_attrib(xml_node, 'id').replace('.', '_')
        self.type = get_xml_attrib(xml_node, 'type')
        self.matrix = Matrix4()
        self.parent = parent
        self.children = []

        self.instance_controller = get_xml_attrib(xml_node.find('instance_controller'), 'url')
        if self.instance_controller.startswith('#'):
            self.instance_controller = self.instance_controller[1:]

        self.instance_geometry = get_xml_attrib(xml_node.find('instance_geometry'), 'url')
        if self.instance_geometry.startswith('#'):
            self.instance_geometry = self.instance_geometry[1:]

        self.parsing_matrix(xml_node)

        for xml_child_node in xml_node.findall('node'):
            child = ColladaNode(xml_child_node, self, depth + 1)
            self.children.append(child)

    def parsing_matrix(self, xml_node):
        xml_matrix = xml_node.find('matrix')
        if xml_matrix is not None:
            matrix = get_xml_text(xml_matrix)
            matrix = [eval(x) for x in matrix.split()]
            if len(matrix) == 16:
                # column major matrix to row major matrix
                self.matrix = np.array(matrix, dtype=np.float32).reshape(4, 4)
        else:
            xml_translate = xml_node.find('translate')
            if xml_translate is not None:
                translation = [eval(x) for x in get_xml_text(xml_translate).split()]
                if len(translation) == 3:
                    matrix_translate(self.matrix, *translation)
                else:
                    logger.error('%s node has a invalid translate.' % self.name)
            xml_rotates = xml_node.findall('rotate')
            for xml_rotate in xml_rotates:
                rotation = [eval(x) for x in get_xml_text(xml_rotate).split()]
                if len(rotation) == 4:
                    axis = get_xml_attrib(xml_rotate, 'sid')
                    if axis == 'rotationX':
                        matrix_rotateX(self.matrix, rotation[3])
                    elif axis == 'rotationY':
                        matrix_rotateY(self.matrix, rotation[3])
                    elif axis == 'rotationZ':
                        matrix_rotateZ(self.matrix, rotation[3])
                    else:
                        logger.error('%s node has a invalid rotate.' % self.name)
            xml_scale = xml_node.find('scale')
            if xml_scale is not None:
                scale = [eval(x) for x in get_xml_text(xml_scale).split()]
                if len(scale) == 3:
                    matrix_scale(self.matrix, *scale)
                else:
                    logger.error('%s node has a invalid scale.' % self.name)


class ColladaContoller:
    def __init__(self, xml_controller, nodes):
        self.valid = False
        self.name = get_xml_attrib(xml_controller, 'name').replace('.', '_')
        self.id = get_xml_attrib(xml_controller, 'id').replace('.', '_')
        self.skin_source = ""
        self.matrix = Matrix4()
        self.bind_shape_matrix = Matrix4()
        self.hierachy = dict()

        self.bone_names = []
        self.bone_indicies = []
        self.bone_weights = []
        self.inv_bind_matrices = []
        self.bone_matrices = []

        self.parsing(xml_controller)

        # find root amature
        root_node = None
        for node in nodes:
            if self.name == node.name:
                self.matrix = node.matrix
                root_node = node
                break

        self.bone_matrices = [Matrix4() for i in range(len(self.bone_names))]

        def build_hierachy(current_node, tree):
            for child in current_node.children:
                tree[child.name] = dict()
                if child.name in self.bone_names:
                    index = self.bone_names.index(child.name)
                    self.bone_matrices[index] = child.matrix.copy()
                else:
                    # maybe dummy...
                    pass
                build_hierachy(child, tree[child.name])

        if root_node:
            build_hierachy(root_node, self.hierachy)

    def parsing(self, xml_controller):
        sources = {}  # {'source_id':source_data}
        joins_semantics = {}  # {'semantic':{'source', 'offset', 'set'}}
        weights_semantics = {}  # {'semantic':{'source', 'offset', 'set'}}
        vertex_index_list = []  # flatten vertex list as triangle

        # parse mesh
        xml_skin = xml_controller.find('skin')
        if xml_skin is not None:
            self.skin_source = get_xml_attrib(xml_skin, 'source', "")
            if self.skin_source and self.skin_source.startswith('#'):
                self.skin_source = self.skin_source[1:]

            # parsing bind_shape_matrix
            bind_shape_matrix = get_xml_text(xml_skin.find('bind_shape_matrix'), None)
            if bind_shape_matrix:
                self.bind_shape_matrix = np.array(convert_list(bind_shape_matrix), dtype=np.float32).reshape(4, 4)
            else:
                self.bind_shape_matrix = Matrix4()

            # parse sources
            sources = parsing_source_data(xml_skin)

            # get vertex position source id
            xml_joints = xml_skin.find('joints')
            if xml_joints is not None:
                joins_semantics = parsing_sematic(xml_joints)

            # parse vertex weights
            xml_vertex_weights = xml_skin.find('vertex_weights')
            if xml_vertex_weights is not None:
                # parse semantic
                weights_semantics = parsing_sematic(xml_vertex_weights)

                # parse vertex weights
                vcount_text = get_xml_text(xml_vertex_weights.find('vcount'))
                v_text = get_xml_text(xml_vertex_weights.find('v'))
                vcount_list = convert_list(vcount_text, int)
                v_list = convert_list(v_text, int)

                # make geomtry data
                self.build(sources, joins_semantics, weights_semantics, vcount_list, v_list)
                return  # done

    def build(self, sources, joins_semantics, weights_semantics, vcount_list, v_list):
        semantic_stride = len(weights_semantics)
        # build weights and indicies
        i = 0
        for vcount in vcount_list:
            bone_indicies = []
            bone_weights = []
            indicies = v_list[i: i + vcount * semantic_stride]
            i += vcount * semantic_stride
            for v in range(vcount):
                if 'JOINT0' in weights_semantics:
                    offset = weights_semantics['JOINT0']['offset']
                    bone_indicies.append(indicies[offset + v * semantic_stride])
                if 'WEIGHT0' in weights_semantics:
                    source_id = weights_semantics['WEIGHT0']['source']
                    offset = weights_semantics['WEIGHT0']['offset']
                    bone_weights.append(sources[source_id][indicies[offset + v * semantic_stride]])
            self.bone_indicies.append(bone_indicies)
            self.bone_weights.append(bone_weights)
        # joints
        if 'JOINT0' in joins_semantics:
            joints_source = joins_semantics['JOINT0'].get('source', '')
            self.bone_names = sources.get(joints_source, [])
        # INV_BIND_MATRIX
        if 'INV_BIND_MATRIX0' in joins_semantics:
            inv_bind_matrix_source = joins_semantics['INV_BIND_MATRIX0'].get('source', '')
            self.inv_bind_matrices = sources.get(inv_bind_matrix_source, [])
            self.inv_bind_matrices = [np.array(inv_bind_matrix, dtype=np.float32).reshape(4, 4) for inv_bind_matrix in
                                      self.inv_bind_matrices]
        self.valid = True


class ColladaGeometry:
    def __init__(self, xml_geometry, controllers, nodes):
        self.valid = False
        self.name = get_xml_attrib(xml_geometry, 'name').replace('.', '_')
        self.id = get_xml_attrib(xml_geometry, 'id').replace('.', '_')

        self.positions = []
        self.bone_indicies = []
        self.bone_weights = []
        self.normals = []
        self.colors = []
        self.texcoords = []
        self.indices = []

        # find matched controller
        self.controller = None
        for controller in controllers:
            if self.id == controller.skin_source:
                self.controller = controller
                break

        # find matrix
        self.matrix = Matrix4()
        for node in nodes:
            if self.name == node.name:
                self.matrix = node.matrix
                break

        if self.controller:
            # coulmn-major matrix calculation.
            self.matrix = np.dot(controller.bind_shape_matrix, self.matrix)

        self.parsing(xml_geometry)

    def parsing(self, xml_geometry):
        sources = {}  # {'source_id':source_data}
        position_source_id = ""
        semantics = {}  # {'semantic':{'source', 'offset', 'set'}}
        vertex_index_list = []  # flatten vertex list as triangle
        semantic_stride = 0

        # parse mesh
        xml_mesh = xml_geometry.find('mesh')
        if xml_mesh is not None:
            # parse sources
            sources = parsing_source_data(xml_mesh)

            # get vertex position source id
            for xml_position in xml_mesh.findall('vertices/input'):
                if get_xml_attrib(xml_position, 'semantic') == 'POSITION':
                    position_source_id = get_xml_attrib(xml_position, 'source')
                    if position_source_id.startswith("#"):
                        position_source_id = position_source_id[1:]
                    break

            # parse polygons
            for tag in ('polygons', 'polylist', 'triangles'):
                xml_polygons = xml_mesh.find(tag)
                if xml_polygons is not None:
                    # parse semantic
                    semantics = parsing_sematic(xml_polygons)
                    semantic_stride = len(semantics)

                    # parse polygon indices
                    if tag == 'triangles':
                        vertex_index_list = get_xml_text(xml_polygons.find('p'))
                        vertex_index_list = convert_list(vertex_index_list, int)
                    elif tag == 'polylist' or tag == 'polygons':
                        vcount_list = []
                        polygon_index_list = []
                        if tag == 'polylist':
                            vcount_list = convert_list(get_xml_text(xml_polygons.find('vcount')), int)
                            # flatten list
                            polygon_index_list = convert_list(get_xml_text(xml_polygons.find('p')), int)
                        elif tag == 'polygons':
                            for xml_p in xml_polygons.findall('p'):
                                polygon_indices = convert_list(get_xml_text(xml_p), int)
                                # flatten list
                                polygon_index_list += polygon_indices
                                vcount_list.append(int(len(polygon_indices) / semantic_stride))
                        # triangulate
                        vertex_index_list = []
                        elapsed_vindex = 0
                        for vcount in vcount_list:
                            if vcount == 3:
                                vertex_index_list += polygon_index_list[
                                                     elapsed_vindex: elapsed_vindex + vcount * semantic_stride]
                            else:
                                polygon_indices = polygon_index_list[
                                                  elapsed_vindex: elapsed_vindex + vcount * semantic_stride]
                                vertex_index_list += convert_triangulate(polygon_indices, vcount, semantic_stride)
                            elapsed_vindex += vcount * semantic_stride
                    # make geomtry data
                    self.build(sources, position_source_id, semantics, semantic_stride, vertex_index_list)
                    return  # done

    def build(self, sources, position_source_id, semantics, semantic_stride, vertex_index_list):
        isSwapYZ = False

        # check vertex count with bone weight count
        if self.controller:
            vertex_count = len(sources[position_source_id]) if position_source_id  else 0
            bone_weight_count = len(self.controller.bone_indicies)
            if vertex_count != bone_weight_count:
                logger.error(
                    "Different count. vertex_count : %d, bone_weight_count : %d" % (vertex_count, bone_weight_count))
                return

        indexMap = []
        for i in range(int(len(vertex_index_list) / semantic_stride)):
            vertIndices = tuple(vertex_index_list[i * semantic_stride: i * semantic_stride + semantic_stride])
            if vertIndices in indexMap:
                self.indices.append(indexMap.index(vertIndices))
            else:
                self.indices.append(len(indexMap))
                indexMap.append(vertIndices)

                if 'VERTEX0' in semantics:
                    source_id = position_source_id
                    offset = semantics['VERTEX0']['offset']
                    posisiton = sources[source_id][vertIndices[offset]]
                    if isSwapYZ:
                        posisiton[1], posisiton[2] = -posisiton[2], posisiton[1]
                    self.positions.append(posisiton)
                    if self.controller:
                        self.bone_indicies.append(self.controller.bone_indicies[vertIndices[offset]])
                        self.bone_weights.append(self.controller.bone_weights[vertIndices[offset]])

                if 'NORMAL0' in semantics:
                    source_id = semantics['NORMAL0']['source']
                    offset = semantics['NORMAL0']['offset']
                    normal = sources[source_id][vertIndices[offset]]
                    if isSwapYZ:
                        normal[1], normal[2] = -normal[2], normal[1]
                    self.normals.append(normal)

                if 'COLOR0' in semantics:
                    source_id = semantics['COLOR0']['source']
                    offset = semantics['COLOR0']['offset']
                    self.colors.append(sources[source_id][vertIndices[offset]])

                if 'TEXCOORD0' in semantics:
                    source_id = semantics['TEXCOORD0']['source']
                    offset = semantics['TEXCOORD0']['offset']
                    self.texcoords.append(sources[source_id][vertIndices[offset]])
        self.valid = True


class Collada:
    def __init__(self, filepath):
        try:
            xml_root = load_xml(filepath)
        except:
            logger.error(traceback.format_exc())
            return

        self.collada_version = get_xml_attrib(xml_root, 'version')
        self.author = get_xml_text(xml_root.find("asset/contributor/author"))
        self.authoring_tool = get_xml_text(xml_root.find("asset/contributor/authoring_tool"))
        self.created = get_xml_text(xml_root.find("asset/created"))
        self.modified = get_xml_text(xml_root.find("asset/modified"))
        self.unit_name = get_xml_attrib(xml_root.find("asset/unit"), 'name', 'meter')
        self.unit_meter = convert_float(get_xml_attrib(xml_root.find("asset/unit"), 'meter'))
        self.up_axis = get_xml_text(xml_root.find("asset/up_axis"))

        self.nodes = []
        self.geometries = []
        self.controllers = []
        self.animations = []

        for xml_node in xml_root.findall('library_visual_scenes/visual_scene/node'):
            node = ColladaNode(xml_node)
            self.nodes.append(node)

        for xml_controller in xml_root.findall('library_controllers/controller'):
            controller = ColladaContoller(xml_controller, self.nodes)
            self.controllers.append(controller)

        for xml_geometry in xml_root.findall('library_geometries/geometry'):
            geometry = ColladaGeometry(xml_geometry, self.controllers, self.nodes)
            self.geometries.append(geometry)

    def get_mesh_data(self):
        geometry_datas = self.get_geometry_data()
        skeleton_datas = self.get_skeleton_data()
        mesh_data = dict(
            geometry_datas=geometry_datas,
            skeleton_datas=skeleton_datas
        )
        return mesh_data

    def get_skeleton_data(self):
        # v += {[(v * BindShapeMatrix) * InvBindMatrix * JointMatrix(animation)] * JointWeight}
        skeleton_datas = []
        check_duplicated = []
        for controller in self.controllers:
            if controller.name not in check_duplicated:
                check_duplicated.append(controller.name)
                skeleton_data = dict(
                    name=controller.name,
                    # matrix of Amature
                    matrix=convert_matrix(controller.matrix, True, self.up_axis),
                    hierachy=controller.hierachy,  # bone names map as hierachy
                    bone_names=controller.bone_names,  # bone name list
                    # local matrix of bone
                    bone_matrices=[convert_matrix(matrix, True, self.up_axis) for matrix in controller.bone_matrices],
                    # inv matrix of bone
                    inv_bind_matrices=[convert_matrix(matrix, True, self.up_axis) for matrix in
                                       controller.inv_bind_matrices],
                )
                skeleton_datas.append(skeleton_data)
        return skeleton_datas

    def get_geometry_data(self):
        geometry_datas = []
        for geometry in self.geometries:
            # swap y and z
            geometry.matrix = convert_matrix(geometry.matrix, True, self.up_axis)

            for i, position in enumerate(geometry.positions):
                geometry.positions[i] = np.dot([position[0], position[1], position[2], 1.0], geometry.matrix)[:3]

            for i, normal in enumerate(geometry.normals):
                geometry.normals[i] = np.dot([normal[0], normal[1], normal[2], 0.0], geometry.matrix)[:3]

            geometry_data = dict(
                name=geometry.name,
                matrix=copy.deepcopy(geometry.matrix),
                positions=copy.deepcopy(geometry.positions),
                normals=copy.deepcopy(geometry.normals),
                colors=copy.deepcopy(geometry.colors),
                texcoords=copy.deepcopy(geometry.texcoords),
                indices=copy.deepcopy(geometry.indices)
            )
            if geometry.controller:
                geometry_data['skeleton'] = geometry.controller.name
                geometry_data['bone_indicies'] = copy.deepcopy(geometry.bone_indicies)
                geometry_data['bone_weights'] = copy.deepcopy(geometry.bone_weights)
            geometry_datas.append(geometry_data)
        return geometry_datas

'''
<bind_shape_matrix>
    # geometry world matrix
    1 0 0 2.98023e-8 / 0 1 0 -3.173189 / 0 0 1 1.868991 / 0 0 0 1
</bind_shape_matrix>

<float_array id="Armature_Suzanne_001-skin-bind_poses-array" count="32">
    # bone world inverse matrix
    1 0 0 0 / 0 0 1 -0.8127056 / 0 -1 0 -3.173189 / 0 0 0 1
    1 0 0 0 / 0 0 1 -2.423439 / 0 -1 0 -3.173189 / 0 0 0 1
</float_array>

# visual scene nodes - affect to only non-skinned mesh and amature(root skeleton)
<amature matrix sid="transform">
    # amature world matrix
    1 0 0 2.98023e-8 / 0 1 0 -3.173189 / 0 0 1 0.8127055 / 0 0 0 1
</matrix>
<bone matrix sid="transform">
    # not use - bone local matrix
    1 0 0 0 / 0 0 -1 0 / 0 1 0 0 / 0 0 0 1
</matrix>
<bone.001 matrix sid="transform">
    # not use - bone local matrix
    1 0 0 0 / 0 1 0 1.610733 / 0 0 1 0 / 0 0 0 1
</matrix>
'''


if __name__ == '__main__':
    mesh = Collada(os.path.join('..', 'Resource', 'Externals', 'Meshes', 'skin_test3.dae'))
    mesh.get_mesh_data()
