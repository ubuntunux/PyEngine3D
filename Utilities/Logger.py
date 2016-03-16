#_*_encoding=utf-8_*_
import os
import traceback
import time
import logging
import collections

LOGGER = collections.OrderedDict()

# create and get logger
def getLogger(name='', directory='', savedToFile=False):
    if name in LOGGER:
        return LOGGER[name]
    elif name == '' and len(LOGGER) > 0:
        return LOGGER.values()[0]
    else:
        logObj = createLogger(name, directory, savedToFile)
        LOGGER[name] = logObj
        return logObj


# utility - join text list
def joinTextList(strList):
    return " ".join([str(i) for i in strList])


# noinspection PyBroadException
def createLogger(name, directory, savedToFile):
    # create logger & set level
    newLogger = logging.getLogger(name)
    newLogger.setLevel(logging.DEBUG)

    # formatter
    formatter = logging.Formatter('[%(levelname)-8s|%(asctime)s.%(msecs)03d] %(message)s (%(filename)s:%(lineno)s)',"%Y-%m-%d %H:%M:%S")

    # check log dir
    if directory:
        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
            except:
                print(traceback.format_exc())
                return

    # set file handler
    if savedToFile:
        szTime = "%04d%02d%02d%02d%02d%02d" % (time.localtime()[:6])
        logFilename = os.path.join(directory, szTime + str(int((time.time() % 1.0) * 1000)) + "_" + name + '.log')
        fileHandler = logging.FileHandler(logFilename)
        fileHandler.setFormatter(formatter)
        newLogger.addHandler(fileHandler)
        newLogger.info("Save log file : " + logFilename)

    # set stream handler
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    newLogger.addHandler(streamHandler)
    return newLogger

if __name__ == '__main__':
    testLogger = getLogger(name = 'logTest', directory = 'logtest', savedToFile = True)
    # unit test
    def test_log():
        testLogger.info("TEST START")
        testLogger.warning("Test warning")
        testLogger.error("Test error")
        testLogger.critical("Test critical")
        testLogger.info("TEST END!")
    test_log()