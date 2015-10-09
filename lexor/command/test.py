"""Lexor Test

This module contains various test for lexor.

"""
from __future__ import print_function

import re
import sys
import lexor
import textwrap
from glob import iglob
from nose.tools import eq_
from lexor.command import exec_cmd, wdisp
from lexor.command.lang import LEXOR_PATH, get_style_module
from lexor.core.parser import Parser
from os.path import dirname, exists
from lexor.command import config
from lexor.util.logging import L


RE = re.compile(r'(?P<code>[A-Z][0-9]*|Okay):')
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
                      help='display test messages')


def run():
    """Run command. """
    arg = config.CONFIG['arg']
    cfg = config.get_cfg(['lang', 'develop', 'dependencies'])
    if arg.installed:
        if 'dependencies' in cfg:
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
            out, err, _ = exec_cmd(cmd)
            if verbose:
                print(out)
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
    keys = [key for key in cfg['dependencies'] if key.startswith(param[0])]
    failed = []
    for key in keys:
        name = '/'.join(key.rsplit('.', 1))
        for base in LEXOR_PATH:
            path = '%s/%s' % (base, name)
            L.info('checking %r', path)
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


def compare_with(str_obj, expected):
    """Calls ``nose.eq_`` to compare the strings and prints a custom
    message. """
    hline = '_'*60
    msg = "str_obj -->\n%s\n%s\n%s\n\
expected -->\n%s\n%s\n%s\n" % (hline, str_obj, hline,
                               hline, expected, hline)
    eq_(str_obj, expected, msg)


def parse_msg(msg):
    """Obtain the tests embedded inside the messages declared in a
    style. The format of the messages is as follows::

        <tab>[A-Z][0-9]*: <msg>

    or::

        <tab>([A-Z][0-9]*|Okay):
        <tab><tab>msg ...
        <tab><tab>msg continues
        <tab>([A-Z][0-9]*|Okay): msg

    Where ``<tab>`` consists of 4 whitespaces. This function returns
    the message without the tests and a list of tuples of the form
    ``(code, msg)`` along with the message """
    lines = msg.split('\n')
    tests = []
    index = 0
    end = len(lines)
    while index < len(lines):
        match = RE.match(lines[index].strip())
        if match is None:
            index += 1
        else:
            end = index
            break
    while index < len(lines):
        line = lines[index].strip()
        match = RE.match(line)
        if match is not None:
            line = line[match.end():].strip()
            if line == '' and index + 1 < len(lines):
                tmp = lines[index+1]
                if RE.match(tmp[4:]) is None:
                    line += tmp[8:]
                    index += 1
                    while index + 1 < len(lines):
                        tmp = lines[index+1]
                        if RE.match(tmp[4:]) is not None:
                            break
                        line += '\n' + tmp[8:]
                        index += 1
            tests.append((match.group('code'), line))
        index += 1
    return '\n'.join([line[4:] for line in lines[:end]]), tests


def find_failed(tests, lang, style, defaults):
    """Run the tests and return a list of the tests that fail. """
    failed = []
    parser = Parser(lang, style, defaults)
    for test in tests:
        parser.parse(test[1])
        if test[0] == 'Okay':
            if len(parser.log.child) != 0:
                failed.append(test)
        else:
            found = False
            for node in parser.log.child:
                if test[0] == node['code']:
                    found = True
                    break
            if not found:
                failed.append(test)
    return failed


def nose_msg_explanations(lang, type_, style, name, to_lang=None,
                          defaults=None):
    """Gather the ``MSG_EXPLANATION`` list and run the tests it
    contains."""
    mod = get_style_module(type_, lang, style, to_lang)
    mod = sys.modules['%s_%s' % (mod.__name__, name)]
    if not hasattr(mod, 'MSG_EXPLANATION'):
        return
    errors = False
    wdisp('\n')
    for num, msg in enumerate(mod.MSG_EXPLANATION):
        wdisp('MSG_EXPLANATION[%d] ... ' % num)
        msg, tests = parse_msg(msg)
        failed = find_failed(tests, lang, style, defaults)
        err = ['    %s: %r' % (fail[0], fail[1]) for fail in failed]
        if err:
            errors = True
            wdisp('\n%s\n' % '\n'.join(err))
        else:
            wdisp('ok\n')
    eq_(errors, False, "Errors in MSG_EXPLANATION")
    wdisp('...................... ')


def equal_nodes(node1, node2):
    """Return true if the nodes contain the same information."""
    # TODO: Perform more comparisons on data and attributes
    if node1.name != node2.name:
        return False
    if len(node1) != len(node2):
        return False
    if node1.child:
        for i, child in enumerate(node1):
            if not equal_nodes(child, node2[i]):
                return False
    return True
