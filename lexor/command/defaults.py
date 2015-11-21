"""
Print the default values for each command.

"""
import textwrap
from lexor.command import import_mod, disp
from lexor.command import config, LexorError
from lexor.command.lang import get_style_module


DESC = """
view default values for a subcommand or lexor style.

The style format must be

    [lang]-[type]-[style]

or

    [lang]-converter-[to_lang]-[style]

where [type] can be either parser or writer.

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
    tmpp.add_argument('name', type=str, help='subcommand/style name')


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
        try:
            items = name.split('-')
            lang = items[0]
            type_ = items[1]
            if items[1] == 'converter':
                to_lang = items[2]
                style = items[3]
            else:
                to_lang = None
                style = items[2]
            mod = get_style_module(type_, lang, style, to_lang)
        except ImportError:
            raise LexorError('invalid command/style: %r' % name)
    if hasattr(mod, 'DEFAULTS'):
        disp('[%s]\n', name)
        for key, val in mod.DEFAULTS.iteritems():
            disp('%s = %s\n', key, val)
    else:
        disp('# NO DEFAULTS\n')
