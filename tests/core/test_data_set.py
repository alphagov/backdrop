from freezegun import freeze_time
from hamcrest import assert_that, has_item, has_entries, \
    has_length, contains, has_entry, is_
from mock import Mock, patch
from nose.tools import assert_raises

from backdrop.core import data_set
from backdrop.core.query import Query
from backdrop.core.timeseries import WEEK, MONTH
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


class BaseDataSetTest(object):
    def setup_config(self, additional_config={}):
        self.mock_storage = Mock()
        base_config = {
            'name': 'test_data_set',
            'data_group': 'group',
            'data_type': 'type',
            'capped_size': 0,
        }
        self.data_set_config = dict(base_config.items() + additional_config.items())
        self.data_set = data_set.DataSet(
            self.mock_storage, self.data_set_config)

    def setUp(self):
        self.setup_config()


class TestNewDataSet_attributes(BaseDataSetTest):

    def test_seconds_out_of_date_returns_none_or_int(self):
        self.mock_storage.get_last_updated.return_value = None
        assert_that(self.data_set.get_seconds_out_of_date(), is_(None))

        self.mock_storage.get_last_updated.return_value = d_tz(2014, 7, 1)
        assert_that(self.data_set.get_seconds_out_of_date(), is_(int))

    def test_seconds_out_of_date_shows_correct_number_of_seconds_out_of_date(self):
        with freeze_time('2014-01-28'):
            # We expect it to be 0 seconds out of date
            self.setup_config({'max_age_expected': int(0)})

            # But it's a day out of date, so it should be 1day's worth of seconds out of date
            self.mock_storage.get_last_updated.return_value = d_tz(2014, 1, 27)
            assert_that(self.data_set.get_seconds_out_of_date(), is_(86400))

        with freeze_time('2014-01-28'):
            # We expect it to be a day out of date
            self.setup_config({'max_age_expected': int(86400)})

            self.mock_storage.get_last_updated.return_value = d_tz(2014, 1, 25)
            # It's three days out, so we should get 2 days past sell by date
            assert_that(self.data_set.get_seconds_out_of_date(), is_(172800))


class TestDataSet_store(BaseDataSetTest):
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
        self.setup_config({'auto_ids': ['foo']})
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
        errors = self.data_set.store([{'_foo': 'bar'}])
        assert_that(len(errors), 1)

    def test_each_record_gets_validated_further_when_schema_given(self):
        self.setup_config({'schema': self.schema})
        errors = self.data_set.store([{"_timestamp": "2014-06-12T00:00:00+0000"}, {'foo': 'bar'}])

        assert_that(
            len(filter(
                lambda error: "'_timestamp' is a required property" in error,
                errors)),
            1
        )

    def test_period_keys_are_added(self):
        self.data_set.store([{'_timestamp': '2012-12-12T00:00:00+00:00'}])
        self.mock_storage.save_record.assert_called_with(
            'test_data_set',
            match(has_entry('_day_start_at', d_tz(2012, 12, 12))))

    @patch('backdrop.core.storage.mongo.MongoStorageEngine.save_record')
    @patch('backdrop.core.records.add_period_keys')
    def test_store_returns_array_of_errors_if_errors(
            self,
            add_period_keys_patch,
            save_record_patch):
        self.setup_config({
            'schema': self.schema,
            'auto_ids': ["_timestamp", "that"]})
        errors = self.data_set.store([
            {"_timestamp": "2014-06-1xxx0:00:00+0000"},
            {'thing': {}},
            {'_foo': 'bar'}])

        assert_that(
            len(filter(
                lambda error: "'_timestamp' is a required property" in error,
                errors)),
            is_(2)
        )
        assert_that(
            "'2014-06-1xxx0:00:00+0000' is not a 'date-time'" in errors,
            is_(True)
        )
        assert_that(
            "thing has an invalid value" in errors,
            is_(True)
        )
        assert_that(
            "_foo is not a recognised internal field" in errors,
            is_(True)
        )
        assert_that(
            "_timestamp is not a valid datetime object" in errors,
            is_(True)
        )
        assert_that(
            'The following required id fields are missing: that' in errors,
            is_(True)
        )
        assert_that(
            'the _timestamp must be a date in the format yyyy-MM-ddT00:00:00Z'
            in errors,
            is_(True)
        )
        assert_that(
            len(errors),
            is_(8)
        )
        assert_that(add_period_keys_patch.called, is_(False))
        assert_that(save_record_patch.called, is_(False))

    @patch('backdrop.core.storage.mongo.MongoStorageEngine.save_record')
    @patch('backdrop.core.records.add_period_keys')
    def test_store_does_not_get_auto_id_type_error_due_to_datetime(
            self,
            add_period_keys_patch,
            save_record_patch):
        self.setup_config({
            'schema': self.schema,
            'auto_ids': ["_timestamp", "that"]})
        errors = self.data_set.store([
            {"_timestamp": "2012-12-12T00:00:00+00:00", 'that': 'dog'},
            {'thing': {}},
            {'_foo': 'bar'}])

        assert_that(
            len(filter(
                lambda error: "'_timestamp' is a required property" in error,
                errors)),
            is_(2)
        )
        assert_that(
            "thing has an invalid value" in errors,
            is_(True)
        )
        assert_that(
            "_foo is not a recognised internal field" in errors,
            is_(True)
        )
        assert_that(
            'The following required id fields are missing: _timestamp, that'
            in errors,
            is_(True)
        )
        assert_that(
            len(errors),
            is_(5)
        )
        assert_that(add_period_keys_patch.called, is_(False))
        assert_that(save_record_patch.called, is_(False))


