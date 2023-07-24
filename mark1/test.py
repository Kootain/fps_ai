# coding_utf-8
import logging
import time

import cv2

from .device_mouse.inout_put import MouseInput, Button, MouseOutput
from .device_screen.inout_put import ScreenInput
from .input import InputHub, InputObj
from .job import PoseDetectJob, YoloPose
import logging

logger = logging.getLogger('mark1')

if __name__ == '__main__':
    from util.region import center_box, grab_width, grab_height

    input_mouse = MouseInput(1)
    output_mouse = MouseOutput()

    screen = ScreenInput(30, region=center_box)

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
                if event.data[0] == 'click' and event.data[4] and event.data[3] == Button.right:
                    hub.start('screen')
                    logger.info(event)

                if event.data[0] == 'click' and not event.data[4] and event.data[3] == Button.right:
                    hub.stop('screen')

            if event.event_type == 'ScreenInput':
                if event.data is None:
                    continue

                result = job.run(event.data)
                pose = YoloPose(result)
                if len(result[0].keypoints.data) == 0:
                    continue
                nose_pose = pose.target_obj(0, 'nose')
                if nose_pose is None:
                    continue
                nose_pose = nose_pose[0]
                w = 0.5
                output_mouse.move((nose_pose[0] - grab_width / 2) * w, (nose_pose[1] - grab_height / 2) * w)
                logger.debug(f'nose at {nose_pose}')
                logger.debug(f'move to {nose_pose[0] - grab_width / 2, nose_pose[1] - grab_height / 2}')

    except (SystemExit, KeyboardInterrupt):
        hub.close()
