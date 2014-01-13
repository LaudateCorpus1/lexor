"""Defaults

Print the default values for each command.

"""

import textwrap
from lexor.command import import_mod, error
import lexor.command.config as config

DESC = """

View default values for a subcommand.

"""


def add_parser(subp, fclass):
    "Add a parser to the main subparser. "
    tmpp = subp.add_parser('defaults', help='print default values',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('name', type=str,
                      help='subcommand name')


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