class TestDataSet_patch(BaseDataSetTest):
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

    def test_patching_a_simple_record(self):
        self.data_set.patch('uuid', {'foo': 'bar'})
        self.mock_storage.update_record.assert_called_with(
            'test_data_set', 'uuid', {'foo': 'bar'})

    def test_record_not_found(self):
        self.mock_storage.find_record.return_value = None
        result = self.data_set.patch('uuid', {'foo': 'bar'})
        assert_that(result, is_('No record found with id uuid'))


class TestDataSet_delete(BaseDataSetTest):
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

    def test_deleting_a_simple_record(self):
        self.data_set.delete('uuid')
        self.mock_storage.delete_record.assert_called_with(
            'test_data_set', 'uuid'
        )

    def test_record_not_found(self):
        self.mock_storage.find_record.return_value = None
        result = self.data_set.delete('uuid')
        assert_that(result, is_('No record found with id uuid'))


class TestDataSet_execute_query(BaseDataSetTest):

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

    def test_last_updated_only_queries_once(self):
        self.mock_storage.get_last_updated.return_value = 3

        initial_last_updated = self.data_set.get_last_updated()
        second_last_updated = self.data_set.get_last_updated()

        assert_that(initial_last_updated, is_(3))
        assert_that(second_last_updated, is_(3))
        assert_that(self.mock_storage.get_last_updated.call_count, 1)

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
            Query.create(period=WEEK, group_by=['some_group']))

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

    def test_flattened_week_and_group_query(self):
        self.mock_storage.execute_query.return_value = [
            {"some_group": "val1", "_week_start_at": d(2013, 1, 7), "_count": 1},
            {"some_group": "val1", "_week_start_at": d(2013, 1, 14), "_count": 5},
            {"some_group": "val2", "_week_start_at": d(2013, 1, 7), "_count": 2},
            {"some_group": "val2", "_week_start_at": d(2013, 1, 14), "_count": 6},
        ]

        data = self.data_set.execute_query(
            Query.create(period=WEEK, group_by=['some_group'], flatten=True))

        assert_that(data, has_length(4))
        assert_that(data, has_item(has_entries({
            "_start_at": d_tz(2013, 1, 7, 0, 0, 0),
            "_end_at": d_tz(2013, 1, 14, 0, 0, 0),
            "_count": 1,
            "some_group": "val1"
        })))
        assert_that(data, has_item(has_entries({
            "_start_at": d_tz(2013, 1, 14, 0, 0, 0),
            "_end_at": d_tz(2013, 1, 21, 0, 0, 0),
            "_count": 5,
            "some_group": "val1"
        })))
        assert_that(data, has_item(has_entries({
            "_start_at": d_tz(2013, 1, 7, 0, 0, 0),
            "_end_at": d_tz(2013, 1, 14, 0, 0, 0),
            "_count": 2,
            "some_group": "val2"
        })))
        assert_that(data, has_item(has_entries({
            "_start_at": d_tz(2013, 1, 14, 0, 0, 0),
            "_end_at": d_tz(2013, 1, 21, 0, 0, 0),
            "_count": 6,
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
                                                        group_by=['some_group']))
        assert_that(data,
                    has_item(has_entries({"values": has_length(2)})))
        assert_that(data,
                    has_item(has_entries({"values": has_length(3)})))

    def test_month_and_groups_query(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', 'another_group': 'val3', '_month_start_at': d(2013, 1, 1), '_count': 1},
            {'some_group': 'val1', 'another_group': 'val3', '_month_start_at': d(2013, 2, 1), '_count': 5},
            {'some_group': 'val2', 'another_group': 'val3', '_month_start_at': d(2013, 3, 1), '_count': 2},
            {'some_group': 'val2', 'another_group': 'val3', '_month_start_at': d(2013, 4, 1), '_count': 6},
            {'some_group': 'val2', 'another_group': 'val3', '_month_start_at': d(2013, 7, 1), '_count': 6},
        ]

        data = self.data_set.execute_query(Query.create(period=MONTH,
                                                        group_by=['some_group', 'another_group']))
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
                         group_by=['some_group'],
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

    def test_flattened_month_and_group_query_with_start_and_end_at(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', '_month_start_at': d(2013, 1, 1), '_count': 1},
            {'some_group': 'val1', '_month_start_at': d(2013, 2, 1), '_count': 5},
            {'some_group': 'val2', '_month_start_at': d(2013, 3, 1), '_count': 2},
            {'some_group': 'val2', '_month_start_at': d(2013, 4, 1), '_count': 6},
            {'some_group': 'val2', '_month_start_at': d(2013, 7, 1), '_count': 6},
        ]

        data = self.data_set.execute_query(
            Query.create(period=MONTH,
                         group_by=['some_group'],
                         start_at=d(2013, 1, 1),
                         end_at=d(2013, 4, 2),
                         flatten=True))
        assert_that(data, has_length(8))

        assert_that(data, has_item(has_entries({
            '_count': 1,
            '_start_at': d_tz(2013, 1, 1),
            'some_group': 'val1',
        })))
        assert_that(data, has_item(has_entries({
            '_count': 5,
            '_start_at': d_tz(2013, 2, 1),
            'some_group': 'val1',
        })))
        assert_that(data, has_item(has_entries({
            '_count': 2,
            '_start_at': d_tz(2013, 3, 1),
            'some_group': 'val2',
        })))
        assert_that(data, has_item(has_entries({
            '_count': 6,
            '_start_at': d_tz(2013, 4, 1),
            'some_group': 'val2',
        })))

    def test_period_group_query_adds_missing_periods_in_correct_order(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 14), '_count': 23},
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 21), '_count': 41},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 14), '_count': 31},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 28), '_count': 12},
        ]

        data = self.data_set.execute_query(
            Query.create(period=WEEK, group_by=['some_group'],
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

        query = Query.create(period=WEEK, group_by=['some_group'],
                             sort_by=["_count", "descending"])
        data = self.data_set.execute_query(query)

        assert_that(data, contains(
            has_entries({'some_group': 'val2'}),
            has_entries({'some_group': 'val1'}),
        ))

    def test_flattened_sorted_week_and_group_query(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 7), '_count': 1},
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 14), '_count': 5},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 7), '_count': 2},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 14), '_count': 6},
        ]

        query = Query.create(period=WEEK, group_by=['some_group'],
                             sort_by=["_count", "descending"], flatten=True)
        data = self.data_set.execute_query(query)

        assert_that(data, contains(
            has_entries({'_start_at': d_tz(2013, 1, 14)}),
            has_entries({'_start_at': d_tz(2013, 1, 14)}),
            has_entries({'_start_at': d_tz(2013, 1, 7)}),
            has_entries({'_start_at': d_tz(2013, 1, 7)}),
        ))

    def test_sorted_week_and_group_query_with_limit(self):
        self.mock_storage.execute_query.return_value = [
            {'some_group': 'val1', '_week_start_at': d(2013, 1, 7), '_count': 1},
            {'some_group': 'val2', '_week_start_at': d(2013, 1, 14), '_count': 5},
        ]

        query = Query.create(period=WEEK, group_by=['some_group'],
                             sort_by=["_count", "descending"], limit=1,
                             collect=[])
        data = self.data_set.execute_query(query)

        assert_that(data, contains(
            has_entries({'some_group': 'val2'})
        ))


class TestDataSet_create(BaseDataSetTest):

    def test_data_set_is_created_if_it_does_not_exist(self):
        self.mock_storage.data_set_exists.return_value = False
        self.data_set.create_if_not_exists()
        self.mock_storage.create_data_set.assert_called_with(
            'test_data_set', 0)

    def test_data_set_is_not_created_if_it_does_exist(self):
        self.mock_storage.data_set_exists.return_value = True
        self.data_set.create_if_not_exists()
        assert_that(self.mock_storage.create_data_set.called, is_(False))
