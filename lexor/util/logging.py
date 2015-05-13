"""logging

The logging module provides a basic object to store information about
an event and a ``Logger`` which creates these events. The module
provides the global variable ``L`` which may be used to record events
during the usage of lexor. For more information on ``L`` see the
documentation on :class:`~.Logger`.

"""

from inspect import currentframe, getframeinfo
from datetime import datetime


class LogMessage(object):
    """Simple object to store an event information."""

    def __init__(self, fname, lineno, kind, msg, lvl, exception=None):
        self.date = datetime.now()
        self.file_name = fname
        self.line_number = lineno
        self.kind = kind
        self.message = msg
        self.exception = exception
        self.level = lvl

    def __repr__(self):
        return '[%s][%s:%d] => %s' % (
            self.kind, self.file_name, self.line_number, self.message
        )


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
        fname = getframeinfo(cfr.f_back).filename
        fname = fname.split('lexor/lexor/')[1]
        lineno = cfr.f_back.f_lineno
        exception = kwargs.get('exception', None)
        level = kwargs.get('level', '=')
        self.history.append(LogMessage(
            fname, lineno, kind, msg % args, level, exception
        ))

    def log(self, msg, *args, **kwargs):
        self._push(currentframe(), 'log', msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._push(currentframe(), 'info', msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._push(currentframe(), 'debug', msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._push(currentframe(), 'warn', msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._push(currentframe(), 'error', msg, *args, **kwargs)

    def msg(self, kind, msg, *args, **kwargs):
        self._push(currentframe(), kind, msg, *args, **kwargs)

    def __repr__(self):
        return '\n'.join([repr(x) for x in self.history])


L = Logger()
