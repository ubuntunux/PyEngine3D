#_*_encoding=utf-8_*_
import os, traceback, unittest, time
import logging
import logging.handlers

class Logger(unittest.TestCase):
    def __init__(self, name='logtest', showTime=True):
	# create logger
        self.logger = logging.getLogger(name)

        # formatter
        formatter = None
        if showTime:
            formatter = logging.Formatter('[%(levelname)-8s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s',"%Y-%m-%d %H:%M:%S")
        else:
            formatter = logging.Formatter('[%(levelname)-8s|%(filename)s:%(lineno)s] > %(message)s')

        # check log dir
        if not os.path.exists('logs'):
            try:
                os.mkdir('logs')
            except:
                print traceback.format_exc()
                return

        # create handler
        fileHandler = logging.FileHandler('./logs/' + str(time.ctime()) + "_" + name + '.log')
        streamHandler = logging.StreamHandler()

        # binding formatter
        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(formatter)

        # binding handler
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)
        
        # set log level
        self.logger.setLevel(logging.DEBUG)
        
        # do test
        self.test()

    def test(self):
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
logger = Logger('logtest', False)
