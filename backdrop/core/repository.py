import json
import logging

import requests
from urllib import quote

from backdrop.core.data_set import DataSetConfig
from backdrop.core.user import UserConfig

from backdrop import statsd

logger = logging.getLogger(__name__)


def get_user_repository(app):
    return UserConfigHttpRepository(
        app.config['STAGECRAFT_URL'],
        app.config['STAGECRAFT_DATA_SET_QUERY_TOKEN'])


class HttpRepository(object):
    def __init__(self,
                 stagecraft_url,
                 stagecraft_token,
                 model_name,
                 model_cls):
        self._stagecraft_url = stagecraft_url
        self._stagecraft_token = stagecraft_token
        self._model_name = model_name
        self._model_cls = model_cls

    def get_all(self):
        with statsd.timer('repository.http.get_all.{model_name}'.format(
                model_name=self._model_name)):
            url = '{base_url}/{model_name}s'.format(
                base_url=self._stagecraft_url,
                model_name=self._model_name)

            # Note: Don't catch HTTP 404 - should never happen on this URL.
            json_response = _get_json_url(url, self._stagecraft_token)
            items = _decode_json(json_response)

            return [self.create_model(item) for item in items]

    def retrieve(self, identifier):
        if len(identifier) == 0:
            raise ValueError('the identifier must not be empty')

        with statsd.timer(
            'repository.http.retrieve.{model_name}s.{identifier}'.format(
                model_name=self._model_name,
                identifier=identifier)):
            path = quote('{model_name}s/{instance_identifier}'.format(
                model_name=self._model_name,
                instance_identifier=identifier))
            url = ('{base_url}/{path}'.format(
                base_url=self._stagecraft_url,
                path=path))

            try:
                json_response = _get_json_url(url, self._stagecraft_token)
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    return None
                else:
                    raise

            return self.create_model(_decode_json(json_response))

    @statsd.timer('repository.http.create_model')
    def create_model(self, stagecraft_dict):
        if stagecraft_dict is None:
            return None
        return self._model_cls(**stagecraft_dict)


class _Repository(object):

    def __init__(self, db, model_cls, collection_name, id_field):
        self.db = db
        self.model_cls = model_cls
        self.collection_name = collection_name
        self.id_field = id_field
        self.collection = db.get_collection(self.collection_name)

    def save(self, model):
        if not isinstance(model, self.model_cls):
            raise ValueError("Expected {0}".format(self.model_cls.__name__))

        doc = {
            "_id": getattr(model, self.id_field)
        }
        doc.update(model._asdict())

        self.collection.save(doc)

    def retrieve(self, identifier):
        return self.find_first_instance_of({self.id_field: identifier})

    def find_first_instance_of(self, params):
        doc = self.collection.find_one(params)
        if doc is None:
            return None
        return self._create_model(doc)

    def get_all(self):
        # Return a list of all data_set config instances
        return [self._create_model(doc) for doc in self.collection.find()]

    def _create_model(self, doc):
        del doc["_id"]
        return self.model_cls(**doc)


class DataSetConfigRepository(object):

    def __init__(self, stagecraft_url, stagecraft_token):
        self._stagecraft_url = stagecraft_url
        self._stagecraft_token = stagecraft_token
        self._repository_proxy = HttpRepository(
            stagecraft_url,
            stagecraft_token,
            'data-set',
            DataSetConfig)

    @statsd.timer('repository.data_set_config.get_all')
    def get_all(self):
        return self._repository_proxy.get_all()

    @statsd.timer('repository.data_set_config.retrieve')
    def retrieve(self, data_set_name):
        return self._repository_proxy.retrieve(data_set_name)

    @statsd.timer('repository.data_set_config.get_data_set_for_query')
    def get_data_set_for_query(self, data_group, data_type):
        empty_vars = []
        if len(data_group) == 0:
            empty_vars += ['Data Group']
        if len(data_type) == 0:
            empty_vars += ['Data Type']
        if len(empty_vars) > 0:
            raise ValueError(' and '.join(empty_vars) + 'must not be empty')

        with statsd.timer(
            'repository.data_set_config.get_data_set_for_query.'
            + '{data_group}.{data_type}'.format(
                data_group=data_group,
                data_type=data_type)):
            data_set_url = ('{url}/data-sets?data-group={data_group_name}'
                            '&data-type={data_type_name}'.format(
                                url=self._stagecraft_url,
                                data_group_name=data_group,
                                data_type_name=data_type))

            json_response = _get_json_url(
                data_set_url, self._stagecraft_token)

            data_sets = _decode_json(json_response)
            if len(data_sets) > 0:
                return self._repository_proxy.create_model(data_sets[0])

            return None


def _decode_json(string):
    return json.loads(string) if string is not None else None


def _get_json_url(url, token):
    auth_header = (
        'Authorization',
        'Bearer {}'.format(token))
    response = requests.get(url, headers=dict([
        ('content-type', 'application/json'),
        auth_header]), verify=False)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.exception(e)
        logger.error('Stagecraft said: {}'.format(response.content))
        raise
    return response.content


class UserConfigHttpRepository(object):

    def __init__(self, stagecraft_url, stagecraft_token):
        self._stagecraft_url = stagecraft_url
        self._stagecraft_token = stagecraft_token
        self._repository = HttpRepository(
            stagecraft_url,
            stagecraft_token,
            'user',
            UserConfig)

    def save(self, user_config):
        raise NotImplementedError

    def retrieve(self, email):
        return self._repository.retrieve(email)
