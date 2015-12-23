# noinspection PyArgumentList
class Singleton(object):
    """
    general singleton design pattern
    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

def decoratorSingleton(cls):
    """
    decorator singleton pattern
    """
    instances = {}
    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance

if __name__ == '__main__':
    # base class type singleton
    class TestClass_1(Singleton):
        pass

    # decorator type singleton
    @decoratorSingleton
    class TestClass_2:
      pass

    import unittest
    class TestStringMethods(unittest.TestCase):
        def test_singleton(self):
            c1_1 = TestClass_1()
            c1_2 = TestClass_1()
            c2_1 = TestClass_2()
            c2_2 = TestClass_2()

            self.assertEqual(c1_1, c1_2)
            self.assertEqual(c2_1, c2_2)

    unittest.main()