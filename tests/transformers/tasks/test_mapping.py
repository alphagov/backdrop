import unittest

from hamcrest import assert_that, is_

from backdrop.transformers.tasks.mapping import compute


data = [
    {
        "_count": 1,
        "_end_at": "2014-12-29T00:00:00+00:00",
        "_start_at": "2014-12-22T00:00:00+00:00",
        "browser": "Internet Explorer",
        "browserVersion": "6",
        "sessions:sum": 10
    },
    {
        "_count": 1,
        "_end_at": "2014-12-29T00:00:00+00:00",
        "_start_at": "2014-12-22T00:00:00+00:00",
        "browser": "Internet Explorer",
        "browserVersion": "7",
        "sessions:sum": 11
    },
    {
        "_count": 1,
        "_end_at": "2014-12-29T00:00:00+00:00",
        "_start_at": "2014-12-22T00:00:00+00:00",
        "browser": "Internet Explorer",
        "browserVersion": "9",
        "sessions:sum": 12
    },
    {
        "_count": 1,
        "_end_at": "2014-12-29T00:00:00+00:00",
        "_start_at": "2014-12-22T00:00:00+00:00",
        "browser": "Internet Explorer",
        "browserVersion": "10",
        "sessions:sum": 13
    },
    {
        "_count": 1,
        "_end_at": "2014-12-29T00:00:00+00:00",
        "_start_at": "2014-12-22T00:00:00+00:00",
        "browser": "Some other browser",
        "browserVersion": "10",
        "sessions:sum": 14
    },
]


def matches(item, props):
    return all(item[k] == v for k, v in props.iteritems())


def find_in(arr, props):
    for item in arr:
        if matches(item, props):
            return item

    return None


class MappingTestCase(unittest.TestCase):

    def test_compute(self):
        transformed_data = compute(data, {
            "value-attribute": "sessions:sum",
            "mapped-attribute": "browser-group",
            "mapping-keys": ["browser", "browserVersion"],
            "mappings": {
                "OldIE": ["Internet Explorer", "[2-8]{1}(.)*"],
                "NewIE": ["Internet Explorer", "(9|1)(.)*"],
            },
        })

        assert_that(len(transformed_data), is_(2))

        print transformed_data

        old_ie = find_in(transformed_data, {
            "browser-group": "OldIE",
            "_start_at": "2014-12-22T00:00:00+00:00",
        })
        assert_that(old_ie["sessions:sum"], is_(21))

        new_ie = find_in(transformed_data, {
            "browser-group": "NewIE",
            "_start_at": "2014-12-22T00:00:00+00:00",
        })
        assert_that(new_ie["sessions:sum"], is_(25))

    def test_compute_with_other(self):
        transformed_data = compute(data, {
            "value-attribute": "sessions:sum",
            "mapped-attribute": "browser-group",
            "other-mapping": "other",
            "mapping-keys": ["browser", "browserVersion"],
            "mappings": {
                "OldIE": ["Internet Explorer", "[2-8]{1}(.)*"],
                "NewIE": ["Internet Explorer", "(9|1)(.)*"],
            },
        })

        assert_that(len(transformed_data), is_(3))

        old_ie = find_in(transformed_data, {
            "browser-group": "OldIE",
            "_start_at": "2014-12-22T00:00:00+00:00",
        })
        assert_that(old_ie["sessions:sum"], is_(21))

        new_ie = find_in(transformed_data, {
            "browser-group": "NewIE",
            "_start_at": "2014-12-22T00:00:00+00:00",
        })
        assert_that(new_ie["sessions:sum"], is_(25))

        other = find_in(transformed_data, {
            "browser-group": "other",
            "_start_at": "2014-12-22T00:00:00+00:00",
        })
        assert_that(other["sessions:sum"], is_(14))
