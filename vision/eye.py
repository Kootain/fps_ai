import dxcam
import time
from typing import Tuple

camera = dxcam.create(output_color="BGR")


def frame(region: Tuple[int, int, int, int] = None):
    return camera.grab(region=region)


if __name__ == '__main__':
    import cv2
    screen_width, screen_height = 2560, 1440
    grab_width, grab_height = 640, 640
    grab_rectangle = (int(screen_width / 2 - grab_width / 2), int(screen_height / 2 - grab_height / 2),
                      int(screen_width / 2 + grab_width / 2), int(screen_height / 2 + grab_height / 2))
    img = frame(region=grab_rectangle)
    cv2.imshow('test', img)
    cv2.waitKey(0)
