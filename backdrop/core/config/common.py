import os
import json
from base64 import b64decode


def load_paas_settings():
    paas = {}
    if 'VCAP_SERVICES' in os.environ:
        vcap = json.loads(os.environ['VCAP_SERVICES'])
        if 'mongodb' in vcap:
            for service in vcap['mongodb']:
                if service['name'] == 'gds-performance-platform-mongodb-service':
                    credentials = service['credentials']
                    paas['DATABASE_URL'] = credentials['uri']
                    ca_cert = b64decode(credentials['ca_certificate_base64'])
                    paas['CA_CERTIFICATE'] = ca_cert
        if 'REDIS_DATABASE_NUMBER' in os.environ:
            for service in vcap['user-provided']:
                if service['name'] == 'redis-poc':
                    database_number = os.environ['REDIS_DATABASE_NUMBER']
                    url = service['credentials']['url']
                    url += '/' + database_number
                    paas['REDIS_URL'] = url
    return paas
