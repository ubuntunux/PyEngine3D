import __main__
import os

# PathResources = os.path.abspath(os.path.join(os.path.split(__main__.__file__)[0], 'Resource'))
PathResources = 'Resource'
DefaultFontFile = os.path.join(PathResources, 'Fonts', 'UbuntuFont.ttf')
DefaultProjectFile = os.path.join(PathResources, "default.project")

from .ColladaLoader import Collada
from .ObjLoader import OBJ
from .ResourceManager import ResourceManager