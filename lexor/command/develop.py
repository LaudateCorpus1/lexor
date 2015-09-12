"""Develop

Routine to append a path to the develop section in the configuration
file.

"""

import os
import textwrap
from imp import load_source
from lexor.command import config, LexorError
from lexor.util.logging import L

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
        msg = 'not a valid module.'
        L.error(msg)
        raise LexorError(msg)
    if not hasattr(mod, 'INFO'):
        msg = 'module does not have `INFO`'
        L.error(msg)
    if mod.INFO['type'] == 'converter':
        key = '%s.%s.%s.%s' % (mod.INFO['lang'], mod.INFO['type'],
                               mod.INFO['to_lang'], mod.INFO['style'])
    else:
        key = '%s.%s.%s' % (mod.INFO['lang'], mod.INFO['type'],
                            mod.INFO['style'])
    if 'develop' in cfg_file:
        if key in cfg_file['develop']:
            if cfg_file['develop'][key] == rel_path:
                msg = '%s is already begin developed from %s'
                msg = msg % (key, path)
                L.error(msg)
                raise LexorError(msg)
        cfg_file['develop'][key] = rel_path
    else:
        cfg_file.add_section('develop')
        cfg_file['develop'][key] = rel_path
    print('%s --> %s' % (key, rel_path))
    config.write_config(cfg_file)
