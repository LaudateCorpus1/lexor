"""Development

This module contains functions to help with the development of lexor.

"""

import os
import sys
import optparse
import datetime
from os.path import dirname, expanduser, splitext, abspath, basename
from lexor.__version__ import get_version


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
