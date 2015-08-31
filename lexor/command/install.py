"""Install

Routine to install a parser/writer/converter style.

"""

import os
import re
import sys
import site
import shutil
import urllib2
import zipfile
import textwrap
import distutils.dir_util
import distutils.errors
import os.path as pth
from glob import iglob
from imp import load_source
from lexor.util.logging import L
from lexor.command import config, disp, LexorError
from lexor.command.cloud import cloud_request
from lexor.util import github


DESC = """
Install a parser/writer/converter style.

"""


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('install', help='install a style',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('style', type=str, nargs="?",
                      help='name of style to install')
    tmpp.add_argument('-u', '--user', action='store_true',
                      help='install in user-site')
    tmpp.add_argument('-g', '--global', action='store_true',
                      help='install globably, requires sudo')
    tmpp.add_argument('--path', type=str, default=None,
                      help='specify the installation path')


def _get_key_typedir(info, install_dir):
    """Helper function for install_style. """
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
    return key, typedir


def install_style(style, install_dir):
    """Install a given style to the install_dir path. """
    if not style.startswith('/'):
        raise NameError('`style` is not an absolute path')
    if not install_dir.startswith('/'):
        raise NameError('`install_dir` is not an absolute path')

    mod = load_source('tmp_mod', style)
    info = mod.INFO
    key, typedir = _get_key_typedir(info, install_dir)
    L.info('module %r will be installed in %r', key, typedir)

    if not pth.exists(typedir):
        try:
            os.makedirs(typedir)
        except OSError:
            msg = 'OSError: unable to create directory %r. ' % typedir
            msg += 'Did you `sudo`?\n'
            raise LexorError(msg)

    moddir = pth.splitext(style)[0]
    base, name = pth.split(moddir)
    if base == '':
        base = '.'

    src = '%s/%s.py' % (base, name)
    dest = '%s/%s.py' % (typedir, name)
    disp('writing %r ... ' % dest)
    try:
        L.info('copying main file %r', src)
        shutil.copyfile(src, dest)
    except OSError:
        L.error('OSError: unable to copy file. Did you `sudo`?')
    disp('done\n')

    src = '%s/%s' % (base, name)
    if pth.exists(src):
        dest = '%s/%s' % (typedir, name)
        disp('writing %s ... ' % dest)
        try:
            L.info('copying auxiliary directory %r', src)
            distutils.dir_util.copy_tree(src, dest)
        except distutils.errors.DistutilsFileError as err:
            L.warn('DistutilsFileError: %r', err.message)
        disp('done\n')

    L.info('compiling modules ...')
    src = '%s/%s.py' % (typedir, name)
    load_source('tmp_mod', src)
    L.info('    - %r', src)

    src = '%s/%s/*.py' % (typedir, name)
    for path in iglob(src):
        load_source('tmp_mod', path)
        L.info('    - %r', path)

    msg = '  -> %r has been installed in %r\n'
    disp(msg % (key, install_dir))


def download_file(url, base='.'):
    """Download a file. """
    try:
        print '-> Retrieving %s' % url
        response = urllib2.urlopen(url)
        local_name = '%s/tmp_%s' % (base, pth.basename(url))
        with open(local_name, "wb") as local_file:
            local_file.write(response.read())
    except urllib2.HTTPError, err:
        print "HTTP Error:", err.code, url
    except urllib2.URLError, err:
        print "URL Error:", err.reason, url
    return local_name


def unzip_file(local_name):
    """Extract the contents of a zip file. """
    zfile = zipfile.ZipFile(local_name)
    dirname = zfile.namelist()[0].split('/')[0]
    zfile.extractall()
    return dirname


def run():
    """Run the command. """
    arg = vars(config.CONFIG['arg'])

    if arg['user']:
        try:
            install_dir = '%s/lib/lexor_modules' % site.getuserbase()
        except AttributeError:
            install_dir = 'lib/lexor_modules'
        L.info('user installation: %r', install_dir)
    elif arg['global']:
        install_dir = '%s/lib/lexor_modules' % sys.prefix
        L.info('global installation: %r', install_dir)
    elif arg['path']:
        install_dir = pth.abspath(arg['path'])
        L.info('custom installation: %r', install_dir)
    else:
        install_dir = pth.join(pth.abspath('.'), 'lexor_modules')
        L.info('default installation: %r', install_dir)

    if arg['style']:
        style_file = arg['style']
        if '.py' not in style_file:
            style_file = '%s.py' % style_file
        if pth.exists(style_file):
            style_file = pth.abspath(style_file)
            L.info('installing local module: %r', style_file)
            install_style(style_file, install_dir)
            return
        info = arg['style'].split('.')
        if len(info) == 3:
            match_parameters = {
                'lang': info[0],
                'type': info[1],
                'style': info[2]
            }
        elif len(info) == 4:
            match_parameters = {
                'lang': info[0],
                'type': info[1],
                'to_lang': info[2],
                'style': info[3]
            }
        else:
            types = ['lang.type.style', 'lang.type.to_lang.style']
            msg = 'invalid module, try %r' % types
            raise LexorError(msg)
        L.info('searching online for %r', info)
        response = cloud_request('match', match_parameters)
        if len(response) == 0:
            L.error('no maches found for %r', info)
            raise LexorError('no matches found')
        if len(response) > 1:
            msg = 'there are %d matches, how did this happen?'
            L.error(msg % len(response))
            raise LexorError('several matches returned')
        info = response[0]
        endpoint = '/repos/{user}/{repo}/tags'.format(
            user=info['user'],
            repo=info['repo']
        )
        response = github.get(endpoint)
        # response should be an array containing all the tags
        print response



    cfg = config.get_cfg(['dependencies'])
    if arg['style'] is None:
        raise LexorError('Needs to check local configuration and install everything')


    
    if not pth.exists('lexor.config'):
        with open('lexor.config', 'w') as _:
            pass
    
    
    cfg = config.get_cfg(['dependencies'])
    arg = config.CONFIG['arg']
    print arg
    print '--------'
    print cfg
    print '----'
    print config.CONFIG
    print '----'

    res = cloud_request('match', {
        'lang': 'lexor',
        'type': 'converter',
        'to_lang': 'html',
        'style': 'default'
    })
    import pprint
    pprint.pprint(res)
    print arg
    exit()


    matches = []
    url = 'http://jmlopez-rod.github.io/lexor-lang/lexor-lang.url'
    print '-> Searching in %s' % url
    response = urllib2.urlopen(url)
    for line in response.readlines():
        name, url = line.split(':', 1)
        if arg.style in name:
            matches.append([name.strip(), url.strip()])

    cwd = os.getcwd()
    for match in matches:
        doc = urllib2.urlopen(match[1]).read()
        links = re.finditer(r' href="?([^\s^"]+)', doc)
        links = [link.group(1) for link in links if '.zip' in link.group(1)]
        for link in links:
            if 'master' in link:
                path = urllib2.urlparse.urlsplit(match[1])
                style_url = '%s://%s%s' % (path[0], path[1], link)
                local_name = download_file(style_url, '.')
                dirname = unzip_file(local_name)
                for path in iglob('%s/*.py' % dirname):
                    install_style(pth.abspath(path), install_dir)
                os.remove(local_name)
                shutil.rmtree(dirname)
