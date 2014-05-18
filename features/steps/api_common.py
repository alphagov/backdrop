from features.support.stagecraft import create_or_update_stagecraft_service

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

    routes = {
        ('GET', u'data-sets/{}'.format(data_set_name)): response,
        ('GET', u'data-sets'): [response],
        ('GET', u'data-sets?data-group={}&data-type={}'.format(
            response['data_group'], response['data_type'])): [response],
    }

    create_or_update_stagecraft_service(context, TEST_STAGECRAFT_PORT, routes)

    context.data_set = data_set_name
