"""Defaults

Print the default values for each command.

"""

import textwrap
import os.path as pt
from glob import iglob
from lexor.command import import_mod, error
from lexor.command import config

DESC = """

View default values for a subcommand.

"""


def name_completer(**_):
    """var completer. """
    rootpath = pt.split(pt.abspath(__file__))[0]
    mod_names = [pt.split(name)[1][:-3]
                 for name in iglob('%s/*.py' % rootpath)]
    mod_names.sort()
    del mod_names[0]
    return mod_names


def add_parser(subp, fclass):
    "Add a parser to the main subparser. "
    tmpp = subp.add_parser('defaults', help='print default values',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('name', type=str,
                      help='subcommand name').completer = name_completer


def run():
    """Run command. """
    arg = config.CONFIG['arg']
    name = arg.name
    try:
        mod = import_mod('lexor.command.%s' % name)
    except ImportError:
        error('ERROR: invalid command: %r\n' % name)
    if hasattr(mod, 'DEFAULTS'):
        for key, val in mod.DEFAULTS.iteritems():
            print '%s = %r' % (key, val)
    else:
        print 'NO DEFAULTS'
