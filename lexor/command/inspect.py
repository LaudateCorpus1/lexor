"""
This is a utility module to inspect all the files in a given
directory.

"""
import os
import re
import sys
import argparse
import textwrap
import configparser
import os.path as pth
from lexor.util.logging import L
from lexor.command import config, import_mod, LexorError, disp
from lexor import core


DESC = """
inspect files in a given directory.

"""
DEFAULTS = {
    'skip-dir': '.git|lib',
    'ignore-file': '.gitignore|^.*\.(jpg|gif|svg|png|swf|less|css|as)'
}


def add_parser(subp, fclass):
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Add a parser to the main sub-parser.
    """
    tmpp = subp.add_parser('inspect', help='inspect directory',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('path', type=str,
                      help='directory to inspect')


def run():
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Run the command.
    """
    arg = config.CONFIG['arg']
    path = pth.abspath(arg.path)
    files = gather_files(path)
    log_writer = core.Writer('lexor', 'log')
    missing_parsers = []
    for ext in files:
        ext = ext[1:]
        parser = core.Parser(ext, )
        try:
            parser.parse('')
        except ImportError:
            missing_parsers.append(ext)
            continue
        for f in files['.'+ext]:
            parser.parse(open(f).read(), f)
            if len(parser.log) > 0:
                log_writer.write(parser.log, sys.stdout)
                disp('\n')
    disp('No parser for: %r\n', missing_parsers)


def gather_files(path):
    """Get a dictionary of lexor files and configuration files. """
    files = {}
    cfg = config.get_cfg(['inspect'])
    inspect = cfg['inspect']
    re_skip = re.compile(inspect['skip-dir'])
    re_ignore = re.compile(inspect['ignore-file'])
    for dirname, dirnames, filenames in os.walk(path):
        allowed = list()
        for subdir in dirnames:
            if re_skip.match(subdir) is None:
                allowed.append(subdir)
            else:
                L.info('  skip-dir -> %r', pth.join(dirname, subdir))

        for name in filenames:
            if re_ignore.match(name) is not None:
                L.info('  skip-file -> %r', pth.join(dirname, name))
                continue
            filename, ext = pth.splitext(name)
            if ext not in files:
                files[ext] = []
            files[ext].append(pth.join(dirname, name))

        del dirnames[:]
        dirnames.extend(allowed)
    return files
