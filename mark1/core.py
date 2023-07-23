# coding = utf-8
import time
from abc import ABC, abstractmethod
from multiprocessing import Queue, Process, Event
from queue import Full, Empty
from typing import List, Optional, Union

from util.utils import cts


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


class Memory(BaseTiker):

    def do(self, ts):
        print(cts() - ts)
        self.tmp = ts
        time.sleep(0.5)

    def init(self):
        self.input_q.empty()
        self.stop = Event()
        self.p = Process(target=self.consume_input, )

    def consume_input(self, q: Queue):
        q.get()

    def __init__(self, input_q: Queue):
        super().__init__()
        self.data = {}
        self.tmp = 0
        self.input_q = input_q
        self.stop = Event()
        self.p: Optional[Process] = None


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


# 所有输入都接入 InputHub


class Task(ABC):
    def __init__(self, task_name: str, event_q: Queue, memory: Memory):
        self.event_q: Queue = event_q
        self.task_name = task_name
        self.memory = memory

    @abstractmethod
    def task(self, event):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass


class Mark1(object):

    def __init__(self):
        self.memory = None
        self.attention = None
        self.input = None
        self.output = None
        self.logic = None
        self.quartz: Optional[Quartz] = None

        self.status = False

    def start(self, fps):
        if self.status:
            pass

        self.quartz = Quartz(fps=fps)
        # 初始化时钟

        # 初始化 memory
        memory = Memory()
        self.quartz.register(memory)

        # 初始化所有 attention, 将 attention 注册在 input 入流中

        # 检查所有input 入流

        # 将所有input 挂载在 input 总线上

        # 检查注册所有 output

        # 注册所有 logic
