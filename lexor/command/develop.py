"""Develop

Routine to append a path to the develop section in the configuration
file.

"""

import os
import textwrap
from imp import load_source
from lexor.command import error
from lexor.command import config

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
    cfg_file = config.read_config()
    arg = config.CONFIG['arg']
    path = os.path.abspath(arg.path)
    if '.py' not in path:
        path = '%s.py' % path
    rel_path = path[len(config.CONFIG['path'])+1:]
    try:
        mod = load_source("tmp-mod", path)
    except IOError:
        error("ERROR: Not a valid module.\n")
    if not hasattr(mod, 'INFO'):
        error("ERROR: module does not have `INFO`\n")
    if mod.INFO['type'] == 'converter':
        key = '%s.%s.%s.%s' % (mod.INFO['lang'], mod.INFO['type'],
                               mod.INFO['to_lang'], mod.INFO['style'])
    else:
        key = '%s.%s.%s' % (mod.INFO['lang'], mod.INFO['type'],
                            mod.INFO['style'])
    if 'develop' in cfg_file:
        if key in cfg_file['develop']:
            if cfg_file['develop'][key] == rel_path:
                error('%s is already begin developed from %s\n' % (key, path))
        cfg_file['develop'][key] = rel_path
    else:
        cfg_file.add_section('develop')
        cfg_file['develop'][key] = rel_path
    print('%s --> %s' % (key, rel_path))
    config.write_config(cfg_file)
