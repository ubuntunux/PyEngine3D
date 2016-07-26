import os
import re
import traceback
from multiprocessing import Queue, Pipe

# logger
from Utilities import Logger
logger = Logger.getLogger('Command Logger', 'logs', False)


#------------------------------------#
# UTIL : call stack function for log
#------------------------------------#
reTraceStack = re.compile("File \"(.+?)\", line (\d+?), .+") # [0] filename, [1] line number

def getTraceCallStack():
    for line in traceback.format_stack()[::-1]:
        m = re.match(reTraceStack, line.strip())
        if m:
            filename = m.groups()[0]
            # ignore case
            if filename == __file__:
                continue
            filename = os.path.split(filename)[1]
            lineNumber = m.groups()[1]
            return "[%s:%s]" % (filename, lineNumber)
    return ""


#---------------------#
# FUNCTION : Error
#---------------------#
def Error():
    raise "Receive wrong command."

#---------------------#
# COMMANDS
#---------------------#
CMD_NAMES = []

# command index coroutine
def genCommandIndex():
        i = -1
        while True:
            cmdName = yield i # return index and receive
            CMD_NAMES.append(cmdName)
            i += 1

def getCommandName(command_index):
    return CMD_NAMES[command_index] if len(CMD_NAMES) > command_index else "getCommandName error - index out of range."


cmd_index = genCommandIndex()
# just first run coroutine
next(cmd_index)

CMD_UI_RUN      = cmd_index.send("CMD_UI_RUN")
CMD_UI_RUN_OK   = cmd_index.send("CMD_UI_RUN_OK")
CMD_FAIL        = cmd_index.send("CMD_FAIL")
CMD_CLOSE_APP   = cmd_index.send("CMD_CLOSE_APP")
CMD_CLOSE_UI    = cmd_index.send("CMD_CLOSE_UI")
CMD_REQUEST_PIPE = cmd_index.send("CMD_REQUEST_PIPE")
CMD_PIPE_DONE   = cmd_index.send("CMD_PIPE_DONE")

# view mode
CMD_VIEWMODE_WIREFRAME = cmd_index.send("CMD_VIEWMODE_WIREFRAME")
CMD_VIEWMODE_SHADING = cmd_index.send("CMD_VIEWMODE_SHADING")

# add object
CMD_ADD_MESH = cmd_index.send("CMD_ADD_MESH")
CMD_REQUEST_MESH_LIST = cmd_index.send("CMD_REQUEST_MESH_LIST")
CMD_SEND_MESH_LIST = cmd_index.send("CMD_SEND_MESH_LIST")
CMD_SEND_OBJECT_NAME  = cmd_index.send("CMD_SEND_OBJECT_NAME")
CMD_REQUEST_OBJECT_INFOS = cmd_index.send("CMD_REQUEST_OBJECT_INFOS")
CMD_SEND_OBJECT_INFOS = cmd_index.send("CMD_SEND_OBJECT_INFOS")
CMD_SET_OBJECT_INFO = cmd_index.send("CMD_SET_OBJECT_INFO")
CMD_SET_OBJECT_SELECT = cmd_index.send("CMD_SET_OBJECT_SELECT")
CMD_SET_OBJECT_FOCUS = cmd_index.send("CMD_SET_OBJECT_FOCUS")

#---------------------#
# CLASS : CustomPipe
#---------------------#
def CustomPipe():
    pipe1, pipe2 = Pipe()
    pipe1 = PipeClass(pipe1)
    pipe2 = PipeClass(pipe2)
    return pipe1, pipe2

