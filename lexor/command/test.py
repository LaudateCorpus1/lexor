"""Lexor Test

This module contains various test for lexor. All the tests should be
run with every release to make sure that everything is working as
advertised.

To run do: nosetests -v -s

"""

from os.path import dirname
import sys
import re
import textwrap
import lexor

__all__ = ['WRAPPER', 'print_log', 'parse_write', 'parse_convert_write']

WRAPPER = textwrap.TextWrapper(width=70, break_long_words=False)


def print_log(node):
    """Display the error obtained from parsing. """
    pos = node['position']
    sys.stderr.write('\n  Line %d, Column %d ' % (pos[0], pos[1]))
    sys.stderr.write('in %s:\n      ' % node['file'])
    tmp = re.sub(r"\s+", " ", node['message'])
    sys.stderr.write('\n      '.join(WRAPPER.wrap(tmp)))
    sys.stderr.write('\n\n ... ')


def parse_write(callerfile, in_, out_, style, lang):
    """Provide the filename as the input and the style you wish
    to compare it against. """
    inputfile = "%s/../%s" % (dirname(callerfile), in_)
    with open(inputfile) as tmpf:
        text = tmpf.read()
    sys.stderr.write('\n%s\n%s' % ('='*70, text))
    sys.stderr.write('%s\n' % ('-'*50))
    outputfile = "%s/%s.%s.%s" % (dirname(callerfile), out_, style, lang)
    with open(outputfile) as tmpf:
        text = tmpf.read()
    doc, log = lexor.read(inputfile)
    doc.style = style
    lexor.write(log, sys.stderr)
    sys.stderr.write('\n%s\n' % ('-'*50))
    lexor.write(doc, sys.stderr)
    sys.stderr.write('\n%s\n' % ('='*70))
    return str(doc), text


def parse_convert_write(callerfile, in_, out_, style, tolang):
    """Provide the filename as the input and the style you wish
    to compare it against. """
    inputfile = "%s/../%s" % (dirname(callerfile), in_)
    with open(inputfile) as tmpf:
        text = tmpf.read()
    sys.stderr.write('\n%s\n%s' % ('='*70, text))
    sys.stderr.write('%s\n' % ('-'*50))
    outputfile = "%s/%s.%s.%s" % (dirname(callerfile), out_, style, tolang)
    with open(outputfile) as tmpf:
        text = tmpf.read()
    doc, log = lexor.read(inputfile)
    doc.style = 'default'
    newdoc, newlog = lexor.convert(doc, tolang, style)
    lexor.write(log, sys.stderr)
    lexor.write(newlog, sys.stderr)
    sys.stderr.write('\n%s\n' % ('-'*50))
    lexor.write(newdoc, sys.stderr)
    sys.stderr.write('\n%s\n' % ('='*70))
    return str(newdoc), text
