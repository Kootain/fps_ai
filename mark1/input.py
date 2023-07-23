# coding=utf-8

import logging
import traceback
import time
from abc import ABC, abstractmethod
from threading import Thread
from multiprocessing import Queue, Event, Process
from typing import Optional, Any, Callable, Dict

from util.utils import cts

logger = logging.getLogger('mark1')


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
        logger.info(f'[Input.{cls.__name__}.Subprocess] start loop')
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
            logger.info(f'[Input.{cls.__name__}.Subprocess] stop loop')

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
        logger.info(f'[Input.{self.__class__.__name__}] status: start')

    def stop(self):
        if not self.status.is_set() or self.finish.is_set():
            return
        self.off()
        self.status.clear()
        logger.info(f'[Input.{self.__class__.__name__}] status: pause')

    def close(self):
        logger.info(f'[Input.{self.__class__.__name__}] closing...')
        self.finish.set()
        self.status.set()  # 防止进程卡在 status.wait() 无法退出
        self.off()
        self.q.put(EOFError('close'))
        self.q.close()
        self.p.join()
        logger.info(f'[Input.{self.__class__.__name__}] closed')


class InputHub(object):
    def __init__(self):
        super().__init__()
        self.queue: Queue = Queue()
        self.inputs: Dict[str, Input] = {}
        self.inputs_consumer: Dict[str, Thread] = {}
        self.event_bus: Queue = Queue()
        self.finish: Event = Event()

    def _consume(self, name: str, q: Queue):
        logger.info(f'[InputHub.{name}.SubThread] input consumer start')
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
        logger.info(f'[InputHub.{name}.SubThread] input consumer stop')

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
        logger.debug(f'[InputHub] trying to stop {iinput_id}')
        self.get_input(iinput_id).stop()

    def close(self):
        self.finish.set()
        for iinput_id, iinput in self.inputs.items():
            logger.info(f'[InputHub.{iinput_id}] closing producer')
            iinput.close()
            logger.info(f'[InputHub.{iinput_id}] producer closed: {iinput.p.is_alive()}')

            logger.info(f'[InputHub.{iinput_id}] closing consumer')
            t = self.inputs_consumer.get(iinput_id)
            t.join()
            logger.info(f'[InputHub.{iinput_id}] consumer is_alive: {t.is_alive()}')

        self.event_bus.close()
