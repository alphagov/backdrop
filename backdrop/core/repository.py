
import json

import requests

from backdrop.core.bucket import BucketConfig
from backdrop.core.user import UserConfig


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

    def retrieve(self, value):
        return self.find_first_instance_of({self.id_field: value})

    def find_first_instance_of(self, params):
        doc = self.collection.find_one(params)
        if doc is None:
            return None
        return self._create_model(doc)

    def get_all(self):
        # Return a list of all bucket config instances
        return [self._create_model(doc) for doc in self.collection.find()]

    def _create_model(self, doc):
        del doc["_id"]
        return self.model_cls(**doc)


class BucketConfigRepository(object):

    def __init__(self, stagecraft_url, stagecraft_token):
        self._stagecraft_url = stagecraft_url
        self._stagecraft_token = stagecraft_token

    def save(self, bucket_config, create_bucket=True):
        raise NotImplementedError("You can't create/update data-sets through "
                                  "backdrop any more - this is read-only.")

    def get_all(self):
        data_set_url = '{url}/data-sets/'.format(url=self._stagecraft_url)

        data_sets = _decode_json(_get_url(data_set_url))
        return [_make_bucket_config(data_set) for data_set in data_sets]

    def retrieve(self, name):
        data_set_url = ('{url}/data-sets/{data_set_name}'.format(
                        url=self._stagecraft_url,
                        data_set_name=name))

        data_set = _decode_json(_get_url(data_set_url))
        return _make_bucket_config(data_set)

    def get_bucket_for_query(self, data_group, data_type):
        data_set_url = ('{url}/data-sets?data-group={data_group_name}'
                        '&data-type={data_type_name}'.format(
                            url=self._stagecraft_url,
                            data_group_name=data_group,
                            data_type_name=data_type))

        data_sets = _decode_json(_get_url(data_set_url))
        if len(data_sets) > 0:
            return _make_bucket_config(data_sets[0])
        return None


def _make_bucket_config(stagecraft_dict):
    if stagecraft_dict is None:
        return None
    return BucketConfig(**stagecraft_dict)


def _decode_json(string):
    return json.loads(string) if string is not None else None


def _get_url(url):
    response = requests.get(url)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise e

    return response.content


class UserConfigRepository(object):

    def __init__(self, db):
        self._db = db
        self._repository = _Repository(db, UserConfig, "users", "email")

    def save(self, user_config):
        self._repository.save(user_config)

    def retrieve(self, email):
        return self._repository.retrieve(email)
