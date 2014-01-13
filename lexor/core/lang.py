"""Language

This module provides functions to load the different languages
parsers, writers and converters.

## Constants

`LEXOR_PATH`: The paths where lexor looks for the parsing, writing
and converting styles.

"""

import os
import sys
import site
from os.path import splitext, abspath
from imp import load_source
from glob import iglob
from lexor.command.config import get_cfg

__all__ = ['LEXOR_PATH', 'get_style_module']

LEXOR_PATH = [
    '%s/lib/lexor' % site.getuserbase(),
    '%s/lib/lexor' % sys.prefix
]

if 'LEXORPATH' in os.environ:
    LEXOR_PATH = os.environ['LEXORPATH'].split(':') + LEXOR_PATH


def get_style_module(type_, lang, style, to_lang=None):
    """Return a parsing/writing/converting module. """
    config = get_cfg([])
    #config = read_config()
    if lang in config['lang']:
        lang = config['lang'][lang]
    if to_lang:
        if to_lang in config['lang']:
            to_lang = config['lang'][to_lang]
        key = '%s.%s.%s.%s' % (lang, type_, to_lang, style)
        name = '%s.%s.%s/%s' % (lang, type_, to_lang, style)
        modname = 'lexor-%s-%s-%s-%s' % (lang, type_, to_lang, style)
    else:
        key = '%s.%s.%s' % (lang, type_, style)
        name = '%s.%s/%s' % (lang, type_, style)
        modname = 'lexor-%s-%s-%s' % (lang, type_, style)
    if 'develop' in config:
        try:
            return load_source(modname, config['develop'][key])
        except KeyError:
            pass
        except IOError:
            pass
    path = ''
    for base in LEXOR_PATH:
        if 'version' in config:
            try:
                path = '%s/%s-%s.py' % (base, name, config['version'][key])
            except KeyError:
                pass
        else:
            path = '%s/%s.py' % (base, name)
        try:
            return load_source(modname, path)
        except IOError:
            continue
    raise IOError("lexor module not found: %s" % name)


def load_mod(modbase, dirpath):
    """Return a dictionary containing the modules located in
    `dirpath`. The name `modbase` must be provided so that each
    module may have a unique identifying name. The result will be a
    dictionary of modules. Each of the modules will have the name
    "modbase_modname" where modname is a module in the directory."""
    mod = dict()
    for path in iglob('%s/*.py' % dirpath):
        if 'test' not in path:
            module = path.split('/')[-1][:-3]
            modname = '%s_%s' % (modbase, module)
            mod[module] = load_source(modname, path)
    return mod


def load_aux(info):
    """Wrapper around load_mod for easy use when developing styles.
    The only parameter is the dictionary INFO that needs to exist
    with every style. INFO is returned by the init function in
    lexor.dev """
    dirpath = splitext(abspath(info['path']))[0]
    if info['to_lang']:
        modbase = 'lexor-lang_%s_converter_%s'
        modbase = modbase % (info['lang'], info['to_lang'])
    else:
        modbase = 'lexor-lang_%s_%s' % (info['lang'], info['type'])
    return load_mod(modbase, dirpath)

def load_rel(path, module):
    """Load relative to a path. If path is the name of a file the
    filename will be dropped. """
    if not os.path.isdir(path):
        path = os.path.dirname(os.path.realpath(path))
    if '.py' in module:
        module = module[1:-3]
    file = '%s/%s.py' % (path, module)
    return load_source('load-rel-%s' % module, file)
