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
import textwrap
from pkg_resources import parse_version
from os.path import splitext, abspath
from imp import load_source
from glob import iglob, glob
from lexor.command import config


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
Show the styles available to lexor through the current configuration
file. You should run this command whenever you create a new
configuration file so that lexor may select the available languages
for you without the need to reinstall the styles.

"""
LEXOR_PATH = [
    '%s/lib/lexor' % site.getuserbase(),
    '%s/lib/lexor' % sys.prefix
]

if 'LEXORPATH' in os.environ:
    LEXOR_PATH = os.environ['LEXORPATH'].split(':') + LEXOR_PATH


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    subp.add_parser('lang', help='see available styles',
                    formatter_class=fclass,
                    description=textwrap.dedent(DESC))


def _handle_kind(paths, cfg):
    """Helper function for _handle_lang. """
    styles = dict()
    if paths:
        kind = os.path.basename(paths[0])
    for path in paths:
        tmp = [os.path.basename(ele) for ele in glob('%s/*.py' % path)]
        for style in tmp:
            index = style.find('-')
            if index == -1:
                continue
            if style[:index] not in styles:
                styles[style[:index]] = []
            styles[style[:index]].append(style[index+1:-3])
    if 'version' not in cfg:
        cfg.add_section('version')
    for style in styles:
        key = '%s.%s' % (kind, style)
        if key in cfg['version']:
            ver = cfg['version'][key]
            print '        [*] %s -> %s' % (style, ver)
        else:
            ver = max(styles[style], key=parse_version)
            cfg['version'][key] = ver
            print '        [+] %s -> %s' % (style, ver)
    config.write_config(cfg)


def _handle_lang(path, cfg):
    """Helper function for run. """
    for kind in path:
        print '    %s:' % kind
        _handle_kind(path[kind], cfg)


def run():
    """Run the command. """
    paths = []
    for base in LEXOR_PATH:
        paths += glob('%s/*' % base)
    path = dict()
    cfg = config.read_config()
    for loc in paths:
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
    for lang in path:
        print '%s:' % lang
        _handle_lang(path[lang], cfg)
        print ''


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
        modname = 'lexor-lang_%s_%s_%s_%s' % (lang, type_, to_lang, style)
    else:
        key = '%s.%s.%s' % (lang, type_, style)
        name = '%s.%s/%s' % (lang, type_, style)
        modname = 'lexor-lang_%s_%s_%s' % (lang, type_, style)
    return key, name, modname


def get_style_module(type_, lang, style, to_lang=None):
    """Return a parsing/writing/converting module. """
    cfg = config.get_cfg(['lang', 'develop', 'version'])
    config.update_single(cfg, 'lang', DEFAULTS)
    key, name, modname = _get_info(cfg, type_, lang, style, to_lang)
    if 'develop' in cfg:
        try:
            path = cfg['develop'][key]
            if path[0] != '/':
                path = '%s/%s' % (config.CONFIG['path'], path)
            return load_source(modname, path)
        except (KeyError, IOError):
            pass
    versions = []
    for base in LEXOR_PATH:
        if 'version' in cfg:
            try:
                path = '%s/%s-%s.py' % (base, name, cfg['version'][key])
            except KeyError:
                versions += glob('%s/%s*.py' % (base, name))
                path = '%s/%s.py' % (base, name)
        else:
            versions += glob('%s/%s*.py' % (base, name))
            path = '%s/%s.py' % (base, name)
        try:
            return load_source(modname, path)
        except IOError:
            continue
    try:
        mod = load_source(modname, versions[0])
        mod.VERSIONS = versions
        return mod
    except (IOError, IndexError):
        raise ImportError("lexor module not found: %s" % name)


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
    The only parameter is the dictionary `INFO` that needs to exist
    with every style. `INFO` is returned by the init function in
    the lexor module."""
    dirpath = splitext(abspath(info['path']))[0]
    if info['to_lang']:
        modbase = 'lexor-lang_%s_converter_%s' % (info['lang'],
                                                  info['to_lang'])
    else:
        modbase = 'lexor-lang_%s_%s_%s' % (info['lang'],
                                           info['type'],
                                           info['style'])
    return load_mod(modbase, dirpath)


def load_rel(path, module):
    """Load relative to a path. If path is the name of a file the
    filename will be dropped. """
    if not os.path.isdir(path):
        path = os.path.dirname(os.path.realpath(path))
    if '.py' in module:
        module = module[1:-3]
    fname = '%s/%s.py' % (path, module)
    return load_source('load-rel-%s' % module, fname)


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
