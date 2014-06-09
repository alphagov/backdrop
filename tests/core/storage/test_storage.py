import datetime

from hamcrest import assert_that, is_, less_than, contains, has_entries, \
    instance_of, has_entry, contains_inanyorder
from nose.tools import assert_raises
from freezegun import freeze_time

from backdrop.core.query import Query
from backdrop.core.errors import DataSetCreationError
from backdrop.core.records import add_period_keys
from backdrop.core.timeseries import DAY

from tests.support.test_helpers import d_tz


class BaseStorageTest(object):
    """
    A set of tests that a storage engine must pass in order to be considered
    valid.

    A concrete test class should be written extending from this test, filling
    out the setup and teardown methods.
    """

    def setup(self):
        raise NotImplemented()

    def teardown(self):
        raise NotImplemented()

    def _save_all(self, data_set, *records):
        self.engine.create_data_set(data_set, 0)
        for record in records:
            self.engine.save_record(data_set, record)

    def _save_all_with_periods(self, data_set_id, *records):
        records = map(add_period_keys, records)

        self._save_all(data_set_id, *records)

    def test_is_alive(self):
        assert_that(self.engine.alive(), is_(True))

    def test_does_not_exist(self):
        assert_that(self.engine.data_set_exists('foo_bar'), is_(False))

    def test_create(self):
        self.engine.create_data_set('foo_bar', 0)

        assert_that(self.engine.data_set_exists('foo_bar'), is_(True))

    def test_create_fails_if_it_already_exists(self):
        self.engine.create_data_set('foo_bar', 0)

        assert_raises(
            DataSetCreationError,
            self.engine.create_data_set, 'foo_bar', 0)

    def test_create_and_delete(self):
        self.engine.create_data_set('foo_bar', 0)
        self.engine.delete_data_set('foo_bar')

        assert_that(self.engine.data_set_exists('foo_bar'), is_(False))

    def test_simple_saving_and_finding(self):
        self._save_all('foo_bar', {'foo': 'bar'})

        assert_that(self.engine.execute_query('foo_bar', Query.create()),
                    contains(has_entries({'foo': 'bar'})))

    def test_saving_a_record_adds_an_updated_at(self):
        self._save_all('foo_bar', {'_id': 'first'})

        assert_that(self.engine.execute_query('foo_bar', Query.create()),
                    contains(has_entries({'_updated_at': instance_of(datetime.datetime)})))

    def test_get_last_updated(self):
        self.engine.create_data_set('foo_bar', 0)
        with freeze_time('2012-12-12'):
            self.engine.save_record('foo_bar', {'foo': 'first'})
        with freeze_time('2012-11-12'):
            self.engine.save_record('foo_bar', {'foo': 'second'})

        assert_that(self.engine.get_last_updated('foo_bar'),
                    is_(d_tz(2012, 12, 12)))

    def test_get_last_updated_returns_none_if_there_is_none(self):
        assert_that(self.engine.get_last_updated('foo_bar'), is_(None))

    def test_saving_a_record_with_an_id_updates_it(self):
        self._save_all('foo_bar',
                       {'_id': 'first', 'foo': 'bar'},
                       {'_id': 'first', 'foo': 'foo'})

        results = self.engine.execute_query('foo_bar', Query.create())

        assert_that(len(results), is_(1))
        assert_that(results, contains(has_entries({'foo': 'foo'})))

    def test_capped_data_set_is_capped(self):
        self.engine.create_data_set('foo_bar', 1)

        for i in range(100):
            self.engine.save_record('foo_bar', {'foo': i})

        assert_that(
            len(self.engine.execute_query('foo_bar', Query.create())),
            less_than(70))

    def test_empty_a_data_set(self):
        self._save_all('foo_bar',
                       {'foo': 'bar'}, {'bar': 'foo'})

        assert_that(len(self.engine.execute_query('foo_bar', Query.create())), is_(2))

        # TODO: fix inconsistency
        self.engine.empty_data_set('foo_bar')

        assert_that(len(self.engine.execute_query('foo_bar', Query.create())), is_(0))

    def test_datetimes_are_returned_as_utc(self):
        self._save_all('foo_bar',
                       {'_timestamp': datetime.datetime(2012, 8, 8)})

        results = self.engine.execute_query('foo_bar', Query.create())

        assert_that(results,
                    contains(
                        has_entries({'_timestamp': d_tz(2012, 8, 8)})))

    def test_query_with_filter(self):
        self._save_all('foo_bar', {'foo': 'bar'}, {'foo': 'foo'})

        results = self.engine.execute_query('foo_bar', Query.create(
            filter_by=[('foo', 'bar')]))

        assert_that(results,
                    contains(
                        has_entry('foo', 'bar')))

    def test_basic_query_with_time_limits(self):
        self._save_all('foo_bar',
                       {'_timestamp': d_tz(2012, 12, 12)},
                       {'_timestamp': d_tz(2012, 12, 14)},
                       {'_timestamp': d_tz(2012, 12, 11)})

        # start at
        results = self.engine.execute_query('foo_bar', Query.create(
            start_at=d_tz(2012, 12, 12, 13)))

        assert_that(results,
                    contains(
                        has_entry('_timestamp', d_tz(2012, 12, 14))))

        # end at
        results = self.engine.execute_query('foo_bar', Query.create(
            end_at=d_tz(2012, 12, 11, 13)))

        assert_that(results,
                    contains(
                        has_entry('_timestamp', d_tz(2012, 12, 11))))

        # both
        results = self.engine.execute_query('foo_bar', Query.create(
            start_at=d_tz(2012, 12, 11, 12),
            end_at=d_tz(2012, 12, 12, 12)))

        assert_that(results,
                    contains(
                        has_entry('_timestamp', d_tz(2012, 12, 12))))

    def test_basic_query_with_sort_ascending(self):
        self._save_all('foo_bar',
                       {'foo': 'mug'},
                       {'foo': 'book'})

        results = self.engine.execute_query('foo_bar', Query.create(
            sort_by=('foo', 'ascending')))

        assert_that(results,
                    contains(
                        has_entry('foo', 'book'),
                        has_entry('foo', 'mug')))

    def test_basic_query_with_sort_descending(self):
        self._save_all('foo_bar',
                       {'foo': 'mug'},
                       {'foo': 'book'})

        results = self.engine.execute_query('foo_bar', Query.create(
            sort_by=('foo', 'descending')))

        assert_that(results,
                    contains(
                        has_entry('foo', 'mug'),
                        has_entry('foo', 'book')))

    def test_basic_query_with_limit(self):
        self._save_all('foo_bar', {'foo': 'bar'}, {'foo': 'foo'})

        results = self.engine.execute_query('foo_bar', Query.create(limit=1))

        assert_that(len(list(results)), is_(1))

    # !GROUPED!
    def test_query_grouped_by_field(self):
        self._save_all('foo_bar',
                       {'foo': 'foo'}, {'foo': 'foo'},
                       {'foo': 'bar'})

        results = self.engine.execute_query('foo_bar', Query.create(
            group_by='foo'))

        assert_that(results,
                    contains_inanyorder(
                        has_entries({'foo': 'bar', '_count': 1}),
                        has_entries({'foo': 'foo', '_count': 2})))

    def test_query_grouped_by_period(self):
        self._save_all_with_periods(
            'foo_bar',
            {'_timestamp': d_tz(2012, 12, 12, 12)},
            {'_timestamp': d_tz(2012, 12, 12, 15)},
            {'_timestamp': d_tz(2012, 12, 13, 12)})

        results = self.engine.execute_query('foo_bar', Query.create(
            period=DAY))

        assert_that(results,
                    contains_inanyorder(
                        has_entries(
                            {'_day_start_at': d_tz(2012, 12, 12), '_count': 2}),
                        has_entries(
                            {'_day_start_at': d_tz(2012, 12, 13), '_count': 1})))

    def test_group_by_field_and_period(self):
        self._save_all_with_periods(
            'foo_bar',
            {'_timestamp': d_tz(2012, 12, 12), 'foo': 'foo'},
            {'_timestamp': d_tz(2012, 12, 13), 'foo': 'foo'},
            {'_timestamp': d_tz(2012, 12, 12), 'foo': 'bar'},
            {'_timestamp': d_tz(2012, 12, 12), 'foo': 'bar'})

        results = self.engine.execute_query('foo_bar', Query.create(
            group_by='foo', period=DAY))

        assert_that(results,
                    contains_inanyorder(
                        has_entries({'_day_start_at': d_tz(2012, 12, 12), 'foo': 'foo', '_count': 1}),
                        has_entries({'_day_start_at': d_tz(2012, 12, 12), 'foo': 'bar', '_count': 2}),
                        has_entries({'_day_start_at': d_tz(2012, 12, 13), 'foo': 'foo', '_count': 1})))

    def test_group_query_with_collect_fields(self):
        self._save_all('foo_bar',
                       {'foo': 'foo', 'c': 1}, {'foo': 'foo', 'c': 3},
                       {'foo': 'bar', 'c': 2})

        results = self.engine.execute_query('foo_bar', Query.create(
            group_by='foo', collect=[('c', 'sum')]))

        assert_that(results,
                    contains_inanyorder(
                        has_entries({'foo': 'bar', 'c': [2]}),
                        has_entries({'foo': 'foo', 'c': [1, 3]})))

    def test_group_and_collect_with_false_values(self):
        self._save_all('foo_bar',
                       {'foo': 'one', 'bar': False},
                       {'foo': 'two', 'bar': True},
                       {'foo': 'two', 'bar': True},
                       {'foo': 'one', 'bar': False})

        results = self.engine.execute_query('foo_bar', Query.create(
            group_by='foo', collect=[('bar', 'sum')]))

        assert_that(results,
                    contains_inanyorder(
                        has_entries({'bar': [False, False]}),
                        has_entries({'bar': [True, True]})))

    def test_group_query_ignores_records_without_grouping_key(self):
        self._save_all('foo_bar',
                       {'foo': 'one'},
                       {'foo': 'two'},
                       {'bar': 'one'})

        results = self.engine.execute_query('foo_bar', Query.create(
            group_by='foo'))

        assert_that(results,
                    contains_inanyorder(
                        has_entries({'foo': 'one', '_count': 1}),
                        has_entries({'foo': 'two', '_count': 1})))
