"""to

Execute lexor by transforming a file "to" another language.

"""

import os
import re
import sys
import textwrap
import argparse
from lexor.command import error, warn
from lexor.core.parser import Parser
from lexor.core.writer import Writer
from lexor.core.converter import Converter
import lexor.command.config as config

DEFAULTS = {
    'parse_lang': 'xml:_',
    'log': 'lexor:log'
}

DESC = """
Transform the inputfile to another language. To see the available
languages see the `module` command.

examples:

    lexor file.html to markdown[cstyle:wstyle]
    lexor file.html to markdown[cstyle:otherlang.wstyle]
    lexor file.html to html~min,plain,_~
    lexor file.html to html~plain,_~mk[cstyle:wstyle,cstyle1,cstyle2]

  Store output to `output.html` and store warnings in `log.html`:
      lexor doc.md > output.html 2> log.html

  Pipe the output from another program:
       cat doc.md | lexor --from markdown

  Write to files without displaying output:
      lexor --quiet --nodisplay --write doc.md

"""


def language_style(lang_str):
    """Parses a language string. In particular, the options --from
    and --log. """
    tmp = lang_str.lower().split(':')
    input_lang = tmp[0]
    input_style = '_'
    if len(tmp) == 2:
        input_style = tmp[1]
    return input_lang, input_style


def input_language(tolang):
    """Parses the tolang argument. """
    index = tolang.find('[')
    type_ = None
    if index == -1:
        index = tolang.find('~')
        if index == -1:
            return ('c', tolang, [('_', '_')])
        else:
            type_ = 'w'
            if tolang[-1] != '~':
                msg = 'must finish with `~`'
                raise argparse.ArgumentTypeError(msg)
    else:
        type_ = 'c'
        if tolang[-1] != ']':
            msg = 'must finish with `]`'
            raise argparse.ArgumentTypeError(msg)
    styles = tolang[index+1:-1]
    if type_ == 'w':
        msg = '`:` is not supported in "%s~%s~"' % (tolang[:index], styles)
        styles = styles.split(',')
        for style in styles:
            if ':' in style:
                raise argparse.ArgumentTypeError(msg)
    else:
        styles = [language_style(ele) for ele in styles.split(',')]
    return type_, tolang[:index], styles


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('to',
                           help='transform inputfile to another language',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('tolang', metavar='lang', nargs='*',
                      type=input_language,
                      help='languate to which it will be converted')
    tmpp.add_argument('--from', type=language_style, metavar='FROM',
                      dest='parse_lang',
                      help='language to be parsed in')
    tmpp.add_argument('--log', type=language_style,
                      help='language in which the logs will be written')
    tmpp.add_argument('--write', '-w', action='store_true',
                      help='write to file')
    tmpp.add_argument('--quiet', '-q', action='store_true',
                      help='supress warning messages')
    tmpp.add_argument('--nodisplay', '-n', action='store_true',
                      help="supress output")


def get_input(input_file, cfg, default='_'):
    """Returns the text to be parsed along with the name assigned to
    that text. The last output is the extension of the file. """
    if input_file is '_':
        return sys.stdin.read(), 'STDIN', 'STDIN', default
    root = cfg['lexor']['root']
    paths = cfg['edit']['path'].split(':')
    found = False
    for path in paths:
        if path[0] in ['/', '.']:
            abspath = '%s/%s' % (path, input_file)
        else:
            abspath = '%s/%s/%s' % (root, path, input_file)
        if os.path.exists(abspath):
            found = True
            break
    if not found:
        error("ERROR: The file '%s' does not exist.\n" % input_file)
    text = open(abspath, 'r').read()
    textname = input_file
    path = os.path.realpath(abspath)
    name = os.path.basename(path)
    name = os.path.splitext(name)
    file_name = name[0]
    file_ext = name[1][1:].lower()
    if file_ext == '':
        file_ext = default  # The default language to parse
    return text, textname, file_name, file_ext


def run():
    """Run the command. """
    arg = config.CONFIG['arg']
    cfg = config.get_cfg(['to', 'edit'])

    text, t_name, f_name, f_ext = get_input(arg.inputfile, cfg)

    parse_lang = cfg['to']['parse_lang']
    if isinstance(parse_lang, str):
        parse_lang = language_style(parse_lang)
    if arg.parse_lang is None and f_ext != '_':
        parse_lang = (f_ext, parse_lang[1])
    in_lang, in_style = parse_lang

    log = cfg['to']['log']
    if isinstance(log, str):
        log = language_style(log)

    try:
        parser = Parser(in_lang, in_style)
    except IOError:
        msg = "ERROR: Parsing style not found: [%s:%s]\n" % parse_lang
        error(msg)
    try:
        log_writer = Writer(log[0], log[1])
    except IOError:
        msg = "ERROR: log writing style not found: [%s:%s]\n" % log
        error(msg)
    parser.parse(text, t_name)
    write_log(log_writer, parser.log, arg.quiet)
    #convert_and_write(parser, opt)


def write_log(writer, log, quiet):
    """Write the log file to stderr. """
    if quiet is False and len(log) > 0:
        writer.write(log, sys.stderr)

"""
'text': text,
'textname': t_name,
'filename': f_name,
'input_lang': parse_lang[0],
'input_style': parse_lang[1],
'log_lang': log[0],
'log_style': log[1],
'output_info': arg.tolang,
'write': arg.write,
'quiet': arg.quiet,
'nodisplay': arg.nodisplay
"""

def write_document(writer, doc, fname, opt):
    """Auxilary function for convert_and_write. """
    if opt['nodisplay'] is False:
        writer.write(doc, sys.stdout)
    if opt['write'] is True:
        writer.write(doc, fname)



#TODO: Too many branches (13/12)
def convert_and_write(parser, opt):
    """Auxilary function to reduce the number of branches in run. """
    in_lang = opt['input_lang']
    out = opt['output_info']
    try:
        log_writer = Writer(opt['log_lang'], opt['log_style'])
    except IOError:
        msg = "ERROR: log writing style not found: " \
              "[%s:%s]\n" % (opt['log_lang'], opt['log_style'])
        error(msg)
    try:
        writer = Writer()
    except IOError:
        error("ERROR: Writing style not found: [xml:default]\n")
    try:
        converter = Converter()
    except IOError:
        error("ERROR: Converting style not found: [xml ==> xml:default]\n")
    for (action, lang, styles) in out:
        if action == 'c':
            for style in styles:
                try:
                    converter.set(in_lang, lang, style[0])
                    wstyle = style[1]
                    try:
                        if '.' in wstyle:
                            (lang, wstyle) = wstyle.split('.')
                            if wstyle == '_':
                                wstyle = 'default'
                        writer.set(lang, wstyle)
                        converter.convert(parser.doc)
                        write_log(log_writer, converter.log, opt)
                        fname = '%s.%s.%s' % (opt['filename'], wstyle, lang)
                        write_document(writer, converter.doc, fname, opt)
                    except IOError:
                        msg = "ERROR: Writing style not found: " \
                              "[%s:%s]\n" % (lang, wstyle)
                        warn(msg)
                except IOError:
                    msg = "ERROR: Converting style not found: " \
                          "[%s ==> %s:%s]\n" % (in_lang, lang, style[0])
                    warn(msg)
        if action == 'w':
            for style in styles:
                try:
                    writer.set(lang, style)
                    fname = '%s.%s.%s' % (opt['filename'], style, lang)
                    write_document(writer, parser.doc, fname, opt)
                except IOError:
                    msg = "ERROR: Writing style not found: " \
                          "[%s:%s]\n" % (lang, style)
                    warn(msg)
