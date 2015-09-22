"""logging

The logging module provides a basic object to store information about
an event and a ``Logger`` which creates these events. The module
provides the global variable ``L`` which may be used to record events
during the usage of lexor. For more information on ``L`` see the
documentation on :class:`~.Logger`.

"""

import sys
import traceback
from datetime import datetime
from inspect import currentframe, getframeinfo


class LogMessage(object):
    """Simple object to store an event information."""

    def __init__(self, fname, func_name, lineno, kind, msg, lvl, exception=None):
        self.date = datetime.now()
        self.file_name = fname
        self.func_name = func_name
        self.line_number = lineno
        self.kind = kind
        self.message = msg
        self.exception = exception
        self.exceptionTraceback = None
        self.level = lvl
        if exception is not None:
            self.exceptionTraceback = traceback.format_exc()


    def __repr__(self):
        msg = '[%s][%s][%s:%d] => %s' % (
            self.kind, self.func_name, self.file_name,
            self.line_number, self.message
        )
        if self.exception is not None:
            msg += '\n' + self.exceptionTraceback
        return msg


class Logger(object):
    """Provides methods function to tag an event. """

    def __init__(self):
        self.on = False
        self.history = []

    def enable(self):
        self.on = True

    def disable(self):
        self.on = False

    def _push(self, cfr, kind, msg, *args, **kwargs):
        f_back = cfr.f_back
        fname = getframeinfo(f_back).filename
        parts = fname.split('lexor/lexor/')
        if len(parts) == 2:
            fname = parts[1]
        lineno = f_back.f_lineno
        func_name = f_back.f_code.co_name
        exception = kwargs.get('exception', None)
        level = kwargs.get('level', '=')
        self.history.append(LogMessage(
            fname, func_name, lineno,
            kind, msg % args, level, exception
        ))

    def log(self, msg, *args, **kwargs):
        if self.on:
            self._push(currentframe(), 'LOG', msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if self.on:
            self._push(currentframe(), 'INFO', msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        if self.on:
            self._push(currentframe(), 'DEBUG', msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._push(currentframe(), 'WARN', msg, *args, **kwargs)
        sys.stderr.write('%r\n' % self.history[-1])

    def error(self, msg, *args, **kwargs):
        self._push(currentframe(), 'ERROR', msg, *args, **kwargs)
        if not self.on:
            self.history[-1].exception = None
        sys.stderr.write('%r\n' % self.history[-1])

    def msg(self, kind, msg, *args, **kwargs):
        if self.on:
            self._push(currentframe(), kind, msg, *args, **kwargs)

    def __repr__(self):
        return '\n'.join([repr(x) for x in self.history])


L = Logger()
