import cProfile
import time

import cPickle as pickle


def pickle_func_io(func):
    def wrapped_fn(*args, **kwargs):
        base_path = '/tmp/{}'.format(str(time.time()))
        pickle.dump(args, open('{}.args'.format(base_path), 'wb'))
        pickle.dump(kwargs, open('{}.kwargs'.format(base_path), 'wb'))

        result = func(*args, **kwargs)

        pickle.dump(result, open('{}.result'.format(base_path), 'wb'))

        return result

    return wrapped_fn


def do_profile(prefix='', keys=[]):
    def do_profile_wrapper(func):
        def profiled_func(*args, **kwargs):
            profile = cProfile.Profile()

            if len(keys) > 0:
                suffix = '-' + \
                    '-'.join([kwargs.get(k, 'no_val') for k in keys])
            else:
                suffix = ''

            filename = '/tmp/{}{}-{}.profile'.format(
                prefix,
                suffix,
                str(time.time())
            )

            try:
                profile.enable()
                result = func(*args, **kwargs)
                profile.disable()
                return result
            finally:
                profile.dump_stats(filename)
        return profiled_func
    return do_profile_wrapper
