"""to

Execute lexor by transforming a file "to" another language.

"""

import re
import os
import sys
import textwrap
import argparse
from lexor.util.logging import L
from lexor.command import config, LexorError
from lexor.core.parser import Parser
from lexor.core.writer import Writer
from lexor.core.converter import Converter


DEFAULTS = {
    'parse_lang': 'lexor:_',
    'log': 'lexor:log',
    'lang': 'html[_:_]'
}

DESC = """
Transform the inputfile to another language. To see the available
languages use the `lang` command.

examples:

    lexor file.html to markdown[cstyle:wstyle]
    lexor file.html to markdown[cstyle:otherlang.wstyle]
    lexor file.html to html~min,plain,_~
    lexor file.html to html~plain,_~ mk[cstyle:wstyle,cstyle1,cstyle2]

    lexor file.xml to xml~_@tab="****"~

    lexor Makefile to xml --from makefile
    lexor Makefile to xml --from makefile:otherstyle

  Store output to `output.html` and store warnings in `log.html`:
      lexor doc.md > output.html 2> log.html

  Pipe the output from another program:
       cat doc.md | lexor --from markdown

  Write to files without displaying output:
      lexor --quiet --nodisplay --write doc.md

"""


def split_at(delimiter, text, opens='[<(', closes=']>)', quotes='"\''):
    """Custom function to split at commas. Taken from stackoverflow
    http://stackoverflow.com/a/20599372/788553"""
    result = []
    buff = ""
    level = 0
    is_quoted = False
    for char in text:
        if char in delimiter and level == 0 and not is_quoted:
            result.append(buff)
            buff = ""
        else:
            buff += char
            if char in opens:
                level += 1
            elif char in closes:
                level -= 1
            elif char in quotes:
                is_quoted = not is_quoted
    if not buff == "":
        result.append(buff)
    return result


def language_style(lang_str):
    """Parses a language string. In particular, the options --from
    and --log. """
    tmp = split_at(':', lang_str.lower())
    if len(tmp) == 2:
        input_lang = tmp[0]
        input_style = style_parameters(tmp[1])
    else:
        index = tmp[0].find('@')
        if index == -1:
            input_lang = tmp[0]
            input_style = style_parameters('_')
        else:
            input_lang = tmp[0][:index]
            input_style = style_parameters(tmp[0][index:])
    if input_lang == '':
        input_lang = '_'
    if input_style['name'] == '':
        input_style['name'] = '_'
    return input_lang, input_style


def parse_styles(lang_str):
    """Parses a language string. In particular, the options --from
    and --log. """
    tmp = split_at(':', lang_str)
    if len(tmp) == 2:
        cstyle = style_parameters(tmp[0])
        wstyle = style_parameters(tmp[1])
    else:
        cstyle = style_parameters(tmp[0])
        wstyle = style_parameters('_')
    if cstyle['name'] == '':
        cstyle['name'] = '_'
    if wstyle['name'] == '':
        wstyle['name'] = '_'
    return cstyle, wstyle


def style_parameters(style):
    """Parsers a style name along with its parameters. """
    style = split_at('@', style)
    style_dict = {'name': style[0], 'params': dict()}
    for ele in style[1:]:
        try:
            var, val = ele.split('=')
        except ValueError:
            msg = 'style arguments must be of the form @var=val'
            raise argparse.ArgumentTypeError(msg)
        try:
            if val[0] == '[':
                val = val[1:-1]
        except IndexError:
            msg = 'To give empty values try @var=[]'
            raise argparse.ArgumentTypeError(msg)
        style_dict['params'][var] = val
    return style_dict


