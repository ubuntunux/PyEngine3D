from .NoiseTexture3D import NoiseTexture3D
from .FFTOceanTexture import FFTOceanTexture


def CreateProceduralTexture(**datas):
    texture_class = datas.get('texture_type', None)
    if texture_class is not None:
        texture_class = eval(texture_class)
        return texture_class(**datas)
    return None
