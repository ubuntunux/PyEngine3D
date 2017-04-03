import os

PathResources = os.path.abspath(os.path.split(__file__)[0])
PathFonts = os.path.join(PathResources, 'Fonts')
PathMaterials = os.path.join(PathResources, 'Materials')
PathMeshes = os.path.join(PathResources, 'Meshes')
PathShaders = os.path.join(PathResources, 'Shaders')
PathTextures = os.path.join(PathResources, 'Textures')

DefaultFontFile = os.path.join(PathFonts, 'UbuntuFont.ttf')

from .ColladaLoader import Collada
from .ObjLoader import OBJ
from .ResourceManager import VertexShaderLoader, FragmentShaderLoader, MaterialInstanceLoader, MeshLoader, ResourceManager