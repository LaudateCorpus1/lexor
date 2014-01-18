"""Lexor Test

This module contains various test for lexor.

To run do: nosetests -vs

"""

from lexor.command import exec_cmd
from lexor.command.lang import LEXOR_PATH
from os.path import dirname, exists
import sys
import re
import textwrap
import lexor
import lexor.command.config as config
from glob import iglob

__all__ = ['WRAPPER', 'print_log', 'parse_write', 'parse_convert_write']

WRAPPER = textwrap.TextWrapper(width=70, break_long_words=False)


DESC = """
This command only takes in one optional parameter. If no parameter
is given then it will attempt to run all the tests available.

If a parameter is given then it may be of one of the following forms:

    lang
    lang.type
    lang.type.style
    lang.converter.tolang.style

The last two forms have the option of being followed by an
specific test name:

    lang.type.style:testname
    lang.converter.tolang.style:testname

"""


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('test', help='test a style',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('param', type=str, nargs='?', default='',
                      help='optional parameter to specify the tests')
    tmpp.add_argument('--installed', action='store_true',
                      help='run all installed tests')
    tmpp.add_argument('--verbose', '-v', action='store_true',
                      help='run all installed tests')


def run():
    """Run command. """
    arg = config.CONFIG['arg']
    cfg = config.get_cfg(['lang', 'develop', 'version'])
    if arg.installed:
        if 'version' in cfg:
            print('Running installed tests ...')
            run_installed(arg.param, cfg, arg.verbose)
        else:
            print('No installed tests to run ...')
    else:
        if 'develop' in cfg:
            print('Running development tests ...')
            run_develop(arg.param, cfg, arg.verbose)
        else:
            print('No development tests to run ...')


def run_develop(param, cfg, verbose):
    """Run develop tests. """
    param = param.split(':')
    testname = '*'
    subtest = ''
    if len(param) > 1:
        testname = param[1]
        if len(param) == 3:
            subtest = ':%s' % param[2]
    keys = [key for key in cfg['develop'] if param[0] in key]
    failed = []
    for key in keys:
        path = cfg['develop'][key][:-3]
        if path[0] != '/':
            path = '%s/%s' % (config.CONFIG['path'], path)
        for pth in iglob('%s/test_%s.py' % (path, testname)):
            cmd = 'nosetests -vs %s%s' % (pth, subtest)
            _, err, _ = exec_cmd(cmd)
            if verbose:
                print(err)
            if 'FAILED' in err:
                failed.append([cmd, err])
    _display_failed(failed)


def run_installed(param, cfg, verbose):
    """Run installed tests. """
    param = param.split(':')
    testname = '*'
    subtest = ''
    if len(param) > 1:
        testname = param[1]
        if len(param) == 3:
            subtest = ':%s' % param[2]
    keys = [key for key in cfg['version'] if key.startswith(param[0])]
    failed = []
    for key in keys:
        name = '/'.join(key.rsplit('.', 1))
        for base in LEXOR_PATH:
            path = '%s/%s-%s' % (base, name, cfg['version'][key])
            if not exists(path):
                continue
            path = '%s/test_%s.py' % (path, testname)
            for pth in iglob(path):
                cmd = 'nosetests -vs %s%s' % (pth, subtest)
                _, err, _ = exec_cmd(cmd)
                if verbose:
                    print(err)
                if 'FAILED' in err:
                    failed.append([cmd, err])
    _display_failed(failed)


def _display_failed(failed):
    """Helper function. """
    if failed:
        print('FAILED TESTS:')
        print('='*70)
        print('')
    else:
        print('ALL TESTS HAVE PASSED')
    for fail in failed:
        print('COMMAND = %s' % fail[0])
        print('-'*70)
        print(fail[1])


def print_log(node):
    """Display the error obtained from parsing. """
    pos = node['position']
    sys.stderr.write('\n  Line %d, Column %d ' % (pos[0], pos[1]))
    sys.stderr.write('in %s:\n      ' % node['file'])
    tmp = re.sub(r"\s+", " ", node['message'])
    sys.stderr.write('\n      '.join(WRAPPER.wrap(tmp)))
    sys.stderr.write('\n\n ... ')


def parse_write(callerfile, in_, out_, style, lang):
    """Provide the filename as the input and the style you wish
    to compare it against. """
    inputfile = "%s/../%s" % (dirname(callerfile), in_)
    with open(inputfile) as tmpf:
        text = tmpf.read()
    sys.stderr.write('\n%s\n%s' % ('='*70, text))
    sys.stderr.write('%s\n' % ('-'*50))
    outputfile = "%s/%s.%s.%s" % (dirname(callerfile), out_, style, lang)
    with open(outputfile) as tmpf:
        text = tmpf.read()
    doc, log = lexor.read(inputfile)
    doc.style = style
    lexor.write(log, sys.stderr)
    sys.stderr.write('\n%s\n' % ('-'*50))
    lexor.write(doc, sys.stderr)
    sys.stderr.write('\n%s\n' % ('='*70))
    return str(doc), text


def parse_convert_write(callerfile, in_, out_, style, tolang):
    """Provide the filename as the input and the style you wish
    to compare it against. """
    inputfile = "%s/../%s" % (dirname(callerfile), in_)
    with open(inputfile) as tmpf:
        text = tmpf.read()
    sys.stderr.write('\n%s\n%s' % ('='*70, text))
    sys.stderr.write('%s\n' % ('-'*50))
    outputfile = "%s/%s.%s.%s" % (dirname(callerfile), out_, style, tolang)
    with open(outputfile) as tmpf:
        text = tmpf.read()
    doc, log = lexor.read(inputfile)
    doc.style = 'default'
    newdoc, newlog = lexor.convert(doc, tolang, style)
    lexor.write(log, sys.stderr)
    lexor.write(newlog, sys.stderr)
    sys.stderr.write('\n%s\n' % ('-'*50))
    lexor.write(newdoc, sys.stderr)
    sys.stderr.write('\n%s\n' % ('='*70))
    return str(newdoc), text
