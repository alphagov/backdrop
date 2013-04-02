from logging import FileHandler
import logging


def get_log_file_handler(path):
    handler = FileHandler(path)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] -> %(message)s"))
    handler.setLevel(logging.DEBUG)
    return handler
