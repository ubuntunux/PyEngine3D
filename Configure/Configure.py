import os
import configparser

# util class
class Empty:
    pass

def getValue(value):
    # find value type
    try:
        evalValue = eval(value)
        if type(evalValue) in [int, float, list, tuple, dict]:
            return evalValue
    except NameError:
        pass
    return value

#------------------------------#
# CLASS : Configure
# Usage :
#   config = Configure()
#   # get value example, section:Screen, option:wdith
#   print(config.Screen.width)
#------------------------------#
class Config:
    def __init__(self, configFilename, debug = False):
        self.debug = debug
        self.filename = os.path.join(os.path.split(__file__)[0], configFilename)
        self.config = configparser.ConfigParser()
        self.config.read(self.filename)
        print("Load Config : %s" % self.filename)

        # set sections
        for section in self.config.sections():
            if self.debug:
                print("[%s]" % section)
            if not hasattr(self, section):
                setattr(self, section, Empty())
            current_section = getattr(self, section)
            # set values
            for option in self.config[section]:
                value = self.config.get(section, option)
                if self.debug:
                    print("%s = %s" % (option, value))
                setattr(current_section, option, getValue(value))

    def getValue(self, section, option):
        return getValue(self.config[section][option])

    def setValue(self, section, option, value):
        # set value
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config[section][option] = str(value)

        # set internal method
        if not hasattr(self, section):
            setattr(self, section, Empty())
        current_section = getattr(self, section)
        setattr(current_section, option, value)

    def save(self):
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)
            print("Saved Config : " + self.filename)

if __name__ == '__main__':
    import unittest

    # force write TestConfig.ini
    f = open(os.path.join(os.path.split(__file__)[0], "TestConfig.ini"), "w")
    f.writelines('''[TestSection]
test_int = 45
test_float = 0.1
test_string = Hello, World
test_list = [1, 2, 3]
test_tuple = (1, 2, 3)
test_dict = {"x":1.0, "y":2.0}
''')
    f.close()

    # test
    class test(unittest.TestCase):
        def testConfig(self):
            # load test
            testConfig = Config("TestConfig.ini", debug=False)
            # call test
            self.assertEqual(testConfig.TestSection.test_int, 45)
            self.assertEqual(testConfig.TestSection.test_float, 0.1)
            self.assertEqual(testConfig.TestSection.test_string, "Hello, World")
            self.assertEqual(testConfig.TestSection.test_list, [1, 2, 3])
            self.assertEqual(testConfig.TestSection.test_tuple, (1, 2, 3))
            self.assertEqual(testConfig.TestSection.test_dict['x'], 1.0)
            self.assertEqual(testConfig.TestSection.test_dict['y'], 2.0)
            # set value test
            testConfig.setValue("TestSection", "test_int", 99)
            self.assertEqual(testConfig.TestSection.test_int, 99)
            testConfig.save()
    unittest.main()


