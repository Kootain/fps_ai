# coding=utf-8

from util.platform import is_mac, is_windows
from util.region import Box

if is_mac():
    from mss import mss
    import numpy as np
if is_windows():
    import dxcam
from ..input import Input
from typing import Optional, Any


class ScreenInput(Input):

    def __init__(self, fps: int, region: Optional[Box] = None):
        super().__init__(fps)
        self.region = region

    if is_windows():
        win_camera = dxcam.create(output_color="BGR")

        @classmethod
        def frame(cls, region: Optional[Box] = None):
            if region:
                return cls.win_camera.grab(region=region.tuple())
            return cls.win_camera.grab()

    if is_mac():
        mac_camera = mss()

        @classmethod
        def frame(cls, region: Optional[Box] = None):
            if region:
                img = np.array(cls.mac_camera.grab(region.rect().tuple()))[:, :, :3]
                return np.ascontiguousarray(img)

    def pull_input_param(self) -> Optional[Box]:
        return self.region

    @classmethod
    def pull_input(cls, param: Optional[Box]) -> Any:
        return cls.frame(param)

    def on(self):
        pass

    def off(self):
        pass

    def close(self):
        super().close()
        if is_windows():
            self.win_camera.release()

        if is_mac():
            self.mac_camera.close()


class ScreenOutput(object):
    pass
