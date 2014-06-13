from hamcrest import assert_that, is_, has_item, has_entries, \
    has_length, contains, has_entry, contains_string
from nose.tools import assert_raises
from mock import Mock

from backdrop.core import data_set
from backdrop.core.data_set import DataSetConfig
from backdrop.core.query import Query
from backdrop.core.timeseries import WEEK, MONTH
from backdrop.core.errors import ValidationError
from jsonschema import ValidationError as SchemaValidationError
from tests.support.test_helpers import d, d_tz, match


def mock_database(mock_repository):
    mock_database = Mock()
    mock_database.get_repository.return_value = mock_repository
    return mock_database


def mock_repository():
    mock_repository = Mock()
    mock_repository.find.return_value = []
    mock_repository.group.return_value = []
    return mock_repository


class BaseNewDataSetTest(object):
    def setup_config(self, **kwargs):
        self.mock_storage = Mock()
        self.data_set_config = DataSetConfig(
            'test_data_set', data_group='group', data_type='type', **kwargs)
        self.data_set = data_set.NewDataSet(
            self.mock_storage, self.data_set_config)

    def setUp(self):
        self.setup_config()


class TestNewDataSet_store(BaseNewDataSetTest):
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "title": "Timestamps",
        "type": "object",
        "properties": {
            "_timestamp": {
                "description": "An ISO8601 formatted date time",
                "type": "string",
                "format": "date-time"
            }
        },
        "required": ["_timestamp"]
    }

    def test_storing_a_simple_record(self):
        self.data_set.store([{'foo': 'bar'}])
        self.mock_storage.save_record.assert_called_with(
            'test_data_set', {'foo': 'bar'})

    def test_id_gets_automatically_generated_if_auto_ids_are_set(self):
        self.setup_config(auto_ids=['foo'])
        self.data_set.store([{'foo': 'bar'}])
        self.mock_storage.save_record.assert_called_with(
            'test_data_set', match(has_entry('_id', 'YmFy')))

    def test_timestamp_gets_parsed(self):
        """Test that timestamps get parsed
        For unit tests on timestamp parsing, including failure modes,
        see the backdrop.core.records module
        """
        self.data_set.store([{'_timestamp': '2012-12-12T00:00:00+00:00'}])
        self.mock_storage.save_record.assert_called_with(
            'test_data_set',
            match(has_entry('_timestamp',  d_tz(2012, 12, 12))))

    def test_record_gets_validated(self):
        assert_raises(ValidationError, self.data_set.store, [{'_foo': 'bar'}])

    def test_each_record_gets_validated_further_when_schema_given(self):
        self.setup_config(schema=self.schema)
        #does store only take lists?
        with assert_raises(SchemaValidationError) as e:
            self.data_set.store([{"_timestamp": "2014-06-12T00:00:00+0000"},{'foo': 'bar'}])

        assert_that(
            str(e.exception),
            contains_string("_timestamp' is a required property")
        )

    def test_period_keys_are_added(self):
        self.data_set.store([{'_timestamp': '2012-12-12T00:00:00+00:00'}])
        self.mock_storage.save_record.assert_called_with(
            'test_data_set',
            match(has_entry('_day_start_at', d_tz(2012, 12, 12))))


