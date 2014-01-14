"""Develop

Routine to append a path to the develop section in the configuration
file.

"""

import os
import textwrap
from imp import load_source
from lexor.command import error
import lexor.command.config as config

DESC = """
Append the path to the develop section in a configuration file.

"""


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('develop', help='develop a style',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('path', type=str,
                      help='path to the style to develop')


def run():
    """Append the path to the develop section in the configuration
    file. """
    arg = config.CONFIG['arg']
    path = os.path.abspath(arg.path)
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
    cfg_file = config.read_config()
    if 'develop' in cfg_file:
        cfg_file['develop'][key] = path
    else:
        cfg_file.add_section('develop')
        cfg_file['develop'][key] = path
    print('%s --> %s' % (key, path))
    config.write_config(cfg_file)
