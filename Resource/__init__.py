import __main__
import os

PathResources = os.path.abspath(os.path.split(__file__)[0])
PathFonts = os.path.join(PathResources, 'Fonts')
PathMaterials = os.path.join(PathResources, 'Materials')
PathMaterialInstances = os.path.join(PathResources, 'MaterialInstances')
PathMeshes = os.path.join(PathResources, 'Meshes')
PathScenes = os.path.join(PathResources, 'Scenes')
PathShaders = os.path.join(PathResources, 'Shaders')
PathTextures = os.path.join(PathResources, 'Textures')

if not os.path.exists(PathResources):
    os.makedirs(PathResources)

DefaultFontFile = os.path.join(PathFonts, 'UbuntuFont.ttf')

from .ColladaLoader import Collada
from .ObjLoader import OBJ
from .ResourceManager import ShaderLoader, MaterialInstanceLoader, MeshLoader, ResourceManager