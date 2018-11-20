import os
import io
import re
import traceback
from collections import OrderedDict
from xml.etree import ElementTree

ignore_xmlns = re.compile(' xmlns=".+?"')


def load_xml(filepath, encoding="utf-8"):
    if os.path.exists(filepath):
        f = io.open(filepath, mode="r", encoding=encoding)
        xmlData = "".join(list(f))
        xmlData = re.sub(ignore_xmlns, "", xmlData, count=1)
        f.close()
        xml_root = ElementTree.fromstring(xmlData)
        return xml_root


def get_xml_attrib(xml_data, key, default=""):
    if xml_data is not None and key in xml_data.attrib:
        return xml_data.attrib[key]
    return default


def get_xml_tag(xml_data, default=""):
    return xml_data.tag if xml_data is not None else default


def get_xml_text(xml_data, default=""):
    return xml_data.text if xml_data is not None else default
