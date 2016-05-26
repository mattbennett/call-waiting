import sys
from contextlib import contextmanager
from threading import Semaphore

from mock import patch


@contextmanager
def patch_wait(obj, target, callback=None):

    class WaitResult(object):
        res = None
        exc_info = None

        @property
        def has_result(self):
            return self.res is not None or self.exc_info is not None

        def send(self, res, exc_info):
            if not self.has_result:
                self.res = res
                self.exc_info = exc_info

        def get(self):
            if self.exc_info is not None:
                raise self.exc_info[1]
            return self.res

    sem = Semaphore(0)
    result = WaitResult()

    unpatched = getattr(obj, target)

    def maybe_release(args, kwargs, res, exc_info):
        should_release = True
        if callable(callback):
            should_release = callback(args, kwargs, res, exc_info)

        if should_release:
            result.send(res, exc_info)
            sem.release()

    def wraps(*args, **kwargs):
        res = None
        exc_info = None
        try:
            res = unpatched(*args, **kwargs)
        except Exception:
            exc_info = sys.exc_info()

        maybe_release(args, kwargs, res, exc_info)

        if exc_info is not None:
            raise exc_info[1]
        return res

    with patch.object(obj, target, new=wraps):
        yield result
        sem.acquire()
