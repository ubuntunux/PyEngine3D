import numpy as np
import unittest
from Utilities import Logger


class Vector(object):
    def __init__(self, *args):
        self.length = len(args)
        self._vec = np.array(args)

    def __getitem__(self, index):
        return self._vec[index]

    def __setitem__(self, key, value):
        self._vec[key] = value

    def __mul__(self, other):
        return Vector()

    def __str__(self):
        return str(self._vec)

    def __add__(self, other):return self._vec + other._vec
    def __iadd__(self, other):return self._vec + other._vec
    def __sub__(self, other):return self._vec - other._vec
    def __isub__(self, other):return self._vec - other._vec
    def __mul__(self, other):return self._vec * other._vec
    def __imul__(self, other):return self._vec * other._vec
    def __idiv__(self, other):return self._vec / other._vec
    def __floordiv__(self, other):return self._vec / other._vec

    def norm(self):
        return np.linalg.norm(self._vec)

    def normalize(self):
        norm = np.linalg.norm(self._vec)
        if norm > 0.0:
            return Vector(*self._vec / norm)
        else:
            return Vector(*((0.0, ) * self.length))

    def dot(self, other):
        return np.dot(self._vec, other._vec)

    def cross(self, other):
        return Vector(*np.cross(self._vec, other._vec))

if __name__ == '__main__':
    class test(unittest.TestCase):
        def testVector(self):
            vector = Vector(-1, -2, 3.5)
            other = Vector(1, 2, 3)
            logger = Logger.getLogger()
            logger.info("Test create vector : %s" % vector)
            logger.info("Test normalize : %s" % vector.normalize())
            logger.info("Test dot : %s" % vector.dot(other))
            logger.info("Test cross : %s" % vector.cross(other))
    unittest.main()