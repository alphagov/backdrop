from logging import FileHandler
import logging


def get_log_file_handler(path, log_level=logging.DEBUG):
    handler = FileHandler(path)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] -> %(message)s"))
    handler.setLevel(log_level)
    return handler


def set_up_logging(app, name, env):
    log_level = logging._levelNames[app.config['LOG_LEVEL']]
    app.logger.addHandler(
        get_log_file_handler("log/%s.log" % env, log_level)
    )
    app.logger.setLevel(log_level)
    app.logger.info("Backdrop %s API logging started" % name)
