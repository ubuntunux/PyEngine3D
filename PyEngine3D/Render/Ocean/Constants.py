from math import pi

import numpy as np

cm = 0.23
km = 370.0

WIND = 5.0
OMEGA = 0.84
AMPLITUDE = 0.5

CHOPPY_FACTOR = np.array([2.3, 2.1, 1.3, 0.9], dtype=np.float32)

PASSES = 8  # number of passes needed for the FFT 6 -> 64, 7 -> 128, 8 -> 256, etc
FFT_SIZE = 1 << PASSES  # size of the textures storing the waves in frequency and spatial domains

N_SLOPE_VARIANCE = 10
GRID1_SIZE = 5488.0
GRID2_SIZE = 392.0
GRID3_SIZE = 28.0
GRID4_SIZE = 2.0
GRID_SIZES = np.array([GRID1_SIZE, GRID2_SIZE, GRID3_SIZE, GRID4_SIZE], dtype=np.float32)
INVERSE_GRID_SIZES = np.array([2.0 * pi * FFT_SIZE / GRID1_SIZE,
                               2.0 * pi * FFT_SIZE / GRID2_SIZE,
                               2.0 * pi * FFT_SIZE / GRID3_SIZE,
                               2.0 * pi * FFT_SIZE / GRID4_SIZE], dtype=np.float32)


GRID_VERTEX_COUNT = 200
GRID_CELL_SIZE = np.array([1.0 / float(GRID_VERTEX_COUNT), 1.0 / float(GRID_VERTEX_COUNT)], dtype=np.float32)
