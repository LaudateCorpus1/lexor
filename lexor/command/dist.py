"""Distribute

Package a style along with auxiliary and test files.

"""

import os
import textwrap
from glob import iglob
from imp import load_source
from zipfile import ZipFile
from lexor.command import error, warn
import lexor.command.config as config

DEFAULTS = {
    'path': '.'
}

DESC = """
Distribute a style along with auxiliary and test files.

"""


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('dist', help='distribute a style',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('style', type=str,
                      help='name of style to distribute')
    tmpp.add_argument('--path', type=str,
                      help='distribution directory')


def run():
    """Run the command. """
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
        error("ERROR: No such file or directory.\n")

    moddir = os.path.splitext(style)[0]
    base, name = os.path.split(moddir)
    if base == '':
        base = '.'

    mod = load_source('tmp_name', style)
    info = mod.INFO
    if info['to_lang']:
        filename = '%s/lexor.%s.%s.%s.%s-%s.zip'
        filename = filename % (dirpath, info['lang'], info['type'],
                               info['to_lang'], info['style'], info['ver'])
    else:
        filename = '%s/lexor.%s.%s.%s-%s.zip'
        filename = filename % (dirpath, info['lang'], info['type'],
                               info['style'], info['ver'])

    warn('Writing %s ...\n' % filename)
    zipf = ZipFile(filename, 'w')
    warn(' including %s\n' % style)
    zipf.write(style)
    for path in iglob('%s/*.py' % moddir):
        warn(' including %s\n' % path)
        zipf.write(path)
    for path in iglob('%s/test_%s/*.py' % (base, name)):
        warn(' including %s\n' % path)
        zipf.write(path)
    zipf.close()
