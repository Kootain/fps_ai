# coding=utf-8
import torch
from ultralytics import YOLO
from ultralytics.engine.results import Results, Keypoints
from typing import List, Optional, Union
import cv2
from torch import Tensor
from queue import Full, Empty
from multiprocessing import Queue, Process, Event
from abc import ABC, abstractmethod
import time
from util.utils import cts


def mark_test(image, results):
    image = results.plot()
    for points in results.keypoints.xy:
        for i in range(len(points)):
            point = points[i]
            cv2.putText(image, str(i), (int(point[0]), int(point[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.imshow('test', image)
    cv2.waitKey(0)


class YoloPose(object):
    yolo_pose_config = {
        'nose': [0],
        'eyes': [1, 2],
        'ears': [3, 4],
        'shoulders': [5, 6],
        'elbows': [7, 8],
        'wrists': [9, 10],
        'crotches': [11, 12],
        'knees': [13, 14],
        'feet': [15, 16]
    }

    def __init__(self, results):
        self.data: Tensor = results[0].keypoints.data

    def size(self):
        return self.data.shape[0]

    def target(self, i: int):
        return self.data[i]

    def target_obj(self, i: int, obj_name: str):
        idxs = self.yolo_pose_config.get(obj_name)
        if not idxs:
            raise ValueError(f'unknown body part {obj_name}')
        try:
            return [self.data[i][j] for j in idxs]
        except:
            return None


def yolo2pose(keypoints: Keypoints) -> torch.Tensor:
    return keypoints.data


class FrameAwareable(ABC):
    @abstractmethod
    def tik(self, ts):
        pass


class FrameLooper(ABC):
    @abstractmethod
    def tikloop_start(self):
        pass

    def tikloop_stop(self):
        pass


# 非阻塞 tiker, 自己有缓冲池，缓冲池如果写满了 不阻塞tik，直接丢弃
class BaseTiker(FrameAwareable, FrameLooper, ABC):
    def __init__(self, size=1):
        self.q = Queue(maxsize=size)
        self.p: Optional[Process] = None
        self.stop: Optional[Event] = None

    @abstractmethod
    def do(self, ts):
        pass

    @abstractmethod
    def init(self):
        pass

    def tik(self, ts):
        try:
            self.q.put(ts, block=False)
        except Full:
            self._replace_in_queue(ts)

    def _replace_in_queue(self, ts):
        try:
            self.q.get(block=False)
            self.q.put(ts, block=False)
        except Empty:
            try:
                self.q.put(ts, block=False)
            except Full:
                # queue.get(block=False) 在队列不空的时候也会raise Full exception 绝了
                pass
        except Full:
            raise Exception('shouldn\'t happened, unless other thread/process write self.q')

    def do_wrapper(self, q: Queue, stop: Event):
        while not stop.is_set():
            ts = q.get()
            self.do(ts)

    def tikloop_stop(self):
        self.stop.set()
        self.p.close()

    def tikloop_start(self):
        self.q.empty()
        self.stop = Event()
        self.p = Process(target=self.do_wrapper, args=(self.q, self.stop))
        self.p.start()


# 核心逻辑钟，所有感知帧变化的组件都要注册在 Quartz 上，由 Quartz 在触发
class Quartz(object):
    def __init__(self, fps=1000):
        self.fps = fps
        self._listener: List[Union[FrameAwareable, FrameLooper]] = []
        self.status = False

    def register(self, obj: Union[FrameAwareable, FrameLooper]):
        assert issubclass(obj.__class__, FrameAwareable)
        assert issubclass(obj.__class__, FrameLooper)
        self._listener.append(obj)

    def start(self):
        self.status = True
        for l in self._listener:
            l.tikloop_start()

        while self.status:
            now = cts()
            for l in self._listener:
                l.tik(now)
            time.sleep(1 / self.fps)


class PoseDetectJob(BaseTiker):
    def do(self, event):
        self.run(event.data)

    yoloV8: Optional[YOLO] = None
    yoloV8Pose: Optional[YOLO] = None

    def init_pose(self):
        if self.yoloV8Pose is None:
            self.yoloV8Pose = YOLO('../yolov8n-pose.pt')

    def init(self):
        if self.yoloV8 is None:
            self.yoloV8 = YOLO('../yolov8n.pt')

    def run(self, img):
        results: Results = self.yoloV8Pose(img)
        image = results[0].plot()
        cv2.imshow('test', image)
        cv2.waitKey(1)
        return results
