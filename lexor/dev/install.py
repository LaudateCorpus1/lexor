"""Install

Routine to install a parser/writer/converter style.

"""

import os
import sys
import site
import shutil
import distutils.dir_util
from glob import iglob
from imp import load_source
from zipfile import ZipFile
from lexor.dev import error, warn
from lexor.config import read_config, write_config

__all__ = ['run']


def install_style(style, install_dir):
    """Install a given style to the install_dir path. """
    mod = load_source('tmp_mod', style)
    info = mod.INFO
    if info['to_lang']:
        key = '%s.%s.%s.%s' % (info['lang'], info['type'], 
                               info['to_lang'], info['style'])
        typedir = '%s/%s.%s.%s' 
        typedir = typedir % (install_dir, info['lang'], info['type'], 
                             info['to_lang'])
    else:
        key = '%s.%s.%s' % (info['lang'], info['type'], info['style'])
        typedir = '%s/%s.%s' 
        typedir = typedir % (install_dir, info['lang'], info['type'])

    if not os.path.exists(typedir):
        os.makedirs(typedir)
    
    moddir = os.path.splitext(style)[0]
    base, name = os.path.split(moddir)
    if base == '':
        base = '.'
    
    print 'installing...'
    
    # Copy main file
    old = '%s/%s.py' % (base, name)
    new = '%s/%s-%s.py' % (typedir, name, info['ver'])
    print new
    shutil.copyfile(old, new)
    
    # Copy auxilary modules
    old = '%s/%s' % (base, name)
    new = '%s/%s-%s' % (typedir, name, info['ver'])
    print new
    distutils.dir_util.copy_tree(old, new)
    
    # Compile the style
    new = '%s/%s-%s.py' % (typedir, name, info['ver'])
    load_source('tmp_mod', new)
    
    # Compile the rest
    new = '%s/%s-%s/*.py' % (typedir, name, info['ver'])
    for path in iglob(new):
        load_source('tmp_mod', path)
    
    # Check if its on development
    config = read_config()
    if 'develop' in config:
        if key in config['develop']:
            del config['develop'][key]
    
    if 'version' in config:
        config['version'][key] = info['ver']
    else:
        config.add_section('version')
        config['version'][key] = info['ver']
    
    # Write configuration
    write_config(config)
    
def run(argp):
    """Create a source distribution. """
    if argp.user:
        install_dir = '%s/lib/lexor' % site.getuserbase()
    else:
        install_dir = '%s/lib/lexor' % sys.prefix

    style = argp.style    
    if '.py' not in style:
        style = '%s.py' % style
    if not os.path.exists(style):
        error("ERROR: No such file or directory\n")

    install_style(style, install_dir)
