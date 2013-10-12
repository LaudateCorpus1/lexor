"""Distribute

Package a style along with auxiliary and test files.

"""

import os
from glob import iglob
from imp import load_source
from zipfile import ZipFile
from lexor.dev import error, warn

__all__ = ['run']


def run(argp):
    """Create a source distribution. """
    style = argp.style
    if argp.dir:
        dirpath = argp.dir
    else:
        dirpath = '.'

    if '.py' not in style:
        style = '%s.py' % style
    if not os.path.exists(style):
        error("ERROR: No such file or directory\n")

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
