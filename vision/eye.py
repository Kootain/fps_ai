import time
import sys
from typing import Tuple
from util.platform import is_mac, is_windows
from util.region import Box


def frame(box: Box = None):
    raise Exception('unknown platform')


def mac_frame(box: Box = None):
    with mss() as sct:
        img = np.array(sct.grab(box.rect().tuple()))[:, :, :3]
        return np.ascontiguousarray(img)


def windows_frame(box: Box = None):
    return camera.grab(region=box.tuple())


if is_windows():
    import dxcam

    camera = dxcam.create(output_color="BGR")
    frame = windows_frame

if is_mac():
    from mss import mss
    import numpy as np

    frame = mac_frame

if __name__ == '__main__':
    import cv2
    from util.region import center_box

    while True:
        img = frame(center_box)
        if img is None:
            continue
        print(type(img))
        cv2.imshow('test', img)
        cv2.waitKey(1)
