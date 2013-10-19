"""Develop

Routine to append a path to the develop section in the configuration
file.

"""

import os
from imp import load_source
from lexor.dev import error
from lexor.config import read_config, write_config

__all__ = ['run']


def run(argp):
    """Append the path to the develop section in the configuration
    file. """
    path = os.path.abspath(argp.path)
    if '.py' not in path:
        path = '%s.py' % path
    try:
        mod = load_source("tmp-mod", path)
    except IOError:
        error("ERROR: Not a valid module.")
    if mod.INFO['type'] == 'converter':
        key = '%s.%s.%s.%s' % (mod.INFO['lang'], mod.INFO['type'],
                               mod.INFO['to_lang'], mod.INFO['style'])
    else:
        key = '%s.%s.%s' % (mod.INFO['lang'], mod.INFO['type'],
                            mod.INFO['style'])
    config = read_config()
    if 'develop' in config:
        config['develop'][key] = path
    else:
        config.add_section('develop')
        config['develop'][key] = path
    write_config(config)
