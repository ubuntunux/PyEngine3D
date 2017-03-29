# https://www.khronos.org/collada/

import os, datetime, glob, traceback, pprint
from collections import OrderedDict

import numpy as np
from PIL import Image
from OpenGL.GL import *

from Resource import *
from Core import logger
from Utilities.Transform import normalize

def convertColladaToMesh(filePath):
    for filename in glob.glob(os.path.join(filePath, '*.dae')):
        obj = OBJ(filename, 1, True)
        print("Convering :", filename)
        obj.saveToMesh()
        print("Done.")


if __name__ == '__main__':
    convertColladaToMesh(PathMeshes)