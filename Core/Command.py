def gen_index():
        i = 0
        while True:
            yield i
            i += 1

cmd_index = gen_index()
# CMD_NAME = (next(cmd_index), any datas)
CMD_UI_RUN      = next(cmd_index)
CMD_UI_RUN_OK   = next(cmd_index)
CMD_FAIL        = next(cmd_index)
CMD_CLOSE_APP   = next(cmd_index)
CMD_CLOSE_UI    = next(cmd_index)
CMD_REQUEST_PIPE = next(cmd_index)
CMD_PIPE_DONE   = next(cmd_index)

# add primitive
CMD_ADD_PRIMITIVE_START = next(cmd_index)
CMD_ADD_TRIANGLE        = next(cmd_index)
CMD_ADD_QUAD            = next(cmd_index)
CMD_ADD_CUBE            = next(cmd_index)
CMD_ADD_PRIMITIVE_END   = next(cmd_index)
CMD_SEND_PRIMITIVENAME  = next(cmd_index)
CMD_REQUEST_PRIMITIVEINFOS = next(cmd_index)
CMD_SEND_PRIMITIVEINFOS = next(cmd_index)
CMD_SET_PRIMITIVEINFO = next(cmd_index)

CMD_OBJECT_MOVE = next(cmd_index)

def Error():
    raise "Receive wrong command."


def PipeSendRecv(pipe, sendCmd, recvCmd):
    if pipe:
        # send message
        pipe.send(sendCmd)
        # wait recv message, and check
        recv = pipe.recv()
        # check type
        if type(recv) is tuple:
            recv, value = recv
        else:
            value = None
        if recv != recvCmd:
            print("Received %s not %s" % (recv, recvCmd))
            raise "Pipe receive error."
        return value


def PipeRecvSend(pipe, recvCmd, sendCmd):
    if pipe:
        # wait recv message, and check
        recv = pipe.recv()
        if recv == recvCmd:
            # succesfull - send message
            pipe.send(sendCmd)
        else:
            pipe.send(CMD_FAIL)
            raise "Received %s not %s" % (recv, recvCmd)

