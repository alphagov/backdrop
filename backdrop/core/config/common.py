import os
import json

def load_paas_settings():
    paas = {}
    if 'VCAP_SERVICES' in os.environ:
        vcap = json.loads(os.environ['VCAP_SERVICES'])
        for service in vcap['mongodb']:
            if service['name'] == 'gds-performance-platform-mongodb-service':
                paas['DATABASE_URL'] = service['credentials']['uri']
    return paas
