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

# add primitive
CMD_ADD_TRIANGLE = next(cmd_index)
CMD_ADD_QUAD     = next(cmd_index)

def Error():
    raise "Receive wrong command."


def PipeSendRecv(pipe, sendCmd, recvCmd):
    # send message
    pipe.send(sendCmd)
    # wait recv message, and check
    recv = pipe.recv()
    if recv != recvCmd:
        raise "Received %s not %s" % (recv, recvCmd)


def PipeRecvSend(pipe, recvCmd, sendCmd):
    # wait recv message, and check
    recv = pipe.recv()
    if recv == recvCmd:
        # succesfull - send message
        pipe.send(sendCmd)
    else:
        pipe.send(CMD_FAIL)
        raise "Received %s not %s" % (recv, recvCmd)

