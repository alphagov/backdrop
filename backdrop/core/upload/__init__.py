from .utils import make_dicts
from .parse_csv import parse_csv
from .parse_excel import parse_excel


def create_parser(upload_format, upload_filters):
    format_parser = load_format_parser(upload_format)
    upload_filters = map(load_filter, upload_filters)

    def parser(file_stream):
        data = format_parser(file_stream)
        for upload_filter in upload_filters:
            data = upload_filter(data)

        return list(make_dicts(data))

    return parser


def load_format_parser(upload_format):
    return {
        "csv": parse_csv,
        "excel": parse_excel,
    }[upload_format]


def load_filter(filter_name):
    if callable(filter_name):
        return filter_name
    module_name, func_name = filter_name.rsplit(".", 1)

    module = __import__(
        module_name,
        fromlist=filter_name.rsplit(".", 1)[0])

    return getattr(module, func_name)