class TestNewDataSet_execute_query(BaseNewDataSetTest):

    def test_period_query_fails_when_weeks_do_not_start_on_monday(self):
        self.mock_storage.execute_query.return_value = [
            {"_week_start_at": d(2013, 1, 7, 0, 0, 0), "_count": 3},
            {"_week_start_at": d(2013, 1, 8, 0, 0, 0), "_count": 1},
        ]

        assert_raises(
            ValueError,
            self.data_set.execute_query,
            Query.create(period=WEEK)
        )

    def test_period_query_fails_when_months_do_not_start_on_the_1st(self):
        self.mock_storage.execute_query.return_value = [
            {"_month_start_at": d(2013, 1, 7, 0, 0, 0), "_count": 3},
            {"_month_start_at": d(2013, 2, 8, 0, 0, 0), "_count": 1},
        ]

        assert_raises(
            ValueError,
            self.data_set.execute_query,
            Query.create(period=MONTH)
        )

    def test_period_query_adds_missing_periods_in_correct_order(self):
        self.mock_storage.execute_query.return_value = [
            {"_week_start_at": d(2013, 1, 14, 0, 0, 0), "_count": 32},
            {"_week_start_at": d(2013, 1, 21, 0, 0, 0), "_count": 45},
            {"_week_start_at": d(2013, 2, 4, 0, 0, 0), "_count": 17},
        ]

        result = self.data_set.execute_query(
            Query.create(period=WEEK,
                         start_at=d_tz(2013, 1, 7, 0, 0,
                                       0),
                         end_at=d_tz(2013, 2, 18, 0, 0,
                                     0)))

        assert_that(result, contains(
            has_entries({"_start_at": d_tz(2013, 1, 7), "_count": 0}),
            has_entries({"_start_at": d_tz(2013, 1, 14), "_count": 32}),
            has_entries({"_start_at": d_tz(2013, 1, 21), "_count": 45}),
            has_entries({"_start_at": d_tz(2013, 1, 28), "_count": 0}),
            has_entries({"_start_at": d_tz(2013, 2, 4), "_count": 17}),
            has_entries({"_start_at": d_tz(2013, 2, 11), "_count": 0}),
        ))

    def test_week_and_group_query(self):
        self.mock_storage.execute_query.return_value = [
            {"some_group": "val1", "_week_start_at": d(2013, 1, 7), "_count": 1},
            {"some_group": "val1", "_week_start_at": d(2013, 1, 14), "_count": 5},
            {"some_group": "val2", "_week_start_at": d(2013, 1, 7), "_count": 2},
            {"some_group": "val2", "_week_start_at": d(2013, 1, 14), "_count": 6},
        ]
        data = self.data_set.execute_query(
            Query.create(period=WEEK, group_by="some_group"))

        assert_that(data, has_length(2))
        assert_that(data, has_item(has_entries({
            "values": has_item({
                "_start_at": d_tz(2013, 1, 7, 0, 0, 0),
                "_end_at": d_tz(2013, 1, 14, 0, 0, 0),
                "_count": 1
            }),
            "some_group": "val1"
        })))
        assert_that(data, has_item(has_entries({
            "values": has_item({
                "_start_at": d_tz(2013, 1, 14, 0, 0, 0),
                "_end_at": d_tz(2013, 1, 21, 0, 0, 0),
                "_count": 5
            }),
            "some_group": "val1"
        })))
        assert_that(data, has_item(has_entries({
            "values": has_item({
                "_start_at": d_tz(2013, 1, 7, 0, 0, 0),
                "_end_at": d_tz(2013, 1, 14, 0, 0, 0),
                "_count": 2
            }),
            "some_group": "val2"
        })))
        assert_that(data, has_item(has_entries({
            "values": has_item({
                "_start_at": d_tz(2013, 1, 14, 0, 0, 0),
                "_end_at": d_tz(2013, 1, 21, 0, 0, 0),
                "_count": 6
            }),
            "some_group": "val2"
        })))

    def test_month_and_group_query(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', '_month_start_at': d(2013, 1, 1), '_count': 1},
            {'some_group': 'val1', '_month_start_at': d(2013, 2, 1), '_count': 5},
            {'some_group': 'val2', '_month_start_at': d(2013, 3, 1), '_count': 2},
            {'some_group': 'val2', '_month_start_at': d(2013, 4, 1), '_count': 6},
            {'some_group': 'val2', '_month_start_at': d(2013, 7, 1), '_count': 6},
        ]

        data = self.data_set.execute_query(Query.create(period=MONTH,
                                                        group_by="some_group"))
        assert_that(data,
                    has_item(has_entries({"values": has_length(2)})))
        assert_that(data,
                    has_item(has_entries({"values": has_length(3)})))

    def test_month_and_group_query_with_start_and_end_at(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', '_month_start_at': d(2013, 1, 1), '_count': 1},
            {'some_group': 'val1', '_month_start_at': d(2013, 2, 1), '_count': 5},
            {'some_group': 'val2', '_month_start_at': d(2013, 3, 1), '_count': 2},
            {'some_group': 'val2', '_month_start_at': d(2013, 4, 1), '_count': 6},
            {'some_group': 'val2', '_month_start_at': d(2013, 7, 1), '_count': 6},
        ]

        data = self.data_set.execute_query(
            Query.create(period=MONTH,
                         group_by="some_group",
                         start_at=d(2013, 1, 1),
                         end_at=d(2013, 4, 2)))
        assert_that(data,
                    has_item(has_entries({"values": has_length(4)})))
        assert_that(data,
                    has_item(has_entries({"values": has_length(4)})))

        first_group = data[0]["values"]
        assert_that(first_group, has_item(has_entries({
            "_start_at": d_tz(2013, 3, 1)})))
        assert_that(first_group, has_item(has_entries({
            "_start_at": d_tz(2013, 4, 1)})))

        first_group = data[1]["values"]
        assert_that(first_group, has_item(has_entries({
            "_start_at": d_tz(2013, 1, 1)})))
        assert_that(first_group, has_item(has_entries({
            "_start_at": d_tz(2013, 2, 1)})))

    def test_period_group_query_adds_missing_periods_in_correct_order(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 14), '_count': 23},
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 21), '_count': 41},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 14), '_count': 31},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 28), '_count': 12},
        ]

        data = self.data_set.execute_query(
            Query.create(period=WEEK, group_by="some_group",
                         start_at=d_tz(2013, 1, 7, 0, 0, 0),
                         end_at=d_tz(2013, 2, 4, 0, 0, 0)))

        assert_that(data, has_item(has_entries({
            "some_group": "val1",
            "values": contains(
                has_entries({"_start_at": d_tz(2013, 1, 7), "_count": 0}),
                has_entries({"_start_at": d_tz(2013, 1, 14), "_count": 23}),
                has_entries({"_start_at": d_tz(2013, 1, 21), "_count": 41}),
                has_entries({"_start_at": d_tz(2013, 1, 28), "_count": 0}),
            ),
        })))

        assert_that(data, has_item(has_entries({
            "some_group": "val2",
            "values": contains(
                has_entries({"_start_at": d_tz(2013, 1, 7), "_count": 0}),
                has_entries({"_start_at": d_tz(2013, 1, 14), "_count": 31}),
                has_entries({"_start_at": d_tz(2013, 1, 21), "_count": 0}),
                has_entries({"_start_at": d_tz(2013, 1, 28), "_count": 12}),
            ),
        })))

    def test_sorted_week_and_group_query(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 7), '_count': 1},
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 14), '_count': 5},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 7), '_count': 2},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 14), '_count': 6},
        ]

        query = Query.create(period=WEEK, group_by="some_group",
                             sort_by=["_count", "descending"])
        data = self.data_set.execute_query(query)

        assert_that(data, contains(
            has_entries({'some_group': 'val2'}),
            has_entries({'some_group': 'val1'}),
        ))

    def test_sorted_week_and_group_query_with_limit(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 7), '_count': 1},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 14), '_count': 5},
        ]

        query = Query.create(period=WEEK, group_by="some_group",
                             sort_by=["_count", "descending"], limit=1,
                             collect=[])
        data = self.data_set.execute_query(query)

        assert_that(data, contains(
            has_entries({'some_group': 'val2'})
        ))


