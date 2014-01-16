"""to

Execute lexor by transforming a file "to" another language.

"""

import os
import re
import sys
import textwrap
from lexor.command import error, warn
from lexor.core.parser import Parser
from lexor.core.writer import Writer
from lexor.core.converter import Converter


DESC = """
Transform the inputfile to another language. To see the available
languages see the module command

"""


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    types = ['parser', 'writer', 'converter',
             'node-parser', 'node-writer', 'node-converter']
    tmpp = subp.add_parser('to', help='transform to another language',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('tolang', metavar='lang', type=str, nargs='?',
                      help='languate to which it will be converted')
    tmpp.add_argument('--from', type=str, metavar='FROM',
                      dest='fromlang',
                       help='language to be parsed in')
    tmpp.add_argument('--log', type=str,
                       help='language in which the logs will be written')
    tmpp.add_argument('--write', '-w', action='store_true',
                      help='write to file')
    tmpp.add_argument('--quite', '-q', action='store_true',
                       help='supress warning messages')
    tmpp.add_argument('--nodisplay', '-n', action='store_true',
                      help="supress output")






RE = re.compile(r'.*?[ :,~\[\]]')

def get_input(input_file):
    """Returns the text to be parsed along with the name assigned to
    that text. The last output is the extension of the file. """
    if input_file is None:
        return sys.stdin.read(), 'STDIN', 'STDIN', 'html'
    if not os.path.exists(input_file):
        error("ERROR: The file '%s' does not exist.\n" % input_file)
    with open(input_file, 'r') as tmpf:
        text = tmpf.read()
    textname = input_file
    path = os.path.realpath(input_file)
    name = os.path.basename(path)
    name = os.path.splitext(name)
    file_name = name[0]
    file_ext = name[1][1:].lower()
    if file_ext == '':
        file_ext = 'html'  # The default language to parse
    return text, textname, file_name, file_ext


def get_lang_style(lang_str, lang='lexor', style='default'):
    """Parses a language string. In particular, the options --from
    and --log. """
    input_lang = lang
    input_style = style
    if lang_str is not None:
        tmp = lang_str.lower().split(':')
        if tmp[0] != '_':
            input_lang = tmp[0]
        if len(tmp) == 2:
            input_style = tmp[1]
            if input_style == '_':
                input_style = 'default'
    return input_lang, input_style


def get_converting_styles(lang, to_lang, caret, output):
    """Assumming that to_lang[caret] is '[' we obtain the converting
    styles. """
    styles = list()
    while caret < len(to_lang):
        match = RE.search(to_lang, caret)
        if match is None:
            msg = "OPTION ERROR (--to): Invalid syntax in '%s'\n" \
                  % to_lang[caret:]
            error(msg)
        cstyle = to_lang[caret:match.end(0)-1].lower()
        if cstyle == '_':
            cstyle = 'default'
        if cstyle == '':
            caret += 1
            continue
        char = to_lang[match.end(0)-1]
        if char == ',':
            styles.append((cstyle, 'default'))
            caret = match.end(0)
            continue
        if char == ']':
            styles.append((cstyle, 'default'))
            caret = match.end(0)
            break
        if char == ':':
            caret = match.end(0)
            match = RE.search(to_lang, caret)
            if match is None:
                msg = "OPTION ERROR (--to): Invalid syntax in '%s'\n" \
                      % to_lang[caret:]
                error(msg)
            wstyle = to_lang[caret:match.end(0)-1].lower()
            if wstyle == '_':
                wstyle = 'default'
            char = to_lang[match.end(0)-1]
            if char == ',':
                styles.append((cstyle, wstyle))
                caret = match.end(0)
                continue
            if char == ']':
                styles.append((cstyle, wstyle))
                caret = match.end(0)
                break
            if char == ':':
                msg = "OPTION ERROR (--to): Invalid syntax in '%s'\n" \
                      % to_lang[caret:]
                error(msg)
            continue
        msg = "OPTION ERROR (--to): Invalid syntax in '%s'\n" \
              % to_lang[caret:]
        error(msg)
    output.append(('c', lang, styles))
    return caret


def get_writing_styles(lang, to_lang, caret, output):
    """Assumming that to_lang[caret] is '~' we obtain the writing
    styles. """
    styles = list()
    while caret < len(to_lang):
        match = RE.search(to_lang, caret)
        if match is None:
            msg = "OPTION ERROR (--to): Invalid syntax in '%s'\n" \
                  % to_lang[caret:]
            error(msg)
        wstyle = to_lang[caret:match.end(0)-1].lower()
        if wstyle == '_':
            wstyle = 'default'
        if wstyle == '':
            caret += 1
            continue
        char = to_lang[match.end(0)-1]
        if char == ',':
            styles.append(wstyle)
            caret = match.end(0)
            continue
        if char == '~':
            styles.append(wstyle)
            caret = match.end(0)
            break
        msg = "OPTION ERROR (--to): Invalid syntax in '%s'\n" \
              % to_lang[caret:]
        error(msg)
    if len(styles) == 0:
        styles.append('default')
    output.append(('w', lang, styles))
    return caret


def get_output_lang(file_ext, to_lang):
    """Parses the option --to (to_lang) to obtain the language to
    which the text will be converted and written to. """
    if to_lang is None:
        return [('w', file_ext, ['default'])]
    caret = 0
    output = list()
    while caret < len(to_lang):
        match = RE.search(to_lang, caret)
        if match is None:
            lang = to_lang[caret:].lower()
            if lang == '_':
                lang = file_ext
            output.append(('c', lang, [('default', 'default')]))
            break
        lang = to_lang[caret:match.end(0)-1].lower()
        if lang == '':
            caret += 1
            continue
        if lang == '_':
            lang = file_ext
        char = to_lang[match.end(0)-1]
        if char == ',':
            output.append(('c', lang, [('default', 'default')]))
            caret = match.end(0)
            continue
        if char == '[':
            caret = match.end(0)
            caret = get_converting_styles(lang, to_lang, caret, output)
            if len(output[-1][2]) == 0:
                output[-1][2].append(('default', 'default'))
        elif char == '~':
            caret = match.end(0)
            caret = get_writing_styles(lang, to_lang, caret, output)
        else:
            print repr(output)
            msg = "OPTION ERROR (--to): Invalid syntax in '%s'\n" \
                  % to_lang[caret:]
            error(msg)
    return output


def parse_command_line(arg):
    """Parse the command line. Assumes arg is obtained using the
    argparse package in the __main__ file. """
    text, textname, filename, fileext = get_input(arg.INPUTFILE)
    inputinfo = get_lang_style(arg.fromlang, fileext, 'default')
    loginfo = get_lang_style(arg.log, 'lexor', 'log')
    output_info = get_output_lang(inputinfo[0], arg.tolang)
    return {
        'text': text,
        'textname': textname,
        'filename': filename,
        'input_lang': inputinfo[0],
        'input_style': inputinfo[1],
        'log_lang': loginfo[0],
        'log_style': loginfo[1],
        'output_info': output_info,
        'write': arg.write,
        'quite': arg.quite,
        'nodisplay': arg.nodisplay
    }

def write_document(writer, doc, fname, opt):
    """Auxilary function for convert_and_write. """
    if opt['nodisplay'] is False:
        writer.write(doc, sys.stdout)
    if opt['write'] is True:
        writer.write(doc, fname)


def write_log(writer, log, opt):
    """Auxilary function for convert_and_write. """
    if opt['quite'] is False and len(log) > 0:
        writer.write(log, sys.stderr)


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


def execute(arg):
    """Execute main command."""
    opt = parse_command_line(arg)
    in_lang = opt['input_lang']
    in_style = opt['input_style']
    try:
        parser = Parser(in_lang, in_style)
    except IOError:
        msg = "ERROR: Parsing style not found: [%s:%s]\n" \
              % (in_lang, in_style)
        error(msg)
    try:
        log_writer = Writer(opt['log_lang'], opt['log_style'])
    except IOError:
        msg = "ERROR: log writing style not found: " \
              "[%s:%s]\n" % (opt['log_lang'], opt['log_style'])
        error(msg)
    parser.parse(opt['text'], opt['textname'])
    write_log(log_writer, parser.log, opt)
    convert_and_write(parser, opt)
