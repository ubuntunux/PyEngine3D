#_*_encoding=utf-8_*_
import os, traceback, time
import logging
import logging.handlers

LOGGER = {}

def getLogger(name = 'logTest', directory = '.', savedToFile = True):
    if name in LOGGER:
        return LOGGER[name]
    else:
        return Logger(name, directory, savedToFile)

class Logger:
<<<<<<< HEAD
    inited = False
    savedToFile = True
    
    def init(self, name='logtest', directory='logs'):
        if self.inited:
            return
=======
    name = None
    directory = None
    savedToFile = False
>>>>>>> 08847ff18009ff34e6be517418014b33bc683f40

    def __init__(self, name, directory, savedToFile):
        '''
        usage : name = 'logtest', directory = 'logs', savedToFile = False
        '''
        self.name = name
        self.directory = directory
        self.savedToFile = savedToFile

        # create logger & set level
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # formatter
        formatter = logging.Formatter('[%(levelname)-8s|%(filename)s:%(lineno)s] %(asctime)s.%(msecs)03d > %(message)s',"%Y-%m-%d %H:%M:%S")

        # check log dir
        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
            except:
                print traceback.format_exc()
                return

        # set file handler
        if self.savedToFile:
            szTime = "%04d%02d%02d%02d%02d%02d" % (time.localtime()[:6])
            logFilename = os.path.join(directory, szTime + str(int((time.time() % 1.0) * 1000)) + "_" + name + '.log')
            fileHandler = logging.FileHandler(logFilename)
            fileHandler.setFormatter(formatter)
            self.logger.addHandler(fileHandler)
            self.info("Save log file :", logFilename)        
        
        # set stream handler
        streamHandler = logging.StreamHandler()        
        streamHandler.setFormatter(formatter)
        self.logger.addHandler(streamHandler)
        
        # test        
        #self.test_logs()

    def test_logs(self):
        self.info("TEST START")
        self.warning("Test warning")
        self.error("Test error")
        self.critical("Test critical")
        self.info("TEST END!")
        
    # log function
    def joinTextList(self, strList):
        try:
            return " ".join([str(i) for i in strList])
        except:
            print traceback,format_exc()
    
    def info(self, *args):
        self.logger.info(self.joinTextList(args))

    def warning(self, *args):
        self.logger.info(self.joinTextList(args))

    def error(self, *args):
        self.logger.info(self.joinTextList(args))
        
    def critical(self, *args):
        self.logger.info(self.joinTextList(args))

if __name__ == '__main__':
    logger = getLogger()
    logger.test_logs()