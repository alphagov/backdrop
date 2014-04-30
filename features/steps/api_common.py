from behave import *
from hamcrest import *
from features.support.stagecraft import StagecraftService

TEST_STAGECRAFT_PORT = 3204


def ensure_data_set_exists(context, data_set_name, settings={}):
    # these should mostly match the default DataSetConfig.__new__() kwargs
    response = {
        'name': data_set_name,
        'data_group': data_set_name,
        'data_type': data_set_name,
        'raw_queries_allowed': False,
        'bearer_token': '%s-bearer-token' % data_set_name,
        'upload_format': 'csv',
        'upload_filters': ['backdrop.core.upload.filters.first_sheet_filter'],
        'auto_ids': None,
        'queryable': True,
        'realtime': False,
        'capped_size': 5040,
        'max_age_expected': 2678400,
    }

    response.update(settings)

    url_response_dict = {
        ('GET', u'data-sets/{}'.format(data_set_name)): response,
        ('GET', u'data-sets'): [response],
        ('GET', u'data-sets?data-group={}&data-type={}'.format(
            response['data_group'], response['data_type'])): [response],
    }

    if 'mock_stagecraft_server' in context and context.mock_stagecraft_server:
        context.mock_stagecraft_server.stop()
    context.mock_stagecraft_server = StagecraftService(
        TEST_STAGECRAFT_PORT, url_response_dict)
    context.mock_stagecraft_server.start()

    context.data_set = data_set_name
    data_set_data = {
        '_id': data_set_name,
        'name': data_set_name,
        'data_group': data_set_name,
        'data_type': data_set_name,
        'bearer_token': "%s-bearer-token" % data_set_name
    }
    context.client.storage()["data_sets"].save(data_set_data)
