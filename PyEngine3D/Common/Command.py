import os
import re
import traceback
from multiprocessing import Queue, Pipe

# logger
from PyEngine3D.Utilities import AutoEnum, MINOR_INFO
from PyEngine3D.Common import logger

# UTIL : call stack function for log
reTraceStack = re.compile("File \"(.+?)\", line (\d+?), .+")  # [0] filename, [1] line number


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


# COMMANDS
class COMMAND(AutoEnum):
    UI_RUN = ()
    UI_RUN_OK = ()
    SHOW_UI = ()
    HIDE_UI = ()
    FAIL = ()
    CLOSE_APP = ()
    CLOSE_UI = ()
    RELOAD = ()
    REQUEST_PIPE = ()
    PIPE_DONE = ()

    SORT_UI_ITEMS = ()

    # menu
    NEW_PROJECT = ()
    OPEN_PROJECT = ()
    SAVE_PROJECT = ()

    NEW_SCENE = ()
    SAVE_SCENE = ()

    PLAY = ()
    STOP = ()

    # view mode
    VIEWMODE_WIREFRAME = ()
    VIEWMODE_SHADING = ()

    # Screen
    TRANS_SCREEN_INFO = ()
    CHANGE_RESOLUTION = ()

    # resource
    LOAD_RESOURCE = ()
    ACTION_RESOURCE = ()
    DUPLICATE_RESOURCE = ()
    SAVE_RESOURCE = ()
    DELETE_RESOURCE = ()
    DELETE_RESOURCE_INFO = ()
    REQUEST_RESOURCE_LIST = ()
    TRANS_RESOURCE_LIST = ()
    TRANS_RESOURCE_INFO = ()
    REQUEST_RESOURCE_ATTRIBUTE = ()
    TRANS_RESOURCE_ATTRIBUTE = ()
    SET_RESOURCE_ATTRIBUTE = ()
    ADD_RESOURCE_COMPONENT = ()
    DELETE_RESOURCE_COMPONENT = ()

    # add to scene
    ADD_CAMERA = ()
    ADD_LIGHT = ()

    # create
    CREATE_PARTICLE = ()
    CREATE_COLLISION = ()
    CREATE_SPLINE = ()

    # object
    CLEAR_OBJECT_LIST = ()
    REQUEST_OBJECT_LIST = ()
    TRANS_OBJECT_LIST = ()
    ACTION_OBJECT = ()
    DELETE_OBJECT = ()
    DELETE_OBJECT_INFO = ()
    TRANS_OBJECT_INFO = ()
    REQUEST_OBJECT_ATTRIBUTE = ()
    TRANS_OBJECT_ATTRIBUTE = ()
    SET_OBJECT_ATTRIBUTE = ()
    SET_OBJECT_SELECT = ()
    SET_OBJECT_FOCUS = ()
    ADD_OBJECT_COMPONENT = ()
    DELETE_OBJECT_COMPONENT = ()

    CLEAR_RENDERTARGET_LIST = ()
    TRANS_RENDERTARGET_INFO = ()
    VIEW_RENDERTARGET = ()
    RECREATE_RENDER_TARGETS = ()

    VIEW_TEXTURE = ()

    VIEW_MATERIAL_INSTANCE = ()

    TRANS_ANTIALIASING_LIST = ()
    SET_ANTIALIASING = ()

    TRANS_RENDERING_TYPE_LIST = ()
    SET_RENDERING_TYPE = ()

    TRANS_GAME_BACKEND_INDEX = ()
    TRANS_GAME_BACKEND_LIST = ()
    CHANGE_GAME_BACKEND = ()

    COUNT = ()


def get_command_name(cmd: COMMAND) -> str:
    return str(cmd)


def CustomPipe():
    """get CustomPipe Instances"""
    pipe1, pipe2 = Pipe()
    pipe1 = PipeClass(pipe1)
    pipe2 = PipeClass(pipe2)
    return pipe1, pipe2


