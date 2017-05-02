import __main__
import os

PathResources = os.path.abspath(os.path.join(os.path.split(__main__.__file__)[0], 'Resource'))
DefaultFontFile = os.path.join(PathResources, 'Fonts', 'UbuntuFont.ttf')

from .ColladaLoader import Collada
from .ObjLoader import OBJ
from .ResourceManager import ResourceManager