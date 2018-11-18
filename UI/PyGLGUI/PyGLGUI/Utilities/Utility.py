import time
import sys
import gc
import os
import datetime


class Profiler:
    profile_map = {}
    start_time = 0.0
    section_start_time = 0.0

    @staticmethod
    def start(profile_name=''):
        if profile_name not in Profiler.profile_map:
            Profiler.profile_map[profile_name] = time.perf_counter()
        else:
            print('%s is already exists.' % profile_name)

    @staticmethod
    def end(profile_name=''):
        if profile_name in Profiler.profile_map:
            start_time = Profiler.profile_map.pop(profile_name)
            print('%s : %.2fms' % (profile_name, (time.perf_counter() - start_time) * 1000.0))

    @staticmethod
    def set_stop_watch():
        Profiler.start_time = time.perf_counter()
        Profiler.section_start_time = Profiler.start_time

    @staticmethod
    def get_stop_watch(profile_name=''):
        current_time = time.perf_counter()
        print('%s : %.2fms ( elapsed %.2fms )' % (profile_name,
                                                       (current_time - Profiler.section_start_time) * 1000.0,
                                                       (current_time - Profiler.start_time) * 1000.0))
        Profiler.section_start_time = current_time

    @staticmethod
    def check(func):
        def decoration(*args, **kargs):
            start_time = time.perf_counter()
            result = func(*args, **kargs)
            print('%s : %.2fms' % (func.__name__, (time.perf_counter() - start_time) * 1000.0))
            return result
        return decoration


def GetClassName(cls):
    return cls.__class__.__name__


def is_gz_compressed_file(filename):
    with open(filename,'rb') as f:
        return f.read(3) == b'\x1f\x8b\x08'
    return False


def check_directory_and_mkdir(dirname):
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)


def get_modify_time_of_file(filepath):
    if filepath != "" and os.path.exists(filepath):
        timeStamp = os.path.getmtime(filepath)
        return str(datetime.datetime.fromtimestamp(timeStamp))
    return str(datetime.datetime.min)


def delete_from_referrer(obj):
    """
    desc : Find and remove all references to obj.
    """
    referrers = gc.get_referrers(obj)
    for referrer in referrers:
        if type(referrer) == dict:
            for key, value in referrer.items():
                if value is obj:
                    referrer[key] = None


def object_copy(src, dst):
    dst.__dict__ = src.__dict__

