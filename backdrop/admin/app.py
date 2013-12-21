from os import getenv

from flask import Flask, jsonify

from ..core import cache_control, log_handler
from ..core.log_handler \
    import create_request_logger, create_response_logger

GOVUK_ENV = getenv("GOVUK_ENV", "development")

app = Flask("backdrop.admin.app", static_url_path="/static")

# Configuration
app.config.from_object(
    "backdrop.admin.config.{}".format(GOVUK_ENV))

log_handler.set_up_logging(app, GOVUK_ENV)


@app.route('/', methods=['GET'])
def index():
    return 'ok'


@app.route('/_status', methods=['GET'])
@cache_control.nocache
def health_check():
    return jsonify(status='ok', message='all ok')


def start(port):
    app.run('0.0.0.0', port=port)
    app.logger.info("Backdrop admin app started")
