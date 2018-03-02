import numpy as np
from numpy import array, mod, floor, ceil, sin, cos, dot


def get_default_3d_data(size):
    value = 255.0 / float(size)
    data = array([0, 0, 0, 255] * size * size * size, dtype=np.uint8)
    for z in range(size):
        for y in range(size):
            for x in range(size):
                index = (x + y * size + z * size * size) * 4
                data[index] = x * value
                data[index + 1] = y * value
                data[index + 2] = z * value
    return data


def get_noise_3d(width, height, depth, noise_scale=6):
    def lerp(x, y, t):
        return x * (1.0 - t) + y * t

    def random_3d(uvw, scale) -> float:
        # This is tiling part, adjusts with the scale...
        uvw = mod(uvw, scale)
        return mod(sin(dot(uvw, [12.9898, 78.233, 45.164])) * 43758.5453123, 1.0)

    # This one has non-ideal tiling properties that I'm still tuning
    def noise_3d(uvw, scale) -> float:
        uvw *= scale
        ijk = floor(uvw)
        xyz = mod(uvw, 1.0)
        xyz = xyz * xyz * (3.0 - 2.0 * xyz)

        return lerp(
            lerp(lerp(random_3d(ijk + array([0, 0, 0]), scale), random_3d(ijk + array([1, 0, 0]), scale), xyz[0]),
                 lerp(random_3d(ijk + array([0, 1, 0]), scale), random_3d(ijk + array([1, 1, 0]), scale), xyz[0]),
                 xyz[1]),
            lerp(lerp(random_3d(ijk + array([0, 0, 1]), scale), random_3d(ijk + array([1, 0, 1]), scale), xyz[0]),
                 lerp(random_3d(ijk + array([0, 1, 1]), scale), random_3d(ijk + array([1, 1, 1]), scale), xyz[0]),
                 xyz[1]), xyz[2])

    data = array([0, 0, 0, 0] * width * height * depth, np.uint8)
    for w in range(depth):
        for v in range(height):
            for u in range(width):
                print(u)
                octaves = 50
                persistance = 0.7
                noise_value = 0.0
                weights = 0.0
                amp = 1.0
                scale = noise_scale
                for i in range(octaves):
                    uvw = np.array([u/width, v/height, w/depth])
                    noise_value += amp * noise_3d(uvw, scale)
                    weights += amp
                    amp *= persistance
                    scale *= 2
                noise_value /= weights
                index = (u + v * width + w * width * height) * 4
                data[index] = noise_value
                data[index + 1] = noise_value
                data[index + 2] = noise_value
                data[index + 3] = noise_value
    return data
