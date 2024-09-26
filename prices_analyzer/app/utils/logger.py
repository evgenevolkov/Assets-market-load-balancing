"""Module responsible for logging """
from decouple import config
import logging


logging_level = config('LOGGING_LEVEL')


def get_logger(name):
    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging_level)
        formatter = logging.Formatter(
            '%(levelname)-8s - %(asctime)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if logger.level == logging.NOTSET:
        logger.setLevel(logging_level)

    return logger
