"""Development

This module contains functions to help with the development of lexor.

"""

import os
import sys
import optparse
import datetime
from os.path import dirname, expanduser, splitext, abspath, basename
from lexor.__version__ import get_version

__all__ = [
    'check_directory', 'get_date', 'open_file', 'Template',
    'error'
]


def error(msg):
    """Print a message to the standard error stream and exit. """
    sys.stderr.write(msg)
    sys.exit(2)


def warn(msg):
    """Print a message to the standard error stream. """
    sys.stderr.write(msg)


def init(**keywords):
    """The following are the valid keywords to initialize a style:

    version: Must be in form
             (major, minor, micro, alpha/beta/rc/final, #)
    lang
    [to_lang]
    type
    description
    author
    author_email
    [url]
    *path

    *Note that the keyword path must be present and must be set to
    __file__. """
    valid_keys = ['version', 'lang', 'to_lang', 'type', 'description',
                  'author', 'author_email', 'url', 'path', 'license']
    info = dict()
    for key in valid_keys:
        info[key] = None
    for key in keywords.keys():
        if key not in valid_keys:
            error("ERROR: Valid keys for lexor.dev.init are %s" % valid_keys)
        else:
            info[key] = keywords[key]
    info['style'] = splitext(basename(info['path']))[0]
    info['style'] = info['style'].split('-')[0]
    info['ver'] = get_version(info['version'])
    return info


def check_directory(path):
    """Checks if a directory exists and prints a status message. """
    if os.path.exists(path):
        print 'Existing directory: %s' % path
    else:
        print 'Creating directory: %s' % path
        os.makedirs(path)


def get_date():
    """Return the current date as a string. """
    date = datetime.datetime.now()
    return date.strftime('%b %d, %Y')


def open_file(path):
    """Open file in an editor. """
    app = os.environ.get('EDITOR', None)
    if app:
        cmd = '%s "%s" > /dev/null' % (app, path)
    else:
        info = os.uname()
        if info[0] == 'Darwin':
            cmd = 'open -a /Applications/TextMate.app "%s"' % path
        elif info[0] == 'Linux':
            cmd = 'emacs "%s"' % path
        else:
            error('ERROR: unknown operating system.\n')
    os.system(cmd)


class Template(object):
    """Basic structure to read and write templates. """
    def __init__(self, filename):
        with open(filename, 'r') as tfn:
            self.text = tfn.read()
            self.var = dict()

    def __setitem__(self, var, val):
        """x.__setitem__(var) = val <==> x[var] = val """
        self.var[var] = val

    def __getitem__(self, var):
        """x.__setitem__(var) <==> x[var] """
        return self.var[var]

    def __delitem__(self, var):
        """x.__delitem__(var) <==> del x[var] """
        del self.var[var]

    def __len__(self):
        """x.__len__() <==> len(x)"""
        return len(self.var)

    def __str__(self):
        """x.__str__() <==> str(x)"""
        tmp = self.text
        for key in self.var:
            tmp = tmp.replace('$(%s)' % key, self.var[key])
            tmp = tmp.replace('${UPPER}(%s)' % key, self.var[key].upper())
        return tmp
