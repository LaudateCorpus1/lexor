"""Command

Collection of functions to create lexor's command line utility.

"""

import sys
from dateutil import parser
from datetime import datetime
from subprocess import Popen, PIPE


def error(msg):
    "Print a message to the standard error stream and exit. "
    sys.stderr.write(msg)
    sys.exit(2)


def warn(msg):
    "Print a message to the standard error "
    sys.stderr.write(msg)


def import_mod(name):
    "Return a module by string. "
    mod = __import__(name)
    for sub in name.split(".")[1:]:
        mod = getattr(mod, sub)
    return mod


def exec_cmd(cmd, verbose=False):
    "Run a subprocess and return its output and errors. "
    if verbose:
        out = sys.stdout
        err = sys.stderr
    else:
        out = PIPE
        err = PIPE
    process = Popen(cmd, shell=True, stdout=out, stderr=err)
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
