# coding = utf-8
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict, Any, Callable
from multiprocessing import Queue, JoinableQueue, Process, Event
from queue import Full, Empty
import traceback

from util.utils import cts
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s - at line %(lineno)d', level=logging.INFO)


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


class InputObj(object):
    def __init__(self, data: Any, event_type: str, ts: Optional[int] = None):
        if ts is None:
            ts = cts()
        self.ts = ts
        self.event_type = event_type
        self.data = data

    def __repr__(self):
        return f'{self.ts}, {self.event_type}, {self.data}'


class Input(ABC):
    def __init__(self, fps=100):
        self.q: Queue = Queue()
        self.status: Event = Event()
        self.p: Optional[Process] = None
        self.fps = fps
        self.finish = Event()

    @abstractmethod
    def pull_input_param(self) -> Any:
        pass

    @classmethod
    @abstractmethod
    def pull_input(cls, param) -> Any:
        pass

    @abstractmethod
    def on(self):
        pass

    @abstractmethod
    def off(self):
        pass

    def push_input(self, data):
        if self.status.is_set():
            input_data = InputObj(data, self.__class__.__name__)
            self.q.put(input_data)

    @classmethod
    def loop(cls, q: Queue, status: Event, finish: Event, fps: int, pull_input: Callable, pull_input_param: Any):
        logging.info(f'[Input.{cls.__name__}.Subprocess] start loop')
        try:
            while not finish.is_set():
                status.wait()
                if finish.is_set():
                    break

                try:
                    input_data = InputObj(pull_input(pull_input_param), cls.__name__)
                except BaseException as e:
                    traceback.print_exc()
                    continue

                try:
                    q.put(input_data)
                except EOFError as e:
                    if finish.is_set():
                        continue
                    raise e

                time.sleep(1 / fps)
        except KeyboardInterrupt as e:
            pass
        finally:
            logging.info(f'[Input.{cls.__name__}.Subprocess] stop loop')

    def start(self):
        if self.status.is_set() or self.finish.is_set():
            return
        self.q.empty()
        self.on()
        self.status.set()
        if self.fps > 0 and self.p is None:
            self.p = Process(target=self.loop, args=(self.q, self.status, self.finish, self.fps, self.pull_input,
                                                     self.pull_input_param()))
            self.p.start()
        logging.info(f'[Input.{self.__class__.__name__}] status: start')

    def stop(self):
        if not self.status.is_set() or self.finish.is_set():
            return
        self.off()
        self.status.clear()
        logging.info(f'[Input.{self.__class__.__name__}] status: pause')

    def close(self):
        logging.info(f'[Input.{self.__class__.__name__}] closing...')
        self.finish.set()
        self.status.set()   # 防止进程卡在 status.wait() 无法退出
        self.off()
        self.q.put(EOFError('close'))
        self.q.close()
        self.p.join()
        logging.info(f'[Input.{self.__class__.__name__}] closed')


from pynput import mouse


class MouseInput(Input):
    controller: mouse.Controller = mouse.Controller()

    def __init__(self, fps=100):
        super().__init__(fps=fps)
        self.listener: Optional[mouse.Listener] = None
        self.position_pull = fps > 0

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
        )
        if not self.position_pull:
            self.listener.on_move = self.on_move
        self.listener.start()

    def off(self):
        self.listener.stop()

    @classmethod
    def pull_input(cls, param) -> Any:
        return 'move', cls.controller.position

    def pull_input_param(self) -> Any:
        pass


from util.platform import is_mac, is_windows
from util.region import Box

if is_mac():
    from mss import mss
    import numpy as np
if is_windows():
    import dxcam


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


import select
from threading import Thread


# 所有输入都接入 InputHub
class InputHub(object):
    def __init__(self):
        super().__init__()
        self.queue: Queue = Queue()
        self.inputs: Dict[str, Input] = {}
        self.inputs_consumer: Dict[str, Thread] = {}
        self.event_bus: Queue = Queue()
        self.finish: Event = Event()

    def _consume(self, name: str, q: Queue):
        logging.info(f'[InputHub.{name}.SubThread] input consumer start')
        while not self.finish.is_set():
            try:
                e = q.get()
                if isinstance(e, EOFError):
                    break
                self.event_bus.put(e)
            except EOFError:
                if self.finish.is_set():
                    break
                else:
                    raise EOFError
        logging.info(f'[InputHub.{name}.SubThread] input consumer stop')

    def register(self, iinput_id: str, iinput: Input):
        if self.inputs.get(iinput_id):
            raise Exception('input_id duplicated')
        self.inputs[iinput_id] = iinput
        self.inputs_consumer[iinput_id] = Thread(target=self._consume, args=(iinput_id, iinput.q,))
        self.inputs_consumer[iinput_id].start()

    def get_input(self, iinput_id: str):
        return self.inputs.get(iinput_id)

    def start(self, iinput_id: str):
        self.get_input(iinput_id).start()

    def stop(self, iinput_id: str):
        logging.debug(f'[InputHub] trying to stop {iinput_id}')
        self.get_input(iinput_id).stop()

    def close(self):
        self.finish.set()
        for iinput_id, iinput in self.inputs.items():
            logging.info(f'[InputHub.{iinput_id}] closing producer')
            iinput.close()
            logging.info(f'[InputHub.{iinput_id}] producer closed: {iinput.p.is_alive()}')

            logging.info(f'[InputHub.{iinput_id}] closing consumer')
            t = self.inputs_consumer.get(iinput_id)
            t.join()
            logging.info(f'[InputHub.{iinput_id}] consumer is_alive: {t.is_alive()}')

        self.event_bus.close()


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


import cv2

if __name__ == '__main__':
    from util.region import center_box

    input_mouse = MouseInput(1)

    screen = ScreenInput(120, region=center_box)

    hub = InputHub()
    hub.register('mouse', input_mouse)
    hub.register('screen', screen)

    hub.start('mouse')
    try:
        while True:
            event: InputObj = hub.event_bus.get()
            if event.event_type == 'MouseInput':
                if event.data[0] == 'click' and event.data[4]:
                    hub.start('screen')

                if event.data[0] == 'click' and not event.data[4]:
                    hub.stop('screen')

            if event.event_type == 'ScreenInput':
                if event.data is None:
                    continue
                cv2.imshow('test', event.data)
                cv2.waitKey(1)
                time.sleep(0.01)
    except (SystemExit, KeyboardInterrupt):
        hub.close()