def input_language(tolang):
    """Parses the tolang argument. """
    type_ = 'w'
    match = re.match("(.+)~(.+)~", tolang)
    if not match:
        type_ = 'c'
        index = tolang.find('[')
        if index == -1:
            if tolang[-1] == ']':
                msg = 'did you mean to write lang[...]?'
                raise argparse.ArgumentTypeError(msg)
            lang_name = tolang
            styles = '_'
        else:
            if tolang[-1] != ']':
                msg = 'must be of the form lang[...] or lang~...~'
                raise argparse.ArgumentTypeError(msg)
            lang_name = tolang[:index]
            styles = tolang[index+1:-1]
    else:
        lang_name, styles = match.groups()
    if type_ == 'w':
        msg = '`:` is not supported in "%s~%s~"' % (lang_name, styles)
        styles = split_at(',', styles)
        for style in styles:
            if ':' in style:
                pass
                # raise argparse.ArgumentTypeError(msg)
        styles = [style_parameters(ele) for ele in styles]
    else:
        styles = [parse_styles(ele) for ele in split_at(',', styles)]
    return type_, lang_name, styles


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('to',
                           help='transform inputfile to another language',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('tolang', metavar='lang', nargs='*',
                      type=input_language,
                      help='language to which it will be converted')
    tmpp.add_argument('--from', type=language_style, metavar='FROM',
                      dest='parse_lang',
                      help='language to be parsed in')
    tmpp.add_argument('--log', type=language_style,
                      help='language in which the logs will be written')
    tmpp.add_argument('--write', '-w', action='store_true',
                      help='write to file')
    tmpp.add_argument('--quiet', '-q', action='store_true',
                      help='suppress warning messages')
    tmpp.add_argument('--nodisplay', '-n', action='store_true',
                      help="suppress output")


def get_input(input_file, default='_'):
    """Returns the text to be parsed along with the name assigned to
    that text. The last output is the extension of the file. """
    if input_file is '_':
        L.info('reading input from stdin')
        return sys.stdin.read(), 'STDIN', 'STDIN', default
    L.info('checking existance of `%s`', input_file)
    if not os.path.exists(input_file):
        raise LexorError('`%s` does not exist' % input_file)
    text = open(input_file).read()
    textname = input_file
    path = os.path.realpath(input_file)
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
    cfg = config.get_cfg(['to'])
    text, t_name, f_name, f_ext = get_input(arg.inputfile)

    parse_lang = cfg['to']['parse_lang']
    if isinstance(parse_lang, str):
        parse_lang = language_style(parse_lang)
    if arg.parse_lang is None and f_ext != '_':
        parse_lang = (f_ext, parse_lang[1])
    in_lang, in_style = parse_lang

    log = cfg['to']['log']
    if isinstance(log, str):
        log = language_style(log)
    else:
        default_log = DEFAULTS['log'].split(':')
        if log[0] == '_':
            log = (default_log[0], log[1])
        if log[1]['name'] == '_':
            log[1]['name'] = default_log[1]

    parser = Parser(in_lang, in_style['name'], in_style['params'])
    log_writer = Writer(log[0], log[1]['name'], log[1]['params'])
    try:
        parser.parse(text, t_name)
    except ImportError:
        msg = 'Parsing style not found: [%s:%s]'
        raise LexorError(msg % (in_lang, in_style['name']))
    try:
        write_log(log_writer, parser.log, arg.quiet)
    except ImportError:
        msg = "ERROR: Writing log style not found: [%s:%s]\n"
        raise LexorError(msg % (parser.log.lang, parser.log.style))
    if not arg.tolang:
        arg.tolang.append(input_language(cfg['to']['lang']))
    convert_and_write(f_name, parser, in_lang, log, arg)


def convert_and_write(f_name, parser, in_lang, log, arg):
    """Auxiliary function to reduce the number of branches in run. """
    log_writer = Writer(log[0], log[1]['name'], log[1]['params'])
    writer = Writer()
    converter = Converter()
    param = {
        'parser': parser,
        'converter': converter,
        'writer': writer,
        'log_writer': log_writer,
        'f_name': f_name,
        'in_lang': in_lang,
        'arg': arg
    }
    for (action, lang, styles) in arg.tolang:
        param['styles'] = styles
        param['lang'] = lang
        if action == 'c':
            run_converter(param)
        if action == 'w':
            run_writer(param)


def write_log(writer, log, quiet):
    """Write the log file to stderr. """
    if quiet is False and len(log) > 0:
        writer.write(log, sys.stderr)


def write_document(writer, doc, fname, arg):
    """Auxiliary function for convert_and_write. """
    if arg.nodisplay is False:
        writer.write(doc, sys.stdout)
    if arg.write is True:
        writer.write(doc, fname)


def run_converter(param):
    """Auxiliary function for convert and write. """
    lang = param['lang']
    f_name = param['f_name']
    in_lang = param['in_lang']
    arg = param['arg']
    parser = param['parser']
    writer = param['writer']
    log_writer = param['log_writer']
    for style in param['styles']:
        cstyle = style[0]['name']
        param['converter'].set(in_lang, lang, cstyle, style[0]['params'])
        try:
            doc, log = param['converter'].convert(parser.doc)
        except ImportError:
            msg = 'converting style not found: [%s ==> %s:%s]'
            L.warn(msg % (in_lang, lang, cstyle))
            continue
        wstyle = style[1]['name']
        if '.' in wstyle:
            (lang, wstyle) = wstyle.split('.')
        if wstyle == '_':
            wstyle = 'default'
        writer.set(lang, wstyle, style[1]['params'])
        fname = '%s.%s.%s' % (f_name, wstyle, lang)
        write_log(log_writer, log, arg.quiet)
        try:
            write_document(writer, doc, fname, arg)
        except ImportError:
            msg = 'writing style not found: [%s:%s]'
            L.warn(msg % (lang, wstyle))
            continue


def run_writer(param):
    """Auxiliary function for convert and write. """
    lang = param['lang']
    f_name = param['f_name']
    arg = param['arg']
    parser = param['parser']
    writer = param['writer']
    for style in param['styles']:
        sname = 'default' if style['name'] == '_' else style['name']
        writer.set(lang, style['name'], style['params'])
        fname = '%s.%s.%s' % (f_name, sname, lang)
        try:
            write_document(writer, parser.doc, fname, arg)
        except ImportError:
            msg = 'writing style not found: [%s:%s]'
            L.warn(msg % (lang, style['name']))
