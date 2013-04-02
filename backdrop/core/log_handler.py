from logging import FileHandler
import logging


def get_log_file_handler(path, log_level=logging.DEBUG):
    handler = FileHandler(path)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] -> %(message)s"))
    handler.setLevel(log_level)
    return handler
