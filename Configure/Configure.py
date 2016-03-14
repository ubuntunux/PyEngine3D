import os
import configparser

from Core import logger
from Utilities import Singleton

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
class Configure(Singleton):
    debug = False
    localFile = os.path.join(os.path.split(__file__)[0], "Config.ini")
    defaultFile = os.path.join(os.path.split(__file__)[0], "DefaultConfig.ini")

    def __init__(self):
        filename = self.localFile if os.path.exists(self.localFile) else self.defaultFile
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        logger.info("Load Config : %s" % filename)

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

    def close(self):
        with open(self.localFile, 'w') as configfile:
            self.config.write(configfile)
            logger.info("Saved Config : " + self.localFile)


# Global variable
config = Configure()