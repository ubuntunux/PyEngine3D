# https://www.khronos.org/collada/

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


class ColladaGeometry:
    def __init__(self, xml_geometry):
        self.name = get_xml_attrib(xml_geometry, 'name')
        self.valid = False
        self.positions = []
        self.normals = []
        self.colors = []
        self.texcoords = []
        self.indices = []
        self.parsing_geomtry(xml_geometry)

    def parsing_geomtry(self, xml_geometry):
        sources = {}  # {'source_id':source_data}
        position_source_id = ""
        semantics = {}  # {'semantic':{'source', 'offset', 'set'}}
        vertex_index_list = []  # flatten vertex list as triangle
        stride_of_index = 0

        # parse mesh
        xml_mesh = xml_geometry.find('mesh')
        if xml_mesh is not None:
            # parse sources
            for xml_source in xml_mesh.findall('source'):
                source_id = get_xml_attrib(xml_source, 'id')
                stride = get_xml_attrib(xml_source.find('technique_common/accessor'), 'stride')
                stride = convert_int(stride, 0)
                source_text = get_xml_text(xml_source.find('float_array'))
                source_data = convert_list(source_text, float, stride)
                sources[source_id] = source_data

            # get vertex position source id
            position_source_id = get_xml_attrib(xml_mesh.find('vertices/input'), 'source')
            if position_source_id.startswith("#"):
                position_source_id = position_source_id[1:]

            # parse polygons
            for tag in ('polygons', 'polylist', 'triangles'):
                xml_polygons = xml_mesh.find(tag)
                if xml_polygons is not None:
                    # parse semantic
                    for xml_semantic in xml_polygons.findall('input'):
                        set_number = get_xml_attrib(xml_semantic, 'set', '0')
                        semantic = get_xml_attrib(xml_semantic, 'semantic') + set_number  # example VERTEX0, TEXCOORD0
                        source = get_xml_attrib(xml_semantic, 'source')
                        if source.startswith("#"):
                            source = source[1:]
                        offset = convert_int(get_xml_attrib(xml_semantic, 'offset'), 0)
                        stride_of_index = max(stride_of_index, offset + 1)
                        semantics[semantic] = dict(source=source, offset=offset, set=set)
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
                                vcount_list.append(int(len(polygon_indices) / stride_of_index))
                        # triangulate
                        vertex_index_list = []
                        elapsed_vindex = 0
                        for vcount in vcount_list:
                            if vcount == 3:
                                vertex_index_list += polygon_index_list[
                                                     elapsed_vindex: elapsed_vindex + vcount * stride_of_index]
                            else:
                                polygon_indices = polygon_index_list[
                                                  elapsed_vindex: elapsed_vindex + vcount * stride_of_index]
                                vertex_index_list += convert_triangulate(polygon_indices, vcount, stride_of_index)
                            elapsed_vindex += vcount * stride_of_index
                    # make geomtry data
                    self.build_gemetry_data(sources, position_source_id, semantics, vertex_index_list,
                                            stride_of_index)
                    self.valid = True
                    return  # done

    def build_gemetry_data(self, sources, position_source_id, semantics, vertex_index_list, stride_of_index):
        self.positions = []
        self.normals = []
        self.colors = []
        self.texcoords = []
        self.indices = []
        indexMap = OrderedDict()

        for i in range(int(len(vertex_index_list) / stride_of_index)):
            vertIndices = tuple(vertex_index_list[i * stride_of_index: i * stride_of_index + stride_of_index])
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
        self.animations = []

        self.parse_geometries(xml_root)

    def parse_geometries(self, xml_root):
        for xml_geometry in xml_root.findall('library_geometries/geometry'):
            geometry = ColladaGeometry(xml_geometry)
            self.geometries.append(geometry)

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
