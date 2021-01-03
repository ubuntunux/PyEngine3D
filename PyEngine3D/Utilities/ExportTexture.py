import codecs
import math
import os
import pickle
import sys
import traceback
import gzip
import pprint
import itertools
import struct
from ctypes import *

from OpenGL.GL import *

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
            # with open(export_filepath, 'w') as f:
            #     f.write(str(loaded_data))

            '''
            export struct {
                texture_type: i32,
                width: i32,
                height: i32,
                depth: i32,
                format: i32,
                min_filter: i32,
                mag_filter: i32,
                wrap: i32,
                data_bytes: i32,
                data: byte array
            }
            '''
            with open(export_filepath, 'wb') as f:
                # texture_type
                texture_type = loaded_data['texture_type']
                if 'Texture2D' == texture_type:
                    f.write(struct.pack('i', 1))  # VK_IMAGE_VIEW_TYPE_2D
                elif 'Texture3D' == texture_type:
                    f.write(struct.pack('i', 2))  # VK_IMAGE_VIEW_TYPE_3D
                elif 'TextureCube' == texture_type:
                    f.write(struct.pack('i', 3))  # VK_IMAGE_VIEW_TYPE_CUBE
                elif 'Texture2DArray' == texture_type:
                    f.write(struct.pack('i', 5))  # VK_IMAGE_VIEW_TYPE_2D_ARRAY
                else:
                    raise BaseException("Not implemented.")

                # width
                f.write(struct.pack('i', loaded_data['width']))

                # height
                f.write(struct.pack('i', loaded_data['height']))

                # depth
                f.write(struct.pack('i', loaded_data['depth']))

                # internal_format
                internal_format = loaded_data['internal_format']
                if GL_R16F == internal_format:
                    # 16f -> 32f
                    f.write(struct.pack('i', 100))  # VK_FORMAT_R32_SFLOAT = 100,
                else:
                    raise BaseException("Not implemented.")

                # min_filter
                min_filter = loaded_data['min_filter']
                if GL_LINEAR == min_filter:
                    f.write(struct.pack('i', 1))  # VK_FILTER_LINEAR = 1,
                else:
                    raise BaseException("Not implemented.")

                # mag_filter
                mag_filter = loaded_data['mag_filter']
                if GL_LINEAR == mag_filter:
                    f.write(struct.pack('i', 1))  # VK_FILTER_LINEAR = 1,
                else:
                    raise BaseException("Not implemented.")

                # wrap
                wrap = loaded_data['wrap']
                if GL_REPEAT == wrap:
                    f.write(struct.pack('i', 0))  # VK_SAMPLER_ADDRESS_MODE_REPEAT = 0,
                else:
                    raise BaseException("Not implemented.")

                # data
                data = loaded_data['data'].tobytes()
                f.write(struct.pack('i', len(data)))
                f.write(data)
    except:
        print(traceback.format_exc())


if __name__ == '__main__':
    if 2 < len(sys.argv):
        export_texture(sys.argv[1], sys.argv[2])
