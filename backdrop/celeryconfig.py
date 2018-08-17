import os
import ssl

if os.environ.get('BACKDROP_BROKER_SSL_CERT_REQS', False):
    broker_use_ssl = {
        'ssl_cert_reqs': eval('ssl.{}'.format(os.environ['BACKDROP_BROKER_SSL_CERT_REQS']))
    }
