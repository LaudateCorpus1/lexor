"""Paste

Routine to append paste templates.

"""

import os
from lexor.dev import Template, open_file, error

__all__ = ['run']


def make_style(base, lang, style, type_, tolang=None):
    """Creates a new style file. """
    template = '%s/templates/%s-style.txt' % (base, type_)
    sfile = '%s.py' % style
    if os.path.exists(sfile):
        print 'Opening: %s' % sfile
    else:
        print 'Creating style: %s' % sfile
        newfile = Template(template)
        newfile['LANG'] = lang
        newfile['STYLE'] = style
        if tolang:
            newfile['TOLANG'] = tolang
        with open(sfile, 'w') as wfile:
            wfile.write(str(newfile))
    open_file(sfile)


#pylint: disable-msg=R0913
def make_auxilary(base, lang, style, type_, name, tolang=None):
    """Creates a new node parser module. """
    template = '%s/templates/%s.txt' % (base, type_)
    npfile = '%s.py' % name
    if os.path.exists(npfile):
        print 'Opening: %s' % npfile
    else:
        print 'Creating node parser: %s' % npfile
        newfile = Template(template)
        newfile['LANG'] = lang
        newfile['NP'] = name
        if tolang:
            newfile['TOLANG'] = tolang
        with open(npfile, 'w') as wfile:
            wfile.write(str(newfile))
    open_file(npfile)

    template = '%s/templates/%s-test.txt' % (base, type_)
    npfile = 'test_%s.py' % name
    if os.path.exists(npfile):
        print 'Opening: %s' % npfile
    else:
        print 'Creating node parser: %s' % npfile
        newfile = Template(template)
        newfile['LANG'] = lang
        newfile['NP'] = name
        newfile['STYLE'] = style
        if tolang:
            newfile['TOLANG'] = tolang
        with open(npfile, 'w') as wfile:
            wfile.write(str(newfile))
    open_file(npfile)


def _get_option(array, index, msg):
    """Exit if array index is not accessible."""
    try:
        return array[index]
    except IndexError:
        error(msg)

def run(argp):
    """paste templates. """
    base = os.path.dirname(__file__)
    lang = argp.lang
    style = argp.style
    type_ = argp.type
    if 'converter' in type_:
        msg = "ERROR: converter needs to_lang.\n"
        tolang = _get_option(argp.optional, 0, msg)
    else:
        tolang = None
    if 'node' in type_:
        msg = "ERROR: provide name of auxilary file.\n"
        if 'converter' in argp.type:
            name = _get_option(argp.optional, 1, msg)
        else:
            name = _get_option(argp.optional, 0, msg)
        make_auxilary(base, lang, style, type_, name, tolang)
    else:
        make_style(base, lang, style, type_, tolang)
            