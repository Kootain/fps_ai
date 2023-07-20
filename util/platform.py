# coding=utf-8

import sys


def is_mac():
    return sys.platform.startswith('darwin')


def is_windows():
    return sys.platform.startswith('win32')