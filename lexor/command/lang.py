"""
This module provides functions to load the different parsers, writers
and converters. It defines the list ``LEXOR_PATH`` which is an array
of paths where lexor looks for the parsing, writing and converting
styles. You may specify more paths by either directly appending to
this path while using lexor as a python module or by editing the
enviromental variable ``LEXORPATH`` and appending paths to it
separating them by a colon ``:``.

"""

import os
import sys
import site
import textwrap
from os.path import splitext, abspath
from imp import load_source
from glob import iglob, glob
from lexor.util.logging import L
from lexor.command import config, disp, LexorError


DEFAULTS = {
    '_': 'default',
    'md': 'markdown',
    'mdown': 'markdown',
    'mkdn': 'markdown',
    'mkd': 'markdown',
    'mdwn': 'markdown',
    'mdtxt': 'markdown',
    'mdtext': 'markdown',
    'text': 'markdown',
    'lex': 'lexor',
    'pyhtml': 'html',
    'pyxml': 'xml',
}
DESC = """
Show all the lexor modules which are installed in the directories
specified in ``LEXORPATH``.

"""
try:
    LEXOR_PATH = [
        './lexor_modules',
        '%s/lib/lexor_modules' % site.getuserbase(),
        '%s/lib/lexor_modules' % sys.prefix
    ]
except AttributeError:
    LEXOR_PATH = [
        './lexor_modules',
        '%s/lib/lexor_modules' % sys.prefix
    ]

if 'LEXORPATH' in os.environ:
    LEXOR_PATH = os.environ['LEXORPATH'].split(':') + LEXOR_PATH


def add_parser(subp, fclass):
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Add a parser to the main subparser.
    """
    subp.add_parser('lang', help='see available styles',
                    formatter_class=fclass,
                    description=textwrap.dedent(DESC))


def _handle_kind(paths):
    """Helper function for _handle_lang. """
    styles = dict()
    for path in paths:
        L.info('... processing %s', path)
        pattern = '%s/*.py' % path
        tmp = [ele for ele in glob(pattern)]
        for module_path in tmp:
            try:
                mod_name = '__tmp%d__' % _handle_kind.loaded
                module = load_source(mod_name, module_path)
                _handle_kind.loaded += 1
            except ImportError:
                continue
            style = os.path.basename(module_path)[:-3]
            L.info('      - %s: %r', style, module)
            if style not in styles:
                styles[style] = []
            styles[style].append(module)
    for style in sorted(styles.keys()):
        disp('        [*] %s ->\n' % style)
        for module in styles[style]:
            info = module.INFO
            msg = '               %s: %s\n'
            disp(msg % (info['ver'], info['path']))
_handle_kind.loaded = 0


def _handle_lang(path):
    """Helper function for run. """
    for kind in sorted(path.keys()):
        disp('    %s:\n' % kind)
        _handle_kind(path[kind])


def run():
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Run the command.
    """
    L.info('searching for lexor modules ...')
    paths = []
    for base in LEXOR_PATH:
        paths += glob('%s/*' % base)
    path = dict()
    for loc in paths:
        L.info('searching in %r', loc)
        kind = os.path.basename(loc)
        try:
            name, kind = kind.split('.', 1)
        except ValueError:
            continue
        if name not in path:
            path[name] = dict()
        if kind not in path[name]:
            path[name][kind] = [loc]
        else:
            path[name][kind].append(loc)
    for lang in sorted(path.keys()):
        disp('%s:\n' % lang)
        _handle_lang(path[lang])
        disp('\n')


def _get_info(cfg, type_, lang, style, to_lang=None):
    """Helper function for get_style_module. """
    if style == '_':
        style = 'default'
    if lang in cfg['lang']:
        lang = cfg['lang'][lang]
    if to_lang:
        if to_lang in cfg['lang']:
            to_lang = cfg['lang'][to_lang]
        key = '%s.%s.%s.%s' % (lang, type_, to_lang, style)
        name = '%s.%s.%s/%s' % (lang, type_, to_lang, style)
        modname = 'lexor-lang_%s_%s_%s_%s'
        modname %= (lang, type_, to_lang, style)
    else:
        key = '%s.%s.%s' % (lang, type_, style)
        name = '%s.%s/%s' % (lang, type_, style)
        modname = 'lexor-lang_%s_%s_%s' % (lang, type_, style)
    return key, name, modname


