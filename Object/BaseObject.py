from Object import TransformObject

#------------------------------#
# CLASS : BaseObject
#------------------------------#
class BaseObject(TransformObject):
    def __init__(self, name='', pos=(0,0,0)):
        # init TransformObject
        TransformObject.__init__(self, pos)
        self.name = name
        self.selected = False

    def setSelected(self, selected):
        self.selected = selected
