# https://www.khronos.org/collada/

import io
import re
import traceback
from collections import OrderedDict
from xml.etree import ElementTree

from Core import logger


ignore_xmlns = re.compile(' xmlns=".+?"')


def get_attrib(xml_data, key, default=""):
    if xml_data is not None and key in xml_data.attrib:
        return xml_data.attrib[key]
    return default


def get_tag(xml_datadata, default=""):
    return xml_data.tag if xml_data is not None else default


def get_text(xml_data, default=""):
    return xml_data.text if xml_data is not None else default


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
        self.name = get_attrib(xml_geometry, 'id')
        self.sources = {}  # {'source_id':source_data}
        self.position_source_id = ""
        self.semantics = {}  # {'semantic':{'source', 'offset', 'set'}}
        self.vertex_index_list = []  # flatten vertex list as triangle
        self.stride_of_index = 0

        # parse mesh
        xml_mesh = xml_geometry.find('mesh')
        if xml_mesh is not None:
            # parse sources
            sources = {}  # {'source_id':source_data}
            for xml_source in xml_mesh.findall('source'):
                source_id = get_attrib(xml_source, 'id')
                stride = get_attrib(xml_source.find('technique_common/accessor'), 'stride')
                stride = convert_int(stride, 0)
                source_text = get_text(xml_source.find('float_array'))
                source_data = convert_list(source_text, float, stride)
                sources[source_id] = source_data

                # get vertex position source id
            position_source_id = get_attrib(xml_mesh.find('vertices/input'), 'source')
            if position_source_id.startswith("#"):
                position_source_id = position_source_id[1:]

            # parse polygons
            vertex_index_list = []
            for tag in ('polygons', 'polylist', 'triangles'):
                xml_polygons = xml_mesh.find(tag)
                if xml_polygons is not None:
                    stride_of_index = 0
                    # parse semantic
                    semantics = {}  # {'semantic':{'source', 'offset', 'set'}}
                    for xml_semantic in xml_polygons.findall('input'):
                        set_number = get_attrib(xml_semantic, 'set', '0')
                        semantic = get_attrib(xml_semantic, 'semantic') + set_number  # example VERTEX0, TEXCOORD0
                        source = get_attrib(xml_semantic, 'source')
                        if source.startswith("#"):
                            source = source[1:]
                        offset = convert_int(get_attrib(xml_semantic, 'offset'), 0)
                        stride_of_index = max(stride_of_index, offset + 1)
                        semantics[semantic] = dict(source=source, offset=offset, set=set)
                    # parse polygon indices
                    if tag == 'triangles':
                        vertex_index_list = get_text(xml_polygons.find('p'))
                        vertex_index_list = convert_list(vertex_index_list, int)
                    elif tag == 'polylist' or tag == 'polygons':
                        vcount_list = []
                        polygon_index_list = []
                        if tag == 'polylist':
                            vcount_list = convert_list(get_text(xml_polygons.find('vcount')), int)
                            # flatten list
                            polygon_index_list = convert_list(get_text(xml_polygons.find('p')), int)
                        elif tag == 'polygons':
                            for xml_p in xml_polygons.findall('p'):
                                polygon_indices = convert_list(get_text(xml_p), int)
                                # flatten list
                                polygon_index_list += polygon_indices
                                vcount_list.append(int(len(polygon_indices) / stride_of_index))
                        # triangulate
                        vertex_index_list = []
                        elapsed_vindex = 0
                        for vcount in vcount_list:
                            if vcount == 3:
                                vertex_index_list += polygon_index_list[
                                                     elapsed_vindex:elapsed_vindex + vcount * stride_of_index]
                            else:
                                polygon_indices = polygon_index_list[
                                                  elapsed_vindex:elapsed_vindex + vcount * stride_of_index]
                                vertex_index_list += convert_triangulate(polygon_indices, vcount, stride_of_index)
                            elapsed_vindex += vcount * stride_of_index
                    self.sources = sources
                    self.position_source_id = position_source_id
                    self.semantics = semantics
                    self.vertex_index_list = vertex_index_list
                    self.stride_of_index = stride_of_index
                    break


class Collada:
    def __init__(self, filepath):
        try:
            f = io.open(filepath, mode="r", encoding="utf-8")
            xmlData = "".join(list(f))
            xmlData = re.sub(ignore_xmlns, "", xmlData, count=1)
            f.close()
            xml_root = ElementTree.fromstring(xmlData)
        except:
            logger.error(traceback.format_exc())
            return

        self.collada_version = get_attrib(xml_root, 'version')
        self.author = get_text(xml_root.find("asset/contributor/author"))
        self.authoring_tool = get_text(xml_root.find("asset/contributor/authoring_tool"))
        self.created = get_text(xml_root.find("asset/created"))
        self.modified = get_text(xml_root.find("asset/modified"))
        self.unit_name = get_attrib(xml_root.find("asset/unit"), 'name', 'meter')
        self.unit_meter = get_attrib(xml_root.find("asset/unit"), 'meter')
        self.unit_meter = convert_float(self.unit_meter)
        self.up_axis = get_text(xml_root.find("asset/up_axis"))

        self.geometries = []
        self.parse_geometries(xml_root)

    def parse_geometries(self, xml_root):
        for xml_geometry in xml_root.findall('library_geometries/geometry'):
            geometry = ColladaGeometry(xml_geometry)
            self.geometries.append(geometry)

    def get_mesh_data(self):
        # Test Code : only one geometry
        geometry = self.geometries[0]

        positions = []
        normals = []
        colors = []
        texcoords = []
        indices = []
        indexMap = OrderedDict()
        stride_of_index = geometry.stride_of_index

        for i in range(int(len(geometry.vertex_index_list) / stride_of_index)):
            vertIndices = tuple(geometry.vertex_index_list[i*stride_of_index: i*stride_of_index + stride_of_index])
            if vertIndices in indexMap:
                indices.append(list(indexMap.keys()).index(vertIndices))
            else:
                indices.append(len(indexMap))
                indexMap[vertIndices] = None

                if 'VERTEX0' in geometry.semantics:
                    source_id = geometry.position_source_id
                    offset = geometry.semantics['VERTEX0']['offset']
                    positions.append(geometry.sources[source_id][vertIndices[offset]])

                if 'NORMAL0' in geometry.semantics:
                    source_id = geometry.semantics['NORMAL0']['source']
                    offset = geometry.semantics['NORMAL0']['offset']
                    normals.append(geometry.sources[source_id][vertIndices[offset]])

                if 'COLOR0' in geometry.semantics:
                    source_id = geometry.semantics['COLOR0']['source']
                    offset = geometry.semantics['COLOR0']['offset']
                    colors.append(geometry.sources[source_id][vertIndices[offset]])

                if 'TEXCOORD0' in geometry.semantics:
                    source_id = geometry.semantics['TEXCOORD0']['source']
                    offset = geometry.semantics['TEXCOORD0']['offset']
                    texcoords.append(geometry.sources[source_id][vertIndices[offset]])

        mesh_data = dict(
            positions=positions,
            normals=normals,
            texcoords=texcoords,
            indices=indices)
        return mesh_data
