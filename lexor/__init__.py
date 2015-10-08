"""
To use lexor as a module you should explore in detail the packages
provided with lexor. These packages contain many other functions and
information which can help you convert your document in the way you
desire.

:|core|:
    The core of lexor defines basic objects such as ``Document`` and
    provides the main objects that define the functions provided in
    this module.

:|command|:
    This module is in charge of providing all the available commands
    to lexor.

.. |core| replace:: :mod:`~lexor.core`
.. |command| replace:: :mod:`~lexor.command`

----------------------------------------------------------------------

In this module we can find useful functions to quickly parse, convert
and write files without first creating any of the main lexor objects.

"""
import re
import os
import os.path as pth
from sys import stdout
from os.path import realpath, basename, splitext
from lexor.__version__ import get_version
from lexor.command.lang import load_aux, style_reference
from lexor import core

__all__ = [
    'lexor',
    'parse',
    'read',
    'convert',
    'write',
    'init',
]


def _read_text(src, search=False):
    """Attempt to read a file and return its contents. """
    try:
        return open(src).read()
    except IOError:
        if search is False:
            return None
    try:
        lexorinputs = os.environ['LEXORINPUTS']
    except KeyError:
        return None
    for directory in lexorinputs.split(':'):
        path = '%s/%s' % (directory, src)
        try:
            return open(path).read()
        except IOError:
            pass
    return None


def lexor(src, search=False, **keywords):
    """Utility function to parse and convert a file or string
    specified by `src`. If `search` is ``True`` then it will
    attemp to search for `src` in the paths specified by the
    enviromental variable ``$LEXORINPUTS``. The following are all the
    valid keywords and its defaults that this function accepts:

    - parser_style: ``'_'``
    - parser_lang: ``None``
    - parser_defaults: ``None``,
    - convert_style: ``'_'``,
    - convert_from: ``None``,
    - convert_to: ``'html'``,
    - convert_defaults: ``None``,
    - convert: ``'true'``

    Returns the converted ``Document`` object and the log
    ``Document`` containing possible warning or error messages.
    """
    info = {
        'parser_style': '_',
        'parser_lang': None,
        'parser_defaults': None,
        'convert_style': '_',
        'convert_from': None,
        'convert_to': 'html',
        'convert_defaults': None,
        'convert': 'true'
    }
    for key in keywords:
        info[key] = keywords[key]
    text = _read_text(src, search)
    if text is None:
        match = re.match(r'^(\.|/)(.*/)?(?:$|(.+?)(?:(\.[^.]*$)|$))', src)
        if match:
            raise IOError('file `%s` not found' % src)
        else:
            text = src
            if info['parser_lang'] is None:
                info['parser_lang'] = 'lexor'
            src = 'string@0x%x' % id(text)
    elif info['parser_lang'] is None:
        path = pth.realpath(src)
        name = pth.basename(path)
        name = pth.splitext(name)
        info['parser_lang'] = name[1][1:]
    parser = core.Parser(info['parser_lang'],
                         info['parser_style'],
                         info['parser_defaults'])
    parser.parse(text, src)
    if info['convert'] == 'true' and info['convert_to'] is not None:
        if info['convert_from'] is None:
            info['convert_from'] = info['parser_lang']
        converter = core.Converter(info['convert_from'],
                                   info['convert_to'],
                                   info['convert_style'],
                                   info['convert_defaults'])

        converter.convert(parser.doc)
        if parser.log:
            converter.update_log(parser.log, False)
        cdoc = converter.doc.pop()
        clog = converter.log.pop()
    else:
        cdoc = parser.doc
        clog = parser.log
    return cdoc, clog


def parse(text, lang='xml', style='default'):
    """Parse the `text` in the language specified by `lang` and
    return its ``Document`` form and a ``Document`` log containing
    the errors encountered during parsing. """
    parser = core.Parser(lang, style)
    parser.parse(text)
    return parser.document, parser.log


def read(filename, style="default", lang=None):
    """Read and parse a file. If `lang` is not specified then the
    language is assummed from the `filename` extension. Returns the
    ``Document`` form and a ``Document`` log containing the errors
    encountered during parsing. """
    if lang is None:
        path = realpath(filename)
        name = basename(path)
        name = splitext(name)
        lang = name[1][1:]
    with open(filename, 'r') as tmpf:
        text = tmpf.read()
    parser = core.Parser(lang, style)
    parser.parse(text, filename)
    return parser.document, parser.log


def convert(doc, lang=None, style="default"):
    """Convert the ``Document`` `doc` to another language in a given
    style. If the `lang` is not specified then the `doc` is
    tranformed to the same language as the ``Document`` using the
    default style. """
    if lang is None:
        lang = doc.owner.lang
    converter = core.Converter(doc.owner.lang, lang, style)
    converter.convert(doc)
    return converter.document, converter.log


def write(doc, filename=None, mode='w', **options):
    """Write `doc` to a file. To write to the standard output use the
    default parameters, otherwise provide `filename`. If `filename`
    is provided you have the option of especifying the mode: ``'w'``
    or ``'a'``.

    You may also provide a file you may have opened yourself in place
    of filename so that the writer writes to that file, in this case
    the `mode` is ignored.

    The valid `options` depends on the language the document
    specifies. See the ``DEFAULT`` values a particular writer style
    has to obtain the valid options. """
    if doc.owner is None:
        style = 'default'
        lang = 'xml'
    else:
        style = doc.owner.style
        lang = doc.owner.lang
    writer = core.Writer(lang, style)
    if doc.owner is not None and doc.owner.defaults is not None:
        for var, val in doc.owner.defaults.iteritems():
            writer.defaults[var] = os.path.expandvars(str(val))
    for var, val in options.iteritems():
        writer.defaults[var] = os.path.expandvars(str(val))
    if filename:
        writer.write(doc, filename, mode)
    else:
        writer.write(doc, stdout)


def init(**keywords):
    """Every lexor style needs to call the ``init`` function. These
    are the valid keywords to initialize a style:

    - version: ``(major, minor, micro, alpha/beta/rc/final, #)``
    - lang
    - [to_lang]
    - type
    - description
    - [github]: ``{'user', 'repo'}``
    - author: ``{'name', 'email'}``
    - [docs]
    - license
    - path: Must be set to ``__file__``.

    """
    required_keys = [
        'version', 'lang', 'type', 'description', 'author', 'license',
        'path'
    ]
    optional_keys = [
        'to_lang', 'github', 'docs'
    ]
    for key in required_keys:
        if key not in keywords:
            raise NameError('lexor.init requies `%s`' % key)
    info = dict()
    for key in optional_keys:
        info[key] = None
    for key in keywords:
        info[key] = keywords[key]
    info['style'] = splitext(basename(info['path']))[0]
    info['style'] = info['style'].split('-')[0]
    info['ver'] = get_version(info['version'])
    return info
