import cProfile
import cPickle as pickle

from hamcrest import assert_that, equal_to

from backdrop.core.timeseries import fill_group_by_permutations


def run_and_assert(base_path):
    args = pickle.load(open('{}.args'.format(base_path)))
    kwargs = pickle.load(open('{}.kwargs'.format(base_path)))
    stored_result = pickle.load(open('{}.result'.format(base_path)))

    profile = cProfile.Profile()
    profile.enable()
    result = fill_group_by_permutations(*args, **kwargs)
    profile.disable()
    profile.print_stats()

    assert_that(result, equal_to(stored_result))


def test_filling_gaps_single_group():
    run_and_assert('./tests/fixtures/perf/lpa-journey')


def test_filling_gaps_multi_group():
    run_and_assert('./tests/fixtures/perf/multi-group')
