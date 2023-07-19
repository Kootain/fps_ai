# coding=-utf-8
import queue
import time


class FPSCounter(object):
    def __init__(self):
        self._qsize = 10000
        self._cur = 0
        self._q = [time.time()] * self._qsize
        self._init_cnt = 0

    def frame(self):
        self._q[self._cur] = time.time()
        self._cur += 1
        if self._cur >= self._qsize:
            self._cur = 0
        if self._init_cnt <= self._qsize:
            self._init_cnt += 1

    def fps(self):
        start = self._cur - 1
        if self._cur == 0:
            start = self._qsize - 1
        d = (self._q[start] - self._q[self._cur])
        if d == 0:
            return 0
        if self._init_cnt <= self._qsize:
            return self._init_cnt / d
        return self._qsize / d


if __name__ == '__main__':
    fps = FPSCounter()

    while True:
        fps.frame()
        print(fps.fps())
