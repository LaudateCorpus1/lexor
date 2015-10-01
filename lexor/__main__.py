"""Command line use of lexor

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
from lexor.command import config, import_mod, LexorError
from lexor.util.logging import L


# pylint: disable=W0212
def get_argparse_options(argp):
    """Helper function to preparse the arguments. """
    opt = dict()
    for action in argp._optionals._actions:
        for key in action.option_strings:
            if action.type is None:
                opt[key] = 1
            else:
                opt[key] = 2
    return opt


def preparse_args(argv, argp, subp):
    """Pre-parse the arguments to be able to have a default subparser
    based on the filename provided. """
    opt = get_argparse_options(argp)
    parsers = subp.choices.keys()
    index = 1
    arg = None
    default = 'to'
    try:
        while argv[index] in opt:
            index += opt[argv[index]]
        if index == 1 and argv[index][0] == '-':
            argv.insert(index, 'to')
            argv.insert(index, '_')
            return
        arg = argv[index]
        if arg == 'defaults':
            argv.insert(index, '_')
        if argv[index+1] in parsers:
            return
        if arg not in parsers:
            argv.insert(index+1, default)
    except IndexError:
        if arg not in parsers:
            argv.append(default)
            if arg is None:
                arg = default
    if arg in parsers:
        argv.insert(index, '_')


def parse_options(mod):
    """Interpret the command line inputs and options. """
    desc = """
lexor can perform various commands. Use the help option with a
command for more information.

"""
    ver = "lexor %s" % VERSION
    epi = """
shortcut:

    lexor file.ext lang <==> lexor fle.ext to lang

more info:
  http://jmlopez-rod.github.com/lexor

version:
  lexor %s

""" % VERSION
    raw = argparse.RawDescriptionHelpFormatter
    argp = argparse.ArgumentParser(formatter_class=raw, version=ver,
                                   description=textwrap.dedent(desc),
                                   epilog=textwrap.dedent(epi))
    argp.add_argument('inputfile', type=str, default='_', nargs='?',
                      help='input file to process')
    argp.add_argument('--debug', action='store_true', dest='debug',
                      help='log events')
    argp.add_argument('--lexor-debug', type=str, dest='debug_path',
                      metavar='PATH', default=None,
                      help='diretory to write lexor debug logs')
    argp.add_argument('--cfg', type=str, dest='cfg_path',
                      metavar='CFG_PATH',
                      help='configuration file directory')
    argp.add_argument('--cfg-user', action='store_true',
                      dest='cfg_user',
                      help='select user config file. Overides --cfg')
    subp = argp.add_subparsers(title='subcommands',
                               dest='parser_name',
                               help='additional help',
                               metavar="<command>")

    names = sorted(mod.keys())
    for name in names:
        mod[name].add_parser(subp, raw)
    preparse_args(sys.argv, argp, subp)
    return argp.parse_args()


def run():
    """Run lexor from the command line. """
    mod = dict()
    rootpath = pt.split(pt.abspath(__file__))[0]

    mod_names = [name for name in iglob('%s/command/*.py' % rootpath)]
    for name in mod_names:
        tmp_name = pt.split(name)[1][:-3]
        tmp_mod = import_mod('lexor.command.%s' % tmp_name)
        if hasattr(tmp_mod, 'add_parser'):
            mod[tmp_name] = tmp_mod

    arg = parse_options(mod)

    if arg.debug:
        L.enable()

    config.CONFIG['cfg_path'] = arg.cfg_path
    config.CONFIG['cfg_user'] = arg.cfg_user
    config.CONFIG['arg'] = arg
    try:
        if L.on:
            msg = 'running lexor v%s `%s` command from `%s`'
            L.info(msg, VERSION, arg.parser_name, rootpath)
        mod[arg.parser_name].run()
    except LexorError as err:
        L.error(err.message, exception=err)
    except Exception as err:
        L.error('Unhandled error: %r' % err.message, exception=err)

    if arg.debug:
        fp = sys.stderr
        if arg.debug_path:
            try:
                fp = open(pt.join(arg.debug_path, 'lexor.debug'), 'w')
            except IOError as err:
                L.error('invalid debug log directory', exception=err)
        fp.write('[LEXOR DEBUG LOG]\n')
        fp.write('%r\n' % L)
        if arg.debug_path:
            fp.close()


if __name__ == '__main__':
    run()
