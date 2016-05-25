from contextlib import contextmanager
from threading import Semaphore


def maybe_release(sem, callback, args, kwargs):
    should_release = True
    if callable(callback):
        should_release = callback(*args, **kwargs)

    if should_release:
        sem.release()


@contextmanager
def patch_wait(obj, target, callback=None):
    from mock import patch

    sem = Semaphore(0)
    unpatched = getattr(obj, target)

    def wraps(*args, **kwargs):
        res = unpatched(*args, **kwargs)
        maybe_release(sem, callback, args, kwargs)
        return res

    with patch.object(obj, target, wraps=wraps):
        yield
        sem.acquire()
