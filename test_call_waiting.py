import time
from threading import Thread

from call_waiting import patch_wait, wrap_wait
from mock import Mock, call, patch


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
        assert callback.call_args_list == [call(arg)]

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
            res = echo.upper(arg)
            assert res == "HELLO-1"
            res = echo.upper(arg)
            assert res == "HELLO-2"

        assert callback.called
        assert callback.call_args_list == [call(arg), call(arg)]

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
        assert callback.call_args_list == [call(arg)]

    def test_with_sleep(self):

        class Echo(object):

            def proxy(self, arg):
                time.sleep(0.1)
                self.upper(arg)

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
        assert callback.call_args_list == [call(arg)]

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


class TestWrapWait(object):

    def test_function(self):

        def echo(arg):
            return arg

        callback = Mock()
        callback.return_value = True

        arg = "hello"
        with wrap_wait(echo, callback) as wrapped:
            res = wrapped(arg)
            assert res == "hello"

        assert callback.called
        assert callback.call_args_list == [call(arg)]

    def test_method(self):

        class Echo(object):

            def upper(self, arg):
                return arg.upper()

        echo = Echo()
        arg = "hello"

        callback = Mock()
        callback.return_value = True

        with wrap_wait(echo.upper, callback) as wrapped:
            res = wrapped(arg)
            assert res == "HELLO"

        assert callback.called
        assert callback.call_args_list == [call(arg)]

    def test_no_callback(self):

        def echo(arg):
            return arg

        arg = "hello"
        with wrap_wait(echo) as wrapped:
            res = wrapped(arg)
            assert res == "hello"

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

        with wrap_wait(echo.upper, callback) as wrapped:
            res = wrapped(arg)
            assert res == "HELLO-1"
            res = wrapped(arg)
            assert res == "HELLO-2"

        assert callback.called
        assert callback.call_args_list == [call(arg), call(arg)]
