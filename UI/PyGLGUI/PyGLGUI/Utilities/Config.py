import os
import configparser
import traceback

from . import Logger


# util class
class Empty:
    pass


def evaluation(value):
    # find value type
    try:
        evalValue = eval(value)
        if type(evalValue) in [int, float, list, tuple, dict]:
            return evalValue
    except:
        return value


def getValue(config, section, option, default_value=None):
    return evaluation(config[section][option]) if config.has_option(section, option) else default_value


def setValue(config, section, option, value):
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, option, value)


# ------------------------------ #
# CLASS : Configure
# Usage :
#   config = Configure()
#   # get value example, section:Screen, option:wdith
#   print(config.Screen.width)
# ------------------------------ #
class Config:
    def __init__(self, configFilename, log_level=Logger.WARN, prevent_lowercase=True):
        self.log_level = log_level
        self.isChanged = False
        self.filename = configFilename
        self.config = configparser.ConfigParser()
        self.config.read(configFilename)
        # prevent the key value being lowercase
        if prevent_lowercase:
            self.config.optionxform = lambda option_name: option_name
        if self.log_level <= Logger.INFO:
            print("Load Config : %s" % self.filename)

        # set sections
        for section in self.config.sections():
            if self.log_level == Logger.DEBUG:
                print("[%s]" % section)
            if not hasattr(self, section):
                setattr(self, section, Empty())
            # set value to member variables
            current_section = getattr(self, section)
            for option in self.config[section]:
                value = self.config.get(section, option)
                if self.log_level == Logger.DEBUG:
                    print("%s = %s" % (option, value))
                setattr(current_section, option, evaluation(value))

    def hasValue(self, section, option):
        return self.config.has_option(section, option)

    def getValue(self, section, option, default_value=None):
        return evaluation(self.config[section][option]) if self.config.has_option(section, option) else default_value

    def setValue(self, section, option, value):
        # set value
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config[section][option] = str(value)

        # set value to member variables
        if not hasattr(self, section):
            setattr(self, section, Empty())
            self.isChanged = True
        elif not self.isChanged:
            self.isChanged = value != getattr(self, section)
        current_section = getattr(self, section)
        setattr(current_section, option, value)

    def setDefaultValue(self, section, option, value):
        if not self.hasValue(section, option):
            self.setValue(section, option, value)

    def save(self):
        if self.isChanged or not os.path.exists(self.filename):
            with open(self.filename, 'w') as configfile:
                self.config.write(configfile)
                if self.log_level <= Logger.INFO:
                    print("Saved Config : " + self.filename)
        self.isChanged = False

    def getFilename(self):
        return self.filename


if __name__ == '__main__':
    import unittest


    class test(unittest.TestCase):
        def testConfig(self):
            # load test
            testConfig = Config("TestConfig.ini", debug=False)

            # set value
            testConfig.setValue("TestSection", "test_int", 45)
            testConfig.setValue("TestSection", "test_float", 0.1)
            testConfig.setValue("TestSection", "test_string", "Hello, World")
            testConfig.setValue("TestSection", "test_list", [1, 2, 3])
            testConfig.setValue("TestSection", "test_tuple", (4, 5, 6))
            testConfig.setValue("TestSection", "test_dict", {"x":7.0, "y":8.0})

            # call test
            self.assertEqual(testConfig.TestSection.test_int, 45)
            self.assertEqual(testConfig.TestSection.test_float, 0.1)
            self.assertEqual(testConfig.TestSection.test_string, "Hello, World")
            self.assertEqual(testConfig.TestSection.test_list, [1, 2, 3])
            self.assertEqual(testConfig.TestSection.test_tuple, (4, 5, 6))
            self.assertEqual(testConfig.TestSection.test_dict['x'], 7.0)
            self.assertEqual(testConfig.TestSection.test_dict['y'], 8.0)

            # set value test
            testConfig.setValue("TestSection", "test_int", 99)
            self.assertEqual(testConfig.TestSection.test_int, 99)

            testConfig.save()
    unittest.main()


