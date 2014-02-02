"""Install

Routine to install a parser/writer/converter style.

"""

import os
import sys
import site
import shutil
import textwrap
import distutils.dir_util
from glob import iglob
from imp import load_source
from lexor.command import error
import lexor.command.config as config

DESC = """
Install a parser/writer/converter style.

"""


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('install', help='install a style',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('style', type=str,
                      help='name of style to install')
    tmpp.add_argument('--user', action='store_true',
                      help='install in user-site')
    tmpp.add_argument('--path', type=str,
                      help='specify the installation path')


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
        try:
            os.makedirs(typedir)
        except OSError:
            msg = 'OSError: unable to create directory. Did you `sudo`?\n'
            error(msg)

    moddir = os.path.splitext(style)[0]
    base, name = os.path.split(moddir)
    if base == '':
        base = '.'

    # Copy main file
    old = '%s/%s.py' % (base, name)
    new = '%s/%s-%s.py' % (typedir, name, info['ver'])
    sys.stdout.write('writing %s ... ' % new)
    try:
        shutil.copyfile(old, new)
    except OSError:
        msg = 'OSError: unable to copy file. Did you `sudo`?\n'
    sys.stdout.write('done\n')

    # Copy auxilary modules
    old = '%s/%s' % (base, name)
    new = '%s/%s-%s' % (typedir, name, info['ver'])
    sys.stdout.write('writing %s/* ... ' % new)
    distutils.dir_util.copy_tree(old, new)
    sys.stdout.write('done\n')

    # Compile the style
    new = '%s/%s-%s.py' % (typedir, name, info['ver'])
    load_source('tmp_mod', new)

    # Compile the rest
    new = '%s/%s-%s/*.py' % (typedir, name, info['ver'])
    for path in iglob(new):
        load_source('tmp_mod', path)

    # Check if its on development
    cfg_file = config.read_config()
    if 'develop' in cfg_file:
        if key in cfg_file['develop']:
            del cfg_file['develop'][key]

    if 'version' in cfg_file:
        cfg_file['version'][key] = info['ver']
    else:
        cfg_file.add_section('version')
        cfg_file['version'][key] = info['ver']

    # Write configuration
    config.write_config(cfg_file)


def run():
    """Run the command. """
    arg = config.CONFIG['arg']
    if arg.path:
        install_dir = arg.path
    elif arg.user:
        install_dir = '%s/lib/lexor' % site.getuserbase()
    else:
        install_dir = '%s/lib/lexor' % sys.prefix

    style = arg.style
    if '.py' not in style:
        style = '%s.py' % style
    if not os.path.exists(style):
        error("ERROR: No such file or directory\n")

    install_style(style, install_dir)
