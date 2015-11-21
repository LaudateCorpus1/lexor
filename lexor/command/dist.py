"""
Package a style along with auxiliary and test files.

"""
import os
import textwrap
from glob import iglob
from imp import load_source
from zipfile import ZipFile
from lexor.command import config, disp, LexorError
from lexor.util.logging import L


DEFAULTS = {
    'path': '.'
}
DESC = """
Distribute a style along with auxiliary and test files.

"""


def add_parser(subp, fclass):
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Add a parser to the main subparser.
    """
    tmpp = subp.add_parser('dist', help='distribute a style',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument(
        'style', type=str, help='name of style to distribute'
    )
    tmpp.add_argument(
        '--path', type=str,
        help='directoy where zip file will be placed'
    )


def run():
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Run the command.
    """
    arg = config.CONFIG['arg']
    cfg = config.get_cfg('dist', DEFAULTS)
    root = cfg['lexor']['root']
    path = cfg['dist']['path']

    style = arg.style
    if path[0] in ['/', '.']:
        dirpath = path
    else:
        dirpath = '%s/%s' % (root, path)

    if '.py' not in style:
        style = '%s.py' % style
    if not os.path.exists(style):
        raise LexorError('no such file or directory: %r' % style)

    moddir = os.path.splitext(style)[0]
    base, name = os.path.split(moddir)
    if base == '':
        base = '.'

    mod = load_source('tmp_name', style)
    info = mod.INFO
    if info['to_lang']:
        filename = '%s/lexor.%s.%s.%s.%s-%s.zip'
        filename %= (dirpath, info['lang'], info['type'],
                     info['to_lang'], info['style'], info['ver'])
    else:
        filename = '%s/lexor.%s.%s.%s-%s.zip'
        filename %= (dirpath, info['lang'], info['type'],
                     info['style'], info['ver'])

    disp('Writing %s ...\n' % filename)
    zipf = ZipFile(filename, 'w')
    disp('  attaching %s\n' % style)
    zipf.write(style)
    L.info('added %r', style)
    for path in iglob('%s/*.py' % moddir):
        disp('  attaching %s\n' % path)
        zipf.write(path)
        L.info('  added %r', path)
    for path in iglob('%s/test_%s/*.py' % (base, name)):
        disp('  attaching %s\n' % path)
        zipf.write(path)
        L.info('  added %r', path)
    zipf.close()
