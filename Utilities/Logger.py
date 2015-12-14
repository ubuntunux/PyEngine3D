#_*_encoding=utf-8_*_
import os, traceback, time
import logging
import logging.handlers

class Logger:    
    def init(self, name='logtest', directory='logs', showTime=True):
        # create logger
        self.logger = logging.getLogger(name)
        self.directory = directory

        # formatter
        formatter = None
        if showTime:
            formatter = logging.Formatter('[%(levelname)-8s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s',"%Y-%m-%d %H:%M:%S")
        else:
            formatter = logging.Formatter('[%(levelname)-8s|%(filename)s:%(lineno)s] > %(message)s')

        # check log dir
        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
            except:
                print traceback.format_exc()
                return

        # create handler
        logFilename = os.path.join(directory, str(int(time.time() * 1000)) + "_" + name + '.log')
        fileHandler = logging.FileHandler(logFilename)
        streamHandler = logging.StreamHandler()

        # binding formatter
        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(formatter)

        # binding handler
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)
        
        # set log level
        self.logger.setLevel(logging.DEBUG)
        
        # test
        self.info("Save log file :", logFilename)
        self.test_logs()

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

# test
if __name__ == '__main__':    
    logger.init('logtest', '../logs', False)
