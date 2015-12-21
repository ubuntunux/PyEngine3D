import numpy as np
import unittest
import Logger

class Vector(object):
    def __init__(self, *args):
        self.length = len(args)
        if self.length == 1:
            if type(args[0]) == np.ndarray:
                self._vec = args[0]
            else:
                self._vec = np.array((args[0], args[0], args[0], args[0]))
        elif self.length > 1:
            self._vec = np.array(args)

    def __getitem__(self,index):
        return self._vec[index]

    def __str__(self):
        return str(self._vec)

    def normalize(self):
        norm = np.linalg.norm(self._vec)
        if norm > 0.0:
            return Vector(self._vec / norm)
        else:
            return Vector(np.array((0.0, ) * self.length))

    def dot(self, other):
        return np.dot(self._vec, other._vec)

    def cross(self, other):
        return Vector(np.cross(self._vec, other._vec))

if __name__ == '__main__':
    class test(unittest.TestCase):
        def testVector(self):
            vector = Vector(-1, -2, 3)
            other = Vector(1, 2, 3)
            logger = Logger.getLogger()
            logger.info("Test create vector : ", vector)
            logger.info("Test normalize : ", vector.normalize())
            logger.info("Test dot : ", vector.dot(other))
            logger.info("Test cross : ", vector.cross(other))
            
    unittest.main()