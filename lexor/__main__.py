""" Command line use of lexor

To run lexor from the command line do the following:

    python -m lexor ...

Use the option --help for more information.

"""

import sys
import argparse
import textwrap
import os.path as pt
from glob import iglob
from lexor.__version__ import VERSION
from lexor.command import import_mod
from lexor.command.edit import valid_files
import lexor.command.config as config
try:
    import argcomplete
except ImportError:
    pass


# pylint: disable=W0212
def get_argparse_options(argp):
    "Helper function to preparse the arguments. "
    opt = dict()
    for action in argp._optionals._actions:
        for key in action.option_strings:
            if action.type is None:
                opt[key] = 1
            else:
                opt[key] = 2
    return opt


def preparse_args(argp, subp):
    """Pre-parse the arguments to be able to have a default subparser
    based on the filename provided. """
    opt = get_argparse_options(argp)
    parsers = subp.choices.keys()
    index = 1
    arg = None
    try:
        while sys.argv[index] in opt:
            index += opt[sys.argv[index]]
        if index == 1 and sys.argv[index][0] == '-':
            sys.argv.insert(index, 'to')
            sys.argv.insert(index, '_')
            return
        arg = sys.argv[index]
        default = 'to'
        if arg == 'defaults':
            sys.argv.insert(index, '_')
        if sys.argv[index+1] in parsers:
            return
        if arg not in parsers:
            sys.argv.insert(index+1, default)
    except IndexError:
        if not arg:
            default = 'to'
        if arg not in parsers:
            sys.argv.append(default)
    if arg in parsers:
        sys.argv.insert(index, '_')


def parse_options(mod):
    "Interpret the command line inputs and options. "
    desc = """
lexor can perform various commands. Use the help option with a
command for more information.

"""
    ver = "lexor %s" % VERSION
    epi = """
shortcut:

    lexor file.ext lang <==> lexor fle.ext to lang

More info:
  http://jmlopez-rod.github.com/lexor

Version:
  This is lexor version %s

""" % VERSION
    raw = argparse.RawDescriptionHelpFormatter
    argp = argparse.ArgumentParser(formatter_class=raw, version=ver,
                                   description=textwrap.dedent(desc),
                                   epilog=textwrap.dedent(epi))
    argp.add_argument('inputfile', type=str, default='_', nargs='?',
                      help='input file to process').completer = valid_files
    argp.add_argument('--cfg', type=str, dest='cfg_path',
                      metavar='CFG_PATH',
                      help='configuration file directory')
    subp = argp.add_subparsers(title='subcommands',
                               dest='parser_name',
                               help='additional help',
                               metavar="<command>")
    names = mod.keys()
    names.sort()
    for name in names:
        mod[name].add_parser(subp, raw)
    try:
        argcomplete.autocomplete(argp)
    except NameError:
        pass
    preparse_args(argp, subp)
    return argp.parse_args()


def run():
    """Run excentury from the command line. """
    mod = dict()
    rootpath = pt.split(pt.abspath(__file__))[0]
    mod_names = [name for name in iglob('%s/command/*.py' % rootpath)]
    for name in mod_names:
        tmp_name = pt.split(name)[1][:-3]
        tmp_mod = import_mod('lexor.command.%s' % tmp_name)
        if hasattr(tmp_mod, 'add_parser'):
            mod[tmp_name] = tmp_mod
    arg = parse_options(mod)
    config.CONFIG['cfg_path'] = arg.cfg_path
    config.CONFIG['arg'] = arg
    mod[arg.parser_name].run()


if __name__ == '__main__':
    run()
