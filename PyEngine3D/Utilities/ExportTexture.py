import codecs
import math
import os
import pickle
import sys
import traceback
import gzip
import pprint
import itertools
import json

from ctypes import *
import numpy as np
from numpy import array, float32, uint8


def is_gz_compressed_file(filename):
    with open(filename,'rb') as f:
        return f.read(3) == b'\x1f\x8b\x08'


def export_texture(filepath, export_filepath):
    try:
        if os.path.exists(filepath):
            # Load data (deserialize)
            if is_gz_compressed_file(filepath):
                with gzip.open(filepath, 'rb') as f:
                    loaded_data = pickle.load(f)
            else:
                # human readable data
                with open(filepath, 'r') as f:
                    loaded_data = eval(f.read())
            # convert numpy array to regular array
            # if 'Texture2DArray' == loaded_data['texture_type'] or 'Texture3D' == loaded_data['texture_type']:
            #     loaded_data['data'] = list(itertools.chain(*[list(texture_data) for texture_data in loaded_data['data']]))
            # else:
            #     loaded_data['data'] = list(loaded_data['data'])

            with open(export_filepath, 'wb') as f:
                f.write(str(loaded_data))

    except:
        print(traceback.format_exc())


if __name__ == '__main__':
    if 2 < len(sys.argv):
        export_texture(sys.argv[1], sys.argv[2])
