from logging import FileHandler
from logging.handlers import RotatingFileHandler
from logstash_formatter import LogstashFormatter
import logging
from flask import request


class RequestIdFilter(logging.Filter):

    def filter(self, record):
        try:
            record.govuk_request_id = request.headers.get('Govuk-Request-Id')
        except RuntimeError:
            # flask will throw a runtime error if we are attempting to get the
            # header outside of the application context. In this case we can't
            # infer the request_id, so we can just pass
            pass
        return True


def get_log_file_handler(path, log_level=logging.DEBUG):
    handler = RotatingFileHandler(
        path, maxBytes=1024 * 1024 * 10, backupCount=5)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] -> %(message)s"))
    handler.setLevel(log_level)
    return handler


def get_json_log_handler(path, app_name):
    handler = RotatingFileHandler(
        path, maxBytes=1024 * 1024 * 10, backupCount=5)
    formatter = LogstashFormatter()
    formatter.defaults['@tags'] = ['application', app_name]
    handler.setFormatter(formatter)
    return handler


def set_up_logging(app, env):
    log_level = app.config['LOG_LEVEL']
    numeric_log_level = logging._levelNames[log_level]
    logger = logging.getLogger()
    if log_level == "DEBUG":
        logger.addHandler(logging.StreamHandler())
    logger.addHandler(
        get_log_file_handler("log/%s.log" % env, numeric_log_level)
    )
    logger.addHandler(
        get_json_log_handler("log/%s.json.log" % env, app.name)
    )
    logger.setLevel(numeric_log_level)
    request_id_filter = RequestIdFilter()
    app.logger.addFilter(request_id_filter)
    app.logger.info("{} logging started".format(app.name))
    app.logger.info("{} logging started".format(numeric_log_level))
    app.before_request(create_request_logger(app))
    app.after_request(create_response_logger(app))


def set_up_audit_logging(app, env):
    logger = logging.getLogger('backdrop.write.audit')
    logger.setLevel(logging._levelNames['INFO'])
    logger.addHandler(
        get_json_log_handler("log/audit/%s.log.json" % env, app.name))
    app.audit_logger = logger


def create_request_logger(app):
    def log_request():
        if request.method != "HEAD":
            app.logger.info("request: %s - %s" % (request.method, request.url),
                            extra=create_logging_extra_dict())
    return log_request


def create_response_logger(app):
    def log_response(response):
        if request.method != "HEAD":
            app.logger.info(
                "response: %s - %s - %s" % (
                    request.method, request.url, response.status
                ),
                extra=create_logging_extra_dict()
            )
        return response
    return log_response


def create_logging_extra_dict():
    return {'govuk_request_id': request.headers.get('Govuk-Request-Id')}
