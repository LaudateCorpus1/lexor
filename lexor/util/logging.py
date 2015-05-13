from inspect import currentframe, getframeinfo
from datetime import datetime


class LogMessage(object):

    def __init__(self, fname, lineno, kind, msg, exception=None):
        self.date = datetime.now()
        self.file_name = fname
        self.line_number = lineno
        self.kind = kind
        self.message = msg
        self.exception = exception

    def __repr__(self):
        return '[%s][%s:%d] => %s' % (
            self.kind, self.file_name, self.line_number, self.message
        )


class Logger(object):

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
        self.history.append(LogMessage(
            fname, lineno, kind, msg % args, exception
        ))

    def log(self, msg, *args, **kwargs):
        self._push(currentframe(), 'log', msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._push(currentframe(), 'debug', msg, *args, **kwargs)

    def __repr__(self):
        return '\n'.join([repr(x) for x in self.history])


LOG = Logger()
