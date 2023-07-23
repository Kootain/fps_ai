# coding_utf-8

import time

import cv2

from .device_mouse.inout_put import MouseInput
from .device_screen.inout_put import ScreenInput
from .input import InputHub, InputObj
from .job import PoseDetectJob

if __name__ == '__main__':
    from util.region import center_box

    input_mouse = MouseInput(1)

    screen = ScreenInput(20, region=center_box)

    hub = InputHub()
    hub.register('mouse', input_mouse)
    hub.register('screen', screen)

    hub.start('mouse')
    job = PoseDetectJob()
    job.init_pose()

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

                # result = job.q.put(event.data)
                job.run(event.data)


    except (SystemExit, KeyboardInterrupt):
        hub.close()
