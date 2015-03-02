import cProfile
import time


def profiler(prefix=''):
    def profiler_wrapper(func):   
        def profiled_func(*args, **kwargs): 
            profile = cProfile.Profile()    

            filename = '/tmp/{}-{}.profile'.format(
                prefix,
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
    return profiler_wrapper 
