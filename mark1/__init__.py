import logging

import colorlog

logger = logging.getLogger('mark1')
logger.setLevel(logging.DEBUG)

log_colors_config = {
    'DEBUG': 'white',
    'INFO': 'cyan',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

default_formats = {
    'color_format': '%(log_color)s%(asctime)s-%(levelname)s - File "%(pathname)s", line %(lineno)d  - %(message)s',
}

handler = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter(default_formats["color_format"], log_colors=log_colors_config)
handler.setFormatter(formatter)
logger.addHandler(handler)
