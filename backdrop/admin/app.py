from flask import Flask, jsonify

from ..core import cache_control


app = Flask(__name__, static_url_path="/static")


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
