# import logging
import colorlog
import logging
import inspect

from agentware.singleton import Singleton


class CallerFormatter(colorlog.ColoredFormatter):
    def format(self, record):
        # Get the caller's frame
        caller_frame = inspect.stack()[9]
        # Get the caller's filename and line number
        caller_filename = caller_frame.filename
        caller_lineno = caller_frame.lineno

        # Update the record's values
        record.filename = caller_filename
        record.lineno = caller_lineno

        return super().format(record)


class Logger(metaclass=Singleton):
    DEBUG = colorlog.DEBUG
    INFO = colorlog.INFO
    WARNING = colorlog.WARNING
    ERROR = colorlog.ERROR
    CRITICAL = colorlog.CRITICAL

    def __init__(self):
        self.logger = colorlog.getLogger('logger')
        self.logger.setLevel(colorlog.DEBUG)
        formatter = CallerFormatter(
            '%(log_color)s%(asctime)s - %(levelname)s - [%(filename)s: %(lineno)d] %(message)s',
            log_colors={
                'DEBUG': 'reset',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red'
            },
            reset=True,
            style='%'
        )
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(formatter)
        # console_handler.setLevel(colorlog.DEBUG)
        self.logger.addHandler(console_handler)

    def set_level(self, level):
        if not level in [self.DEBUG, self.INFO, self.WARNING, self.ERROR, self.CRITICAL]:
            raise ValueError(f"log level {level} in valid")
        self.logger.setLevel(level)

    def debug(self, message, bg_color=None):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
