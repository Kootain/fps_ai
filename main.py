# coding=utf-8
import time

from analyze.vision import filter_target
from vision.eye import frame
from vision.detect import detect, print_results
from util.fps import FPSCounter
from util.region import center_box, Box
from util.printer import draw
import cv2


center = []
fps = FPSCounter()


def draw_fps(img, fps):
    cv2.putText(img, f'{fps}', (20, 40), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 2)


def results2boxes(results, phrase:Box):
    r = results[0]
    boxes = r.boxes
    b = []
    if boxes is not None:
        for d in reversed(boxes):
            x1, y1, x2, y2 = (int(x) for x in d.xyxy.squeeze())
            b.append(Box(x1+phrase.topx, y1+phrase.topy, x2+phrase.topx, y2+phrase.topy ))

    return b


if __name__ == '__main__':
    from multiprocessing import Queue, Process
    q = Queue()
    p = Process(target=draw, args=(q,))
    p.start()

    while True:

        img = frame(box=center_box)
        if img is None:
            continue
        result = detect(img)
        filter_target(result, ['person'])
        boxes = results2boxes(result, center_box)
        q.put(boxes)
        # print_results(img, result)
        # draw_fps(img, fps.fps())
        # cv2.imshow('plugin', img)
        # cv2.waitKey(1)
        fps.frame()




