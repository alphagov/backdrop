from flask import Flask, jsonify
from pymongo import MongoClient


# Configuration
DATABASE_NAME = 'performance_platform'


app = Flask(__name__)
app.config.from_object(__name__)

mongo = MongoClient('localhost', 27017)


def collection(bucket):
    return mongo[app.config['DATABASE_NAME']][bucket]


@app.route('/<bucket>', methods=['GET'])
def query(bucket):
    return jsonify(data=list(collection(bucket).find()))


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
