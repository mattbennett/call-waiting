import time
from threading import Thread

import pytest
from call_waiting import patch_wait
from mock import Mock, call, patch


@pytest.yield_fixture
def forever():
    value = [True]
    yield value
    value.pop()


class TestPatchWaitUseCases(object):

    def test_wait_for_specific_result(self, forever):

        class Counter(object):
            value = 0

            def count(self):
                self.value += 1
                return self.value

        counter = Counter()

        def count_forever():
            while forever:
                counter.count()
                time.sleep(0)

        def cb(args, kwargs, res, exc_info):
            if res == 10:
                return True
            return False

        with patch_wait(counter, 'count', callback=cb) as result:
            Thread(target=count_forever).start()

        assert result.get() == 10

    def test_wait_until_called_with_argument(self, forever):

        class CounterWithSkipTo(object):
            value = 0

            def count(self):
                self.value += 1
                return self.value

            def skip_to(self, skip_to):
                self.value = skip_to
                return self.value

        counter = CounterWithSkipTo()

        def increment_forever():
            while forever:
                counter.skip_to(counter.value + 1)
                time.sleep(0)

        def cb(args, kwargs, res, exc_info):
            if args == (10,):
                return True
            return False

        with patch_wait(counter, 'skip_to', callback=cb) as result:
            Thread(target=increment_forever).start()

        assert result.get() == 10

    def test_wait_until_raises(self, forever):

        class LimitExceeded(Exception):
            pass

        class CounterWithLimit(object):
            def __init__(self, limit):
                self.value = 0
                self.limit = limit

            def count(self):
                self.value += 1
                if self.value >= self.limit:
                    raise LimitExceeded(self.limit)
                return self.value

        limit = 10
        counter = CounterWithLimit(limit)

        def count_forever():
            while forever:
                counter.count()
                time.sleep(0)

        def cb(args, kwargs, res, exc_info):
            if exc_info is not None:
                return True
            return False

        with patch_wait(counter, 'count', callback=cb) as result:
            Thread(target=count_forever).start()

        with pytest.raises(LimitExceeded):
            result.get()

    def test_wait_until_stops_raising(self, forever):

        class ThresholdNotReached(Exception):
            pass

        class CounterWithThreshold(object):

            def __init__(self, threshold):
                self.value = 0
                self.threshold = threshold

            def count(self):
                self.value += 1
                if self.value < self.threshold:
                    raise ThresholdNotReached(self.threshold)
                return self.value

        threshold = 10
        counter = CounterWithThreshold(threshold)

        def count_forever():
            while forever:
                try:
                    counter.count()
                except ThresholdNotReached:
                    pass
                time.sleep(0)

        def cb(args, kwargs, res, exc_info):
            if exc_info is not None:
                return False
            return True

        with patch_wait(counter, 'count', callback=cb) as result:
            Thread(target=count_forever).start()

        assert result.get() == threshold


class TestPatchWait(object):

    def test_direct(self):

        class Echo(object):

            def upper(self, arg):
                return arg.upper()

        echo = Echo()
        arg = "hello"

        with patch_wait(echo, 'upper'):
            res = echo.upper(arg)
            assert res == "HELLO"

    def test_indirect(self):

        class Echo(object):

            def proxy(self, arg):
                return self.upper(arg)

            def upper(self, arg):
                return arg.upper()

        echo = Echo()
        arg = "hello"

        with patch_wait(echo, 'upper'):
            assert echo.proxy(arg) == "HELLO"

    def test_result(self):

        class Echo(object):

            def upper(self, arg):
                return arg.upper()

        echo = Echo()
        arg = "hello"

        with patch_wait(echo, 'upper') as result:
            res = echo.upper(arg)

        assert result.get() == res

    def test_result_not_ready(self):

        class Echo(object):

            def upper(self, arg):
                return arg.upper()

        echo = Echo()
        arg = "hello"

        with patch_wait(echo, 'upper') as result:
            assert result.get() is None  # not ready
            res = echo.upper(arg)

        assert result.get() == res

    def test_wrapped_method_raises(self):

        class EchoException(Exception):
            pass

        class Echo(object):

            def error(self):
                raise EchoException("error!")

        echo = Echo()

        with patch_wait(echo, 'error'):
            with pytest.raises(EchoException):
                echo.error()

    def test_result_get_raises(self):

        class EchoException(Exception):
            pass

        class Echo(object):

            def error(self):
                raise EchoException("error!")

        echo = Echo()

        with patch_wait(echo, 'error') as result:
            with pytest.raises(EchoException):
                echo.error()

            with pytest.raises(EchoException):
                result.get()

    def test_callback(self):

        class Echo(object):

            def upper(self, arg):
                return arg.upper()

        echo = Echo()
        arg = "hello"

        callback = Mock()
        callback.return_value = True

        with patch_wait(echo, 'upper', callback):
            res = echo.upper(arg)
            assert res == "HELLO"

        assert callback.called
        assert callback.call_args_list == [call((arg,), {}, res, None)]

    def test_callback_multiple_calls(self):

        class Echo(object):

            count = 0

            def upper(self, arg):
                self.count += 1
                return "{}-{}".format(arg.upper(), self.count)

        echo = Echo()
        arg = "hello"

        callback = Mock()
        callback.side_effect = [False, True]

        with patch_wait(echo, 'upper', callback):
            res1 = echo.upper(arg)
            assert res1 == "HELLO-1"
            res2 = echo.upper(arg)
            assert res2 == "HELLO-2"

        assert callback.called
        assert callback.call_args_list == [
            call((arg,), {}, res1, None),
            call((arg,), {}, res2, None),
        ]

    def test_callback_with_exception(self):

        class EchoException(Exception):
            pass

        class Echo(object):

            def error(self):
                raise exc

        echo = Echo()
        exc = EchoException("error!")

        callback = Mock()
        callback.return_value = True

        with patch_wait(echo, 'error', callback):
            with pytest.raises(EchoException):
                echo.error()

        assert callback.called
        assert callback.call_args_list == [call((), {}, None, (EchoException, exc, ANY))]

    def test_callback_with_exception_multiple_calls(self):

        class EchoException(Exception):
            pass

        class Echo(object):

            def error(self):
                raise exc

        echo = Echo()
        exc = EchoException("error!")

        callback = Mock()
        callback.side_effect = [False, True]

        with patch_wait(echo, 'error', callback):
            with pytest.raises(EchoException):
                echo.error()
            with pytest.raises(EchoException):
                echo.error()

        assert callback.called
        assert callback.call_args_list == [
            call((), {}, None, (EchoException, exc, ANY)),
            call((), {}, None, (EchoException, exc, ANY))
        ]

    def test_with_new_thread(self):

        class Echo(object):

            def proxy(self, arg):
                Thread(target=self.upper, args=(arg,)).start()

            def upper(self, arg):
                return arg.upper()

        echo = Echo()
        arg = "hello"

        callback = Mock()
        callback.return_value = True

        with patch_wait(echo, 'upper', callback):
            res = echo.proxy(arg)
            assert res is None

        assert callback.called
        assert callback.call_args_list == [call((arg,), {}, "HELLO", None)]

    def test_target_as_mock(self):

        class Klass(object):

            def __init__(self):
                self.attr = "value"

            def method(self):
                return self.attr.upper()

        instance = Klass()

        with patch.object(instance, 'attr') as patched_attr:

            with patch_wait(patched_attr, 'upper'):
                instance.method()

            assert patched_attr.upper.called
            assert instance.attr.upper.called
