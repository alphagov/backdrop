import os
import json
from base64 import b64decode


def load_paas_settings():
    paas = {}
    if 'VCAP_SERVICES' in os.environ:
        vcap = json.loads(os.environ['VCAP_SERVICES'])
        database_engine = os.getenv('DATABASE_ENGINE', 'mongodb')
        paas['DATABASE_ENGINE'] = database_engine

        if database_engine == 'mongodb' and 'mongodb' in vcap:
            for service in vcap['mongodb']:
                if service['name'] == 'gds-performance-platform-mongodb-service':
                    credentials = service['credentials']
                    paas['DATABASE_URL'] = credentials['uri']
                    ca_cert = b64decode(credentials['ca_certificate_base64'])
                    paas['CA_CERTIFICATE'] = ca_cert

        if database_engine == 'postgres' and 'postgres' in vcap:
            for service in vcap['postgres']:
                if service['name'] == 'backdrop-db':
                    credentials = service['credentials']
                    paas['DATABASE_URL'] = credentials['uri']

        if 'REDIS_DATABASE_NUMBER' in os.environ:
            for service in vcap['redis']:
                if service['name'] == 'redis':
                    database_number = os.environ['REDIS_DATABASE_NUMBER']
                    url = service['credentials']['uri']
                    url += '/' + database_number
                    paas['REDIS_URL'] = url
    return paas
