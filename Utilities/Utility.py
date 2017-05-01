import os
import datetime


def GetClassName(cls):
    return cls.__class__.__name__


def is_gz_file(filename):
    with open(filename,'rb') as f:
        return f.read(3) == b'\x1f\x8b\x08'
    return False


def check_directory_and_mkdir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def get_modify_time_of_file(filepath):
    timeStamp = 0.0
    if filepath != "" and os.path.exists(filepath):
        timeStamp = os.path.getmtime(filepath)
    return str(datetime.datetime.fromtimestamp(timeStamp))