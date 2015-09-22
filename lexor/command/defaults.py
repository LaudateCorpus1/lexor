"""
Print the default values for each command.

"""
import textwrap
from lexor.command import import_mod
from lexor.command import config, LexorError


DESC = """
View default values for a subcommand.

"""


def add_parser(subp, fclass):
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Add a parser to the main subparser.
    """
    tmpp = subp.add_parser('defaults', help='print default values',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('name', type=str, help='subcommand name')


def run():
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Run the command.
    """
    arg = config.CONFIG['arg']
    name = arg.name
    try:
        mod = import_mod('lexor.command.%s' % name)
    except ImportError:
        raise LexorError('invalid command: %r' % name)
    if hasattr(mod, 'DEFAULTS'):
        for key, val in mod.DEFAULTS.iteritems():
            print '%s = %r' % (key, val)
    else:
        print 'NO DEFAULTS'
