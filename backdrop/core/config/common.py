import os
import json
from base64 import b64decode

def load_paas_settings():
    paas = {}
    if 'VCAP_SERVICES' in os.environ:
        vcap = json.loads(os.environ['VCAP_SERVICES'])
        for service in vcap['mongodb']:
            if service['name'] == 'gds-performance-platform-mongodb-service':
                credentials = service['credentials']
                paas['DATABASE_URL'] = credentials['uri']
                ca_cert = b64decode(credentials['ca_certificate_base64'])
                paas['CA_CERTIFICATE'] = ca_cert
    return paas
