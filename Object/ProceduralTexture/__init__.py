from .CloudTexture3D import CloudTexture3D
from .NoiseTexture3D import NoiseTexture3D
from .ForceFieldTexture3D import ForceFieldTexture3D


def CreateProceduralTexture(**datas):
    texture_class = datas.get('texture_type', None)
    if texture_class is not None:
        texture_class = eval(texture_class)
        return texture_class(**datas)
    return None
