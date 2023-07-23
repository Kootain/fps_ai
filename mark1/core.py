# coding = utf-8
import time
from abc import ABC, abstractmethod
from multiprocessing import Queue, Process, Event
from queue import Full, Empty
from typing import List, Optional, Union

from util.utils import cts


# class Memory(BaseTiker):
#
#     def do(self, ts):
#         print(cts() - ts)
#         self.tmp = ts
#         time.sleep(0.5)
#
#     def init(self):
#         self.input_q.empty()
#         self.stop = Event()
#         self.p = Process(target=self.consume_input, )
#
#     def consume_input(self, q: Queue):
#         q.get()
#
#     def __init__(self, input_q: Queue):
#         super().__init__()
#         self.data = {}
#         self.tmp = 0
#         self.input_q = input_q
#         self.stop = Event()
#         self.p: Optional[Process] = None


class Mark1(object):

    def __init__(self):
        self.memory = None
        self.attention = None
        self.input = None
        self.output = None
        self.logic = None
        # self.quartz: Optional[Quartz] = None

        self.status = False

    def start(self, fps):
        if self.status:
            pass

        # self.quartz = Quartz(fps=fps)
        # 初始化时钟

        # 初始化 memory

        # 初始化所有 attention, 将 attention 注册在 input 入流中

        # 检查所有input 入流

        # 将所有input 挂载在 input 总线上

        # 检查注册所有 output

        # 注册所有 logic
