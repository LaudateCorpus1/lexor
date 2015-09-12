"""Paste

Routine to append paste templates.

"""
# pylint: disable=W0142

import os
import textwrap
from lexor.command import config, LexorError

DESC = """
Paste a template to create a new style.

"""


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    types = ['parser', 'writer', 'converter',
             'node-parser', 'node-writer', 'node-converter']
    tmpp = subp.add_parser('paste', help='paste a template',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('lang', type=str,
                      help='language name')
    tmpp.add_argument('type', type=str, metavar='type', choices=types,
                      help='file type: ' + ', '.join(types))
    tmpp.add_argument('style', type=str,
                      help='style name')
    tmpp.add_argument('optional', nargs='*', default=None,
                      help="[to language] [auxilary filename]")


def make_style(base, type_, fmt):
    """Creates a new style file. """
    template = '%s/../core/templates/%s-style.txt' % (base, type_)
    content = open(template).read()
    sfile = '%s.py' % fmt['style']
    if os.path.exists(sfile):
        print 'Opening: %s' % sfile
    else:
        print 'Creating style: %s' % sfile
        with open(sfile, 'w') as wfile:
            wfile.write(content.format(**fmt))
    return sfile


def make_auxilary(base, type_, fmt, aux_type=''):
    """Creates a new node parser module. """
    tmp = '' if aux_type == '' else '-test'
    template = '%s/../core/templates/%s%s.txt' % (base, type_, tmp)
    content = open(template).read()
    tmp = '' if aux_type == '' else 'test_'
    npfile = '%s%s.py' % (tmp, fmt['np'])
    if os.path.exists(npfile):
        print 'Opening: %s' % npfile
    else:
        print 'Creating node processor: %s' % npfile
        with open(npfile, 'w') as wfile:
            wfile.write(content.format(**fmt))
    return npfile


def _get_option(array, index, msg):
    """Exit if array index is not accessible."""
    try:
        return array[index]
    except IndexError:
        raise LexorError(msg)


def run():
    """Run the command. """
    arg = config.CONFIG['arg']

    base = os.path.dirname(__file__)
    lang = arg.lang
    style = arg.style
    type_ = arg.type

    if 'converter' in type_:
        msg = 'converter needs to_lang.'
        tolang = _get_option(arg.optional, 0, msg)
    else:
        tolang = ''

    fmt = {
        'LANG': lang.upper(),
        'STYLE': style.upper(),
        'TOLANG': tolang.upper(),
        'lang': lang,
        'style': style,
        'tolang': tolang
    }

    if 'node' in type_:
        msg = 'provide name of auxilary file.'
        if 'converter' in type_:
            name = _get_option(arg.optional, 1, msg)
        else:
            name = _get_option(arg.optional, 0, msg)
        fmt['NP'] = name.upper()
        fmt['np'] = name
        npfile = make_auxilary(base, type_, fmt)
        # os.system('%s "%s" > /dev/null' % (editor, npfile))
        npfile = make_auxilary(base, type_, fmt, '-test')
        # os.system('%s "%s" > /dev/null' % (editor, npfile))
    else:
        sfile = make_style(base, type_, fmt)
        # cmd = '%s "%s" > /dev/null' % (editor, sfile)
        # os.system(cmd)
