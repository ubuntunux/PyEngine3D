from collections import OrderedDict


class Attribute:
    def __init__(self, attrName, attrValue, attrType, isReadOnly):
        self.name = attrName
        self.value = attrValue
        self.type = attrType
        self.isReadOnly = isReadOnly


class Attributes:
    def __init__(self):
        self.attributeMap = OrderedDict()

    def getAttribute(self, attrname):
        return self.attributeMap[attrname] if attrname in self.attributeMap else None

    def getAttributes(self):
        return self.attributeMap.values()

    def getAttributeNames(self):
        return self.attributeMap.keys()

    def setAttribute(self, attrName, attrValue, attrType=None, isReadOnly=False):
        if attrType is None:
            attrType = type(attrValue)
        self.attributeMap[attrName] = Attribute(attrName, attrValue, attrType, isReadOnly)
