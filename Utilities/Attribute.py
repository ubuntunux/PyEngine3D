from collections import OrderedDict


class Attribute:
    def __init__(self, attrName, attrValue, attrType, isReadOnly):
        self.name = attrName
        self.value = attrValue
        self.type = attrType
        self.isReadOnly = isReadOnly


class Attributes:
    def __init__(self):
        self.attribute_map = OrderedDict()

    def clear(self):
        self.attribute_map = OrderedDict()

    def get_attribute_map(self):
        return self.attribute_map

    def get_attributes(self):
        return self.attribute_map.values()

    def get_attribute_names(self):
        return self.attribute_map.keys()

    def has_attribute(self, attrname):
        return attrname in self.attribute_map

    def get_attribute(self, attrname):
        return self.attribute_map[attrname] if attrname in self.attribute_map else None

    def set_attribute(self, attrName, attrValue, isReadOnly=False):
        if attrValue is None:
            attrValue = ""
            attrType = None
        else:
            # get type
            attrType = type(attrValue)
            # class object use name as attrValue.
            if hasattr(attrValue, "name"):
                attrValue = attrValue.name
        self.attribute_map[attrName] = Attribute(attrName, attrValue, attrType, isReadOnly)

    def delete_attribute(self, attrName):
        if attrName in self.attribute_map:
            self.attribute_map.pop(attrName)