class PipeClass:
    def __init__(self, pipe):
        self.pipe = pipe
        self.simpleLog = True

    def send(self, sendCmd, sendValue=None):
        if self.simpleLog:
            logger.info("Pipe : Send %s in %s" % (getCommandName(sendCmd), getTraceCallStack()))
        else:
            logger.info("Pipe : Send %s, %s in %s" % (getCommandName(sendCmd), str(sendValue), getTraceCallStack()))
        # must send queue date to tuple type
        self.pipe.send((sendCmd, sendValue))

    def recv(self):
        # must be a tuple type
        cmdAndValue = self.pipe.recv()
        if self.simpleLog:
            logger.info("Pipe : Recv %s in %s" % (getCommandName(cmdAndValue[0]), getTraceCallStack()))
        else:
            logger.info("Pipe : Recv %s, %s in %s" % (getCommandName(cmdAndValue[0]), str(cmdAndValue[1]), getTraceCallStack()))
        return cmdAndValue

    def SendAndRecv(self, sendCmd, sendValue, checkRecvCmd, checkReceiveValue):
        # send message - must be a tuple type
        self.pipe.send((sendCmd, sendValue))

        # wait recv message - must be a tuple type
        recv, value = self.pipe.recv()
        if self.simpleLog:
            logger.info("Pipe : Send %s and Recv %s in %s" % (getCommandName(sendCmd), getCommandName(recv), getTraceCallStack()))
        else:
            logger.info("Pipe : Send %s, %s and Recv %s, %s in %s" % (getCommandName(sendCmd), str(sendValue), getCommandName(recv), str(value), getTraceCallStack()))

        # check receive correct command and value
        if recv != checkRecvCmd or (checkReceiveValue is not None and checkReceiveValue != value):
            if self.simpleLog:
                logger.info("Pipe : RecvFailed %s and Send %s in %s" % (getCommandName(recv), CMD_FAIL, getTraceCallStack()))
            else:
                logger.info("Pipe : RecvFailed %s, %s and Send %s, %s in %s" % (getCommandName(recv), str(value), CMD_FAIL, "None", getTraceCallStack()))
            logger.error("ERROR : Received %s not %s" % (recv, checkRecvCmd))
            raise BaseException("Pipe receive error.")
        return value

    def RecvAndSend(self, checkRecvCmd, checkReceiveValue, sendCmd, sendValue):
        # wait recv message - must be a tuple type
        recv, value = self.pipe.recv()

        if recv == checkRecvCmd and (checkReceiveValue is None or checkReceiveValue == value):
            # receive succesfull - send message, must be a tuple type
            self.pipe.send((sendCmd, sendValue))
            if self.simpleLog:
                logger.info("Pipe : Recv %s and Send %s in %s" % (getCommandName(recv), getCommandName(sendCmd), getTraceCallStack()))
            else:
                logger.info("Pipe : Recv %s, %s and Send %s, %s in %s" % (getCommandName(recv), str(value), getCommandName(sendCmd), str(sendValue), getTraceCallStack()))

            # return received value
            return value
        else:
            self.pipe.send((CMD_FAIL,None))
            if self.simpleLog:
                logger.info("Pipe : RecvFailed %s and Send %s in %s" % (getCommandName(recv), CMD_FAIL, getTraceCallStack()))
            else:
                logger.info("Pipe : RecvFailed %s, %s and Send %s, %s in %s" % (getCommandName(recv), str(value), CMD_FAIL, "None", getTraceCallStack()))
            logger.error("ERROR : Received %s not %s" % (recv, checkRecvCmd))
            raise BaseException("Pipe receive error.")


#---------------------#
# CLASS : CustomQueue
#---------------------#
class CustomQueue:
    def __init__(self):
        self.queue = Queue()
        self.simpleLog = True

    def empty(self):
        return self.queue.empty()

    def get(self):
        # receive value must be tuple type
        cmdAndValue = self.queue.get(self)
        if self.simpleLog:
            logger.info("Queue : get %s in %s" % (getCommandName(cmdAndValue[0]), getTraceCallStack()))
        else:
            logger.info("Queue : get %s, %s in %s" % (getCommandName(cmdAndValue[0]), str(cmdAndValue[1]), getTraceCallStack()))
        return cmdAndValue

    def put(self, cmdIndex, value=None):
        if self.simpleLog:
            logger.info("Queue : put %s in %s" % (getCommandName(cmdIndex), getTraceCallStack()))
        else:
            logger.info("Queue : put %s, %s in %s" % (getCommandName(cmdIndex), str(value), getTraceCallStack()))
        # must send queue date to tuple type
        self.queue.put((cmdIndex, value))