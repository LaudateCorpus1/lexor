"""Development

This module contains functions to help with the development of lexor.

"""

import os
import sys
import optparse
import datetime
from os.path import dirname, expanduser, splitext, abspath, basename
from lexor.__version__ import get_version



def check_directory(path):
    """Checks if a directory exists and prints a status message. """
    if os.path.exists(path):
        print 'Existing directory: %s' % path
    else:
        print 'Creating directory: %s' % path
        os.makedirs(path)