def get_style_module(type_, lang, style, to_lang=None):
    """Return a parsing/writing/converting module. """
    cfg = config.get_cfg(['lang', 'develop'])
    config.update_single(cfg, 'lang', DEFAULTS)
    key, name, modname = _get_info(cfg, type_, lang, style, to_lang)
    L.info('searching for %s', name)
    if 'develop' in cfg:
        try:
            path = cfg['develop'][key]
            if path[0] != '/':
                path = '%s/%s' % (config.CONFIG['path'], path)
            try:
                module = load_source(modname, path)
            except IOError:
                msg = 'Unable to load module in development: %s'
                raise LexorError(msg % path)
            ver = module.INFO['ver']
            L.info('... developing v%s from %s', ver, path)
            return module
        except KeyError:
            pass
    for base in LEXOR_PATH:
        path = '%s/%s.py' % (base, name)
        try:
            module = load_source(modname, path)
            ver = module.INFO['ver']
            L.info('... found v%s in %r', ver, base)
            return module
        except IOError:
            L.info('... searched in %r', base)
    raise ImportError('lexor module not found: %s' % name)


def load_mod(modbase, dirpath):
    """Return a dictionary containing the modules located in
    `dirpath`. The name `modbase` must be provided so that each
    module may have a unique identifying name. The result will be a
    dictionary of modules. Each of the modules will have the name
    ``"modbase_modname"`` where modname is a module in the
    directory."""
    mod = dict()
    for path in iglob('%s/*.py' % dirpath):
        if 'test' not in path:
            module = path.split('/')[-1][:-3]
            modname = '%s_%s' % (modbase, module)
            mod[module] = load_source(modname, path)
    return mod


def load_aux(info):
    """Wrapper around :func:`load_mod` for easy use when developing
    styles. The only parameter is the dictionary ``INFO`` that needs
    to be defined with every style. ``INFO`` is returned by the
    :func:`lexor.init` function.
    """
    dirpath = splitext(abspath(info['path']))[0]
    if info['to_lang']:
        modbase = 'lexor-lang_%s_converter_%s_%s'
        modbase %= (info['lang'], info['to_lang'], info['style'])
    else:
        modbase = 'lexor-lang_%s_%s_%s'
        modbase %= (info['lang'], info['type'], info['style'])
    return load_mod(modbase, dirpath)


def load_rel(path, module):
    """Load relative to a path. If path is the name of a file the
    filename will be dropped.
    """
    if not os.path.isdir(path):
        path = os.path.dirname(os.path.realpath(path))
    if '.py' in module:
        module = module[1:-3]
    fname = '%s/%s.py' % (path, module)
    return load_source('load-rel-%s' % module, fname)


def style_reference(**info):
    """Return a reference to a style module. Useful in situations
    when a node converter may want to access to the style they define.

    Expects the following keys:

    - lang
    - [to_lang]
    - [type]: Required if to_lang is not defined.
    - [style]: defaults to 'default'.

    """
    style = info.get('style', 'default')
    if style == '_':
        style = 'default'
    to_lang = info.get('to_lang', None)
    if to_lang:
        modbase = 'lexor-lang_%s_converter_%s_%s'
        modbase %= (info['lang'], to_lang, style)
    else:
        modbase = 'lexor-lang_%s_%s_%s'
        modbase %= (info['lang'], info['type'], style)
    return sys.modules[modbase]


def map_explanations(mod, exp):
    """Helper function to create a map of msg codes to explanations
    in the lexor language modules. """
    if not mod:
        return
    for mod_name, module in mod.iteritems():
        exp[mod_name] = dict()
        codes = module.MSG.keys()
        for index in xrange(len(module.MSG_EXPLANATION)):
            sub = len(codes) - 1
            while sub > -1:
                code = codes[sub]
                if code in module.MSG_EXPLANATION[index]:
                    del codes[sub]
                    exp[mod_name][code] = index
                sub -= 1
            if not codes:
                break
