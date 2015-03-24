"""
Collection of functions to create lexor's command line utility.

"""

import sys
import lexor
from dateutil import parser
from datetime import datetime
from subprocess import Popen, PIPE
from inspect import currentframe, getframeinfo


def debug(msg, level=1):
    """Prints a message to the standard error stream. The message
    will only be displayed if the ``CONFIG`` global variable in the
    config module is set to a level greater than or equal to the
    level specified in the parameter of this function. """
    if lexor.CONFIG['debug'] >= level:
        cfr = currentframe()
        fname = getframeinfo(cfr.f_back).filename.split('lexor/lexor/')[1]
        lineno = cfr.f_back.f_lineno
        msg = 'debug%d: [%s:%d] => %s\n' % (level, fname, lineno, msg)
        sys.stderr.write(msg)


def error(msg):
    "Print a message to the standard error stream and exit. "
    sys.stderr.write(msg)
    sys.exit(2)


def warn(msg):
    "Print a message to the standard error. "
    sys.stderr.write(msg)


def disp(msg):
    "Print a message to the standard output. "
    sys.stdout.write(msg)


def import_mod(name):
    "Return a module by string. "
    mod = __import__(name)
    for sub in name.split(".")[1:]:
        mod = getattr(mod, sub)
    return mod


def exec_cmd(cmd, verbose=False):
    """Run a subprocess and return its output, errors and return code
    when `verbose` is set to False. Otherwise execute the command
    `cmd`. """
    if verbose:
        out = sys.stdout
        err = sys.stderr
    else:
        out = PIPE
        err = PIPE
    process = Popen(cmd, shell=True,
                    universal_newlines=True, executable="/bin/bash",
                    stdout=out, stderr=err)
    out, err = process.communicate()
    return out, err, process.returncode


def date(short=False):
    "Return the current date as a string. "
    if isinstance(short, str):
        now = parser.parse(short)
        return now.strftime("%a %b %d, %Y %r")
    now = datetime.now()
    if not short:
        return now.strftime("%a %b %d, %Y %r")
    return now.strftime("%Y-%m-%d-%H-%M-%S")


class ConfigError(Exception):
    """Raised when a lexor configuration file is not found. """
    pass


class LexorError(Exception):
    """Every known error should be raised via this exception. """
    pass