class TestDataSetConfig(object):

    def test_creating_a_data_set_config_with_raw_queries_allowed(self):
        data_set_config = DataSetConfig("name", data_group="group", data_type="type", raw_queries_allowed=True)
        assert_that(data_set_config.raw_queries_allowed, is_(True))

    def test_default_values(self):
        data_set = DataSetConfig("default", data_group="with_defaults", data_type="def_type")

        assert_that(data_set.raw_queries_allowed, is_(False))
        assert_that(data_set.queryable, is_(True))
        assert_that(data_set.realtime, is_(False))
        assert_that(data_set.capped_size, is_(5040))
        assert_that(data_set.bearer_token, is_(None))
        assert_that(data_set.upload_format, is_("csv"))
        assert_that(data_set.upload_filters, is_(["backdrop.core.upload.filters.first_sheet_filter"]))
        assert_that(data_set.auto_ids, is_(None))

    def test_data_set_name_validation(self):
        data_set_names = {
            "": False,
            "foo": True,
            "foo_bar": True,
            "foo-bar": False,
            "12foo": False,
            123: False
        }
        for (data_set_name, name_is_valid) in data_set_names.items():
            if name_is_valid:
                DataSetConfig(data_set_name, data_group="group", data_type="type")
            else:
                assert_raises(ValueError, DataSetConfig, data_set_name, "group", "type")

    def test_max_age(self):
        data_set = DataSetConfig("default", "group", "type", realtime=False)
        assert_that(data_set.max_age, is_(1800))

        data_set = DataSetConfig("default", "group", "type", realtime=True)
        assert_that(data_set.max_age, is_(120))
