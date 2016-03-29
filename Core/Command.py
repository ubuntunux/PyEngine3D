def gen_index():
        i = 0
        while True:
            yield i
            i += 1

class CMD:
    cmd_index = gen_index()
    # arguments
    # CMD_NAME = (next(cmd_index), any datas)
    UI_RUN      = next(cmd_index)
    UI_RUN_OK   = next(cmd_index)
    FAIL        = next(cmd_index)
    CLOSE_APP   = next(cmd_index)
    CLOSE_UI    = next(cmd_index)

    @staticmethod
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
        pipe.send(CMD.FAIL)
        raise "Received %s not %s" % (recv, recvCmd)

