# https://www.khronos.org/collada/

import os
import io
import re
import traceback
import copy
from collections import OrderedDict

from Core import logger
from Utilities import load_xml, get_xml_attrib, get_xml_tag, get_xml_text


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
    data_list = [data_type(x) for x in data.strip().split()]
    if stride < 2:
        return data_list
    else:
        return [data_list[i * stride:i * stride + stride] for i in range(int(len(data_list) / stride))]


def convert_triangulate(polygon, vcount, stride=1):
    indices_list = [polygon[i * stride:i * stride + stride] for i in range(int(len(polygon) / stride))]
    triangulated_list = []
    # first triangle
    triangulated_list += indices_list[0]
    triangulated_list += indices_list[1]
    triangulated_list += indices_list[2]
    for i in range(3, vcount):
        triangulated_list += indices_list[0]
        triangulated_list += indices_list[i - 1]
        triangulated_list += indices_list[i]


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


class ColladaGeometry:
    def __init__(self, xml_geometry):
        self.valid = False
        self.name = get_xml_attrib(xml_geometry, 'name')
        self.id = get_xml_attrib(xml_geometry, 'id')
        self.positions = []
        self.normals = []
        self.colors = []
        self.texcoords = []
        self.indices = []
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
            position_source_id = get_xml_attrib(xml_mesh.find('vertices/input'), 'source')
            if position_source_id.startswith("#"):
                position_source_id = position_source_id[1:]

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
                    self.build(sources, position_source_id, semantics, vertex_index_list, semantic_stride)
                    self.valid = True
                    return  # done

    def build(self, sources, position_source_id, semantics, vertex_index_list, semantic_stride):
        self.positions = []
        self.normals = []
        self.colors = []
        self.texcoords = []
        self.indices = []
        indexMap = OrderedDict()

        for i in range(int(len(vertex_index_list) / semantic_stride)):
            vertIndices = tuple(vertex_index_list[i * semantic_stride: i * semantic_stride + semantic_stride])
            if vertIndices in indexMap:
                self.indices.append(list(indexMap.keys()).index(vertIndices))
            else:
                self.indices.append(len(indexMap))
                indexMap[vertIndices] = ()

                if 'VERTEX0' in semantics:
                    source_id = position_source_id
                    offset = semantics['VERTEX0']['offset']
                    self.positions.append(sources[source_id][vertIndices[offset]])

                if 'NORMAL0' in semantics:
                    source_id = semantics['NORMAL0']['source']
                    offset = semantics['NORMAL0']['offset']
                    self.normals.append(sources[source_id][vertIndices[offset]])

                if 'COLOR0' in semantics:
                    source_id = semantics['COLOR0']['source']
                    offset = semantics['COLOR0']['offset']
                    self.colors.append(sources[source_id][vertIndices[offset]])

                if 'TEXCOORD0' in semantics:
                    source_id = semantics['TEXCOORD0']['source']
                    offset = semantics['TEXCOORD0']['offset']
                    self.texcoords.append(sources[source_id][vertIndices[offset]])


class ColladaContoller:
    def __init__(self, xml_controller):
        self.valid = False
        self.name = get_xml_attrib(xml_controller, 'name')
        self.id = get_xml_attrib(xml_controller, 'id')
        self.bind_shape_matrix = None
        self.parsing(xml_controller)

    def parsing(self, xml_controller):
        sources = {}  # {'source_id':source_data}
        bind_shape_matrix = []
        position_source_id = ""
        semantics = {}  # {'semantic':{'source', 'offset', 'set'}}
        vertex_index_list = []  # flatten vertex list as triangle
        semantic_stride = 0

        # parse mesh
        xml_skin = xml_controller.find('skin')
        if xml_skin is not None:
            # parsing bind_shape_matrix
            xml_bind_shape_matrix = xml_skin.find('bind_shape_matrix')
            if xml_bind_shape_matrix is not None:
                bind_shape_matrix = get_xml_text(xml_bind_shape_matrix, None)
                if bind_shape_matrix:
                    bind_shape_matrix = convert_list(bind_shape_matrix)
                else:
                    bind_shape_matrix = [0, ] * 16  # matrix4x4

            # parse sources
            sources = parsing_source_data(xml_skin)

            # parse vertex_weights
            xml_vertex_weights = xml_skin.find('vertex_weights')
            if xml_vertex_weights is not None:
                # parse semantic
                semantics = parsing_sematic(xml_vertex_weights)
                semantic_stride = len(semantics)

                # parse vertex_weights
                vcount_text = get_xml_text(xml_vertex_weights.find('vcount'))
                v_text = get_xml_text(xml_vertex_weights.find('v'))
                vcount_list = []
                skin_index_list = []
                if vcount_text:
                    vcount_list = convert_list(vcount_text, int)
                if v_text:
                    skin_index_list = convert_list(v_text, int)

                # make geomtry data
                self.build(sources, semantics, vcount_list, skin_index_list, semantic_stride)
                self.valid = True
                return  # done

    def build(self, sources, semantics, vcount_list, skin_index_list, semantic_stride):
        self.positions = []
        self.normals = []
        self.colors = []
        self.texcoords = []
        self.indices = []
        indexMap = OrderedDict()

        for i in range(int(len(skin_index_list) / semantic_stride)):
            vertIndices = tuple(skin_index_list[i * semantic_stride: i * semantic_stride + semantic_stride])
            if vertIndices in indexMap:
                self.indices.append(list(indexMap.keys()).index(vertIndices))
            else:
                self.indices.append(len(indexMap))
                indexMap[vertIndices] = ()

                if 'VERTEX0' in semantics:
                    source_id = position_source_id
                    offset = semantics['VERTEX0']['offset']
                    self.positions.append(sources[source_id][vertIndices[offset]])

                if 'NORMAL0' in semantics:
                    source_id = semantics['NORMAL0']['source']
                    offset = semantics['NORMAL0']['offset']
                    self.normals.append(sources[source_id][vertIndices[offset]])

                if 'COLOR0' in semantics:
                    source_id = semantics['COLOR0']['source']
                    offset = semantics['COLOR0']['offset']
                    self.colors.append(sources[source_id][vertIndices[offset]])

                if 'TEXCOORD0' in semantics:
                    source_id = semantics['TEXCOORD0']['source']
                    offset = semantics['TEXCOORD0']['offset']
                    self.texcoords.append(sources[source_id][vertIndices[offset]])


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
        self.unit_meter = get_xml_attrib(xml_root.find("asset/unit"), 'meter')
        self.unit_meter = convert_float(self.unit_meter)
        self.up_axis = get_xml_text(xml_root.find("asset/up_axis"))

        self.geometries = []
        self.controllers = []
        self.animations = []

        for xml_geometry in xml_root.findall('library_geometries/geometry'):
            geometry = ColladaGeometry(xml_geometry)
            self.geometries.append(geometry)

        for xml_controller in xml_root.findall('library_controllers/controller'):
            controller = ColladaContoller(xml_controller)
            self.controllers.append(controller)

    def get_geometry_data(self):
        geometry_datas = []
        for geometry in self.geometries:
            geometry_datas.append(dict(
                positions=copy.copy(geometry.positions),
                normals=copy.copy(geometry.normals),
                colors=copy.copy(geometry.colors),
                texcoords=copy.copy(geometry.texcoords),
                indices=copy.copy(geometry.indices)
            ))

# from Core import logger
# xml_root = load_xml(os.path.join('..', 'Resource', 'Meshes', 'anim.dae'))
# xml_controllers = xml_root.findall('library_controllers/controller')
# ColladaContoller(xml_controllers[0])