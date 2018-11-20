# method type
class Singleton:
    __instance = None

    @classmethod
    def __getInstance(cls):
        return cls.__instance

    @classmethod
    def getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__getInstance
        return cls.__instance


if __name__ == '__main__':
    # base class type singleton
    class TestClass_1(Singleton):
        pass

    import unittest

    class TestStringMethods(unittest.TestCase):
        def test_singleton(self):
            c1_1 = TestClass_1.instance()
            c1_2 = TestClass_1.instance()

            self.assertEqual(c1_1, c1_2)

    unittest.main()