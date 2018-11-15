import sched
import time
from functools import wraps
from threading import Thread


def daemon(func):
    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.daemon = True
        func_hl.start()
        return func_hl
    return async_func


def schedule(interval):
    def decorator(func):
        def periodic(scheduler, sched_interval, action, actionargs=()):
            scheduler.enter(sched_interval, 1, periodic,
                            (scheduler, sched_interval, action, actionargs))
            action(*actionargs)

        @wraps(func)
        def wrap(*args, **kwargs):
            scheduler = sched.scheduler(time.time, time.sleep)
            periodic(scheduler, interval, func)
            scheduler.run()
        return wrap
    return decorator