class PipeClass:
    """Custom Pipe class"""

    def __init__(self, pipe):
        self.pipe = pipe
        self.simpleLog = True

    def send(self, sendCmd, sendValue=None):
        if self.simpleLog:
            logger.log(MINOR_INFO, "Pipe : Send %s in %s" % (get_command_name(sendCmd), getTraceCallStack()))
        else:
            logger.log(MINOR_INFO,
                       "Pipe : Send %s, %s in %s" % (get_command_name(sendCmd), str(sendValue), getTraceCallStack()))
        # must send queue date to tuple type
        self.pipe.send((sendCmd, sendValue))

    def recv(self):
        """must be a tuple type"""
        cmdAndValue = self.pipe.recv()
        if self.simpleLog:
            logger.log(MINOR_INFO, "Pipe : Recv %s in %s" % (get_command_name(cmdAndValue[0]), getTraceCallStack()))
        else:
            logger.log(MINOR_INFO,
                       "Pipe : Recv %s, %s in %s" % (
                           get_command_name(cmdAndValue[0]), str(cmdAndValue[1]), getTraceCallStack()))
        return cmdAndValue

    def SendAndRecv(self, sendCmd, sendValue, checkRecvCmd, checkReceiveValue):
        # send message - must be a tuple type
        self.pipe.send((sendCmd, sendValue))

        # wait recv message - must be a tuple type
        recv, value = self.pipe.recv()
        if self.simpleLog:
            logger.log(MINOR_INFO, "Pipe : Send %s and Recv %s in %s" % (
                get_command_name(sendCmd), get_command_name(recv), getTraceCallStack()))
        else:
            logger.log(MINOR_INFO, "Pipe : Send %s, %s and Recv %s, %s in %s" % (
                get_command_name(sendCmd), str(sendValue), get_command_name(recv), str(value), getTraceCallStack()))

        # check receive correct command and value
        if recv != checkRecvCmd or (checkReceiveValue is not None and checkReceiveValue != value):
            if self.simpleLog:
                logger.log(MINOR_INFO, "Pipe : RecvFailed %s and Send %s in %s" % (get_command_name(recv),
                                                                                   COMMAND.FAIL, getTraceCallStack()))
            else:
                logger.log(MINOR_INFO, "Pipe : RecvFailed %s, %s and Send %s, %s in %s" % (
                    get_command_name(recv), str(value), COMMAND.FAIL, "None", getTraceCallStack()))
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
                logger.log(MINOR_INFO, "Pipe : Recv %s and Send %s in %s" % (
                    get_command_name(recv), get_command_name(sendCmd), getTraceCallStack()))
            else:
                logger.log(MINOR_INFO, "Pipe : Recv %s, %s and Send %s, %s in %s" % (
                    get_command_name(recv), str(value), get_command_name(sendCmd), str(sendValue), getTraceCallStack()))

            # return received value
            return value
        else:
            self.pipe.send((COMMAND.FAIL, None))
            if self.simpleLog:
                logger.log(MINOR_INFO,
                           "Pipe : RecvFailed %s and Send %s in %s" % (
                               get_command_name(recv), COMMAND.FAIL, getTraceCallStack()))
            else:
                logger.log(MINOR_INFO, "Pipe : RecvFailed %s, %s and Send %s, %s in %s" % (
                    get_command_name(recv), str(value), COMMAND.FAIL, "None", getTraceCallStack()))
            logger.error("ERROR : Received %s not %s" % (recv, checkRecvCmd))
            raise BaseException("Pipe receive error.")


# CLASS : Custom Queue
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
            logger.log(MINOR_INFO, "Queue : get %s in %s" % (get_command_name(cmdAndValue[0]), getTraceCallStack()))
        else:
            logger.log(MINOR_INFO,
                       "Queue : get %s, %s in %s" % (
                           get_command_name(cmdAndValue[0]), str(cmdAndValue[1]), getTraceCallStack()))
        return cmdAndValue

    def put(self, cmdIndex, value=None):
        if self.simpleLog:
            logger.log(MINOR_INFO, "Queue : put %s in %s" % (get_command_name(cmdIndex), getTraceCallStack()))
        else:
            logger.log(MINOR_INFO,
                       "Queue : put %s, %s in %s" % (get_command_name(cmdIndex), str(value), getTraceCallStack()))
        # must send queue date to tuple type
        self.queue.put((cmdIndex, value))
