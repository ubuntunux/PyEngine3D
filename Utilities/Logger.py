#_*_encoding=utf-8_*_
import os, traceback, time
import logging
import logging.handlers

class Logger:
    inited = False
    savedToFile = True
    
    def init(self, name='logtest', directory='logs'):
        if self.inited:
            return

        # create logger
        self.logger = logging.getLogger(name)
        # set log level
        self.logger.setLevel(logging.DEBUG)
        self.directory = directory

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
            logFilename = os.path.join(directory, str(int(time.time() * 1000)) + "_" + name + '.log')
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

        self.inited = True

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
        
# create log instance
logger = Logger()
logger.init('logtest', '../logs')
