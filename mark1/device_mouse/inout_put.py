# coding=utf-8

from pynput import mouse
from pynput.mouse import Button
from typing import Any, Optional
import interception

from ..input import Input


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

    def close(self):
        super().close()


class MouseOutput(object):
    def __init__(self):
        pass

    def move(self, x, y):
        interception.move_relative(x, y)
