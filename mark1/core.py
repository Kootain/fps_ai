# coding = utf-8
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict, Any, Callable
from multiprocessing import Queue, JoinableQueue, Process, Event
from queue import Full, Empty
from util.utils import cts
import logging


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
        self.p:Optional[Process] = None


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


class InputObj(object):
    def __init__(self, data: Any, ts: Optional[int]=None):
        if ts is None:
            ts = cts()
        self.ts = ts
        self.data = data

    def __repr__(self):
        return f'{self.ts}, {self.data}'


class Input(ABC):
    def __init__(self, fps=100):
        self.q: Queue = Queue()
        self.stop_event: Optional[Event] = None
        self.p: Optional = None
        self.fps = fps

    @classmethod
    @abstractmethod
    def pull_input(cls) -> Any:
        pass

    @abstractmethod
    def on(self):
        pass

    @abstractmethod
    def off(self):
        pass

    def push_input(self, data):
        if not self.stop_event.is_set():
            input_data = InputObj(data)
            self.q.put(input_data)

    @classmethod
    def loop(cls, q: Queue, stop_event: Event, pull_input: Callable, fps: int):
        logging.debug(f'[Input.{cls.__name__}] start loop')
        while not stop_event.is_set():
            input_data = InputObj(pull_input())
            q.put(input_data)
            time.sleep(1/fps)
        logging.debug(f'[Input.{cls.__name__}] stop loop')

    def start(self):
        self.stop_event = Event()
        self.q.empty()
        self.on()
        self.p = Process(target=self.loop, args=(self.q, self.stop_event, self.pull_input, self.fps))
        self.p.start()
        logging.info(f'[Input.{self.__class__.__name__}] start running')

    def stop(self):
        self.off()
        self.stop_event.set()
        # TODO: 检查进程退出状况

        logging.info(f'[Input.{self.__class__.__name__}] stop running.')


from pynput import mouse


class MouseInput(Input):

    controller: mouse.Controller = mouse.Controller()

    def __init__(self, fps=100):
        super().__init__(fps=fps)
        self.listener: Optional[mouse.Listener] = None

    def on_move(self, x, y):
        self.push_input(('move', x, y))

    def on_click(self, x, y, button, pressed):
        self.push_input(('click', x, y, button, pressed))

    def on_scroll(self, x, y, dx, dy):
        self.push_input(('scroll', x, y, dx, dy))

    def on(self):
        self.listener = mouse.Listener(
            on_click=self.on_click,
            on_scroll=self.on_scroll,
            on_move=self.on_move,
        )
        self.listener.start()

    def off(self):
        self.listener.close()

    @classmethod
    def pull_input(cls) -> Any:
        return 'move', *cls.controller.position


# 所有输入都接入 InputHub
class InputHub(object):
    def __init__(self):
        super().__init__()
        self.queue: Queue = Queue()
        self.inputs: Dict[str, Input] = {}
        self.buffer = []

    def register(self, iinput_id: str, iinput: Input):
        if self.inputs.get(iinput_id):
            raise Exception('input_id duplicated')
        self.inputs[iinput_id] = iinput


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


if __name__ == '__main__':
    i = MouseInput(1)
    i.start()

    while True:
        print(i.q.get())

