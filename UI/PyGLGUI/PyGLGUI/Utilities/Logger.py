import os
import traceback
import time
import logging
from logging import CRITICAL, FATAL, ERROR, WARNING, WARN, INFO, DEBUG, NOTSET
import collections

# add custom log level
MINOR_INFO = DEBUG + 5
logging.addLevelName(MINOR_INFO, "MINOR_INFO")

# global variables
LOGGER = collections.OrderedDict()
# defaultLogPath = os.path.abspath(os.path.abspath(os.getcwd()))
# defaultLogPath = os.path.join(os.path.split(defaultLogPath)[0], "logs")
defaultLogPath = "logs"


def getLevelName(level):
    return logging.getLevelName(level)


def addLevelName(level, levelName):
    logging.addLevelName(level, levelName)


# create and get logger
def getLogger(name='default', directory=defaultLogPath, level=logging.DEBUG):
    if name not in LOGGER:
        LOGGER[name] = createLogger(name, directory, level)
    return LOGGER[name]


# utility - join text list
def joinTextList(strList):
    return " ".join([str(i) for i in strList])


# noinspection PyBroadException
def createLogger(name, directory, level):
    # create logger & set level
    newLogger = logging.getLogger(name)
    newLogger.setLevel(level)

    # formatter - verbose
    formatter = logging.Formatter('[%(levelname)-8s|%(asctime)s.%(msecs)03d] %(message)s (%(filename)s:%(lineno)s)',
                                  "%Y-%m-%d %H:%M:%S")
    # formatter - simple
    # formatter = logging.Formatter('[%(levelname)-8s| %(filename)s:%(lineno)s] %(message)s')

    # check log dir
    if directory:
        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
            except:
                print(traceback.format_exc())
                return

    # set file handler
    # szTime = "%04d%02d%02d%02d%02d%02d" % (time.localtime()[:6])
    # logFilename = os.path.join(directory, szTime + str(int((time.time() % 1.0) * 1000)) + "_" + name + '.log')
    logFilename = os.path.join(directory, name + '.log')

    fileHandler = logging.FileHandler(logFilename, 'w')
    fileHandler.setFormatter(formatter)
    newLogger.addHandler(fileHandler)
    newLogger.info("Save log file : " + logFilename)

    # set stream handler
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    newLogger.addHandler(streamHandler)
    return newLogger


if __name__ == '__main__':
    testLogger = getLogger(name='logTest', directory='logtest', level=logging.DEBUG)

    # unit test
    def test_log():
        testLogger.info("TEST START")
        testLogger.warning("Test warning")
        testLogger.error("Test error")
        testLogger.critical("Test critical")
        testLogger.info("TEST END!")

        CUSTOM_LOG_LEVEL = logging.DEBUG + 1
        addLevelName(CUSTOM_LOG_LEVEL, "CUSTOM_LOG_LEVEL")
        testLogger.log(CUSTOM_LOG_LEVEL, "Custom log level test. %s" % getLevelName(CUSTOM_LOG_LEVEL))

        # level test
        testLogger.setLevel(logging.CRITICAL)
        testLogger.log(CUSTOM_LOG_LEVEL, "Log level test. This message must not display.")

    test_log()