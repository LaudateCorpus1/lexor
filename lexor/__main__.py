""" Command line use of lexor

To run lexor from the command line do the following:

    python -m lexor ...

Use the option --help for more information.

"""

import os
import sys
import argparse
import textwrap
from lexor.__version__ import VERSION
import lexor.config
import lexor.dev.dist
import lexor.dev.install
import lexor.dev.develop
import lexor.dev.paste
import lexor.cmd_parser

def _get_parser(parsers):
    """Return the type of parser to be executed. A valid file name
    has a higher priority over a command. If a command is requested
    while the first argument is a valid file then you may specify
    that the argument is a command by using the option `--cmd`."""
    arg = None
    found = False
    for arg in sys.argv[1:]:
        if arg == '--cmd':
            found = True
        elif arg[0] != '-':
            break
    if arg in parsers:
        if found:
            return arg
        if os.path.isfile(arg):
            return None
        return arg
    return None


def parse_options():
    """Interpret the command line inputs and options. """
    desc = """lexor is a document converter. In case no INPUTFILE is
given lexor will read from STDIN. """
    ver = "lexor %s" % VERSION
    epi = """
commands:
    config      edit the configuration file ~/.lexorconfig
    dist        create a zip file containing the distribution
    install     install a parser/writer/converter style
    develop     develop a style in the given path
    paste       paste a template

example:
    
    lexor file.html --to markdown[cstyle:wstyle]
    lexor file.html --to markdown[cstyle:otherlang.wstyle]
    lexor file.html --to html~min,plain,_~
    lexor file.html --to html~plain,_~mk[cstyle:wstyle,cstyle1,cstyle2]
  
  Store output to `output.html` and store warnings in `log.html`:
      lexor doc.md > output.html 2> log.html
  
  Pipe the output from another program:
       cat doc.md | lexor --from markdown
  
  Write to files without displaying output:
      lexor --quite --nodisplay --write doc.md

More info:
  http://jmlopez-rod.github.com/lexor/

Version:
  This is lexor version %s

""" % VERSION
    argp = argparse.ArgumentParser(
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                    description=textwrap.dedent(desc),
                    version=ver, epilog=textwrap.dedent(epi))
    command = _get_parser([
        'config', 'dist', 'install', 'develop', 'paste'
    ])
    if not command:
        argp.add_argument('INPUTFILE', type=str, nargs='?', default=None,
                          help='input file to process')
        argp.add_argument('--from', dest='fromlang', type=str, nargs='?',
                          default=None, help='language to be parsed in')
        argp.add_argument('--to', dest='tolang', type=str,
                          default=None, nargs='?',
                          help='language to which it will be converted')
        argp.add_argument('--write', dest='write', action='store_const',
                          const=True, default=False, help='write to file')
        argp.add_argument('--log', dest='log', type=str, nargs='?',
                          default=None,
                          help='language in which the logs will be written')
        argp.add_argument('-q', '--quite', dest='quite', action='store_const',
                          const=True, default=False,
                          help='supress warning messages')
        argp.add_argument('--nodisplay', dest='nodisplay', action='store_const',
                          const=True, default=False, help='supress output')
    else:
        argp.add_argument('--cmd', action='store_const',
                          const=True, default=False,
                          help='force argument to be treated as a command')
        subp = argp.add_subparsers(title='Subcommands',
                                   help='additional help',
                                   dest='parser_name', metavar="<command>")
        # CONFIG
        desc = """edit the configuration file ~/.lexorconfig"""
        tmpp = subp.add_parser('config', help='configure lexor',
                                description=desc)
        tmpp.add_argument('key', type=str,
                          help='Must be in the form of section.key')
        tmpp.add_argument('value', type=str,  nargs='?', default=None,
                          help='key value')
        # DIST
        desc = """create a zip file containing the distribution """
        tmpp = subp.add_parser('dist', help='distribute a style',
                                description=desc)
        tmpp.add_argument('style', type=str,
                          help='name of style')
        tmpp.add_argument('--dir', type=str, dest='dir',
                          default=None, help='distribution directory')
        # INSTALL
        desc = """install a parser/writer/converter style """
        tmpp = subp.add_parser('install', help='install a style',
                                description=desc)
        tmpp.add_argument('style', type=str,
                           help='name of the style to install')
        tmpp.add_argument('--user', action='store_const',
                          const=True, default=False,
                          help='install in user-site')
        # DEVELOP
        desc = """develop a style in the given path """
        tmpp = subp.add_parser('develop', help='install a style',
                                description=desc)
        tmpp.add_argument('path', type=str,
                           help='path to the style, it may be relative.')

        # PASTE
        desc = """paste a template """
        tmpp = subp.add_parser('paste', help='paste a style',
                                description=desc)
        tmpp.add_argument('style', type=str,
                           help='the style name')
        tmpp.add_argument('lang', type=str,
                           help='language')
        tmpp.add_argument('type', type=str, choices=[
                          'parser', 'writer', 'converter',
                          'node-parser', 'node-writer', 'node-converter'],
                           help='the type of file to write')
        tmpp.add_argument('optional', nargs='*', default=None,
                          help="[to language] [auxilary filename]")

        tmpp = subp.add_parser('parser', help='make a style')
        tmpp.add_argument('repo', type=str, help='path to repository')
    return command, argp.parse_args()


def run():
    """Run promus from the command line. """
    command, arg = parse_options()
    if command:
        cmd_map = {
            'config': lexor.config.run,
            'dist': lexor.dev.dist.run,
            'install': lexor.dev.install.run,
            'develop': lexor.dev.develop.run,
            'paste': lexor.dev.paste.run
        }
        cmd_map[command](arg)
    else:
        lexor.cmd_parser.execute(arg)


if __name__ == '__main__':
    run()
