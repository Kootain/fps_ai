# coding=utf-8
import time

from analyze.vision import filter_target
from vision.eye import frame
from vision.detect import detect, print_results
from util.fps import FPSCounter
from util.region import center_box
import cv2


center = []
fps = FPSCounter()


def draw_fps(img, fps):
    cv2.putText(img, f'{fps}', (20, 40), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 2)


if __name__ == '__main__':

    while True:
        img = frame(box=center_box)
        if img is None:
            continue
        result = detect(img)
        filter_target(result, ['person'])
        print_results(img, result)
        draw_fps(img, fps.fps())

        cv2.imshow('plugin', img)
        fps.frame()
        cv2.waitKey(1)




