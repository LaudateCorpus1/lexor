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
from glob import iglob, glob
from imp import load_source
from pkg_resources import parse_version
from lexor.util.logging import L
from lexor.command import config, disp, LexorError, exec_cmd
from lexor.command.cloud import cloud_request
from lexor.util import github


DESC = """
Install a parser/writer/converter style.

"""
GITHUB_PATTERN = re.compile(
    r'(?:@|://)github.com[:/]([^/\s]+?)/([^/\s]+?)(?:\.git)?/?$',
    re.IGNORECASE
)


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
    tmpp.add_argument('-s', '--save', action='store_true',
                      help='save dependency')


def decompose(endpoint):
    """Parse an endpoint. Extracted from

        https://github.com/bower/endpoint-parser/blob/master/index.js

    """
    exp = '^(?:([\w\-]|(?:[\w\.\-]+[\w\-])?)=)?([^\|#]+)(?:#(.*))?$'
    matches = re.match(exp, endpoint)
    if not matches:
        raise LexorError('invalid endpoint %r' % endpoint)
    matches = matches.groups()
    name = '' if not matches[0] else matches[0].strip()
    source = '' if not matches[1] else matches[1].strip()
    target = '' if not matches[2] else matches[2].strip()
    is_wild_card = not target or target == '*' or target == 'latest'
    return {
        'name': name,
        'source': source,
        'target': '*' if is_wild_card else target
    }


def get_org_repo_pair(url):
    """Parse a github url returning the organization/user and the
    repo name. """
    matches = re.search(GITHUB_PATTERN, url)
    if not matches:
        return None
    matches = matches.groups()
    org = '' if not matches[0] else matches[0].strip()
    repo = '' if not matches[1] else matches[1].strip()
    return {
        'org': org,
        'repo': repo
    }


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

    msg = '  -> %r v%s has been installed in %r\n'
    disp(msg % (key, info['ver'], install_dir))
    return key, info['ver']


def download_file(url, base='.'):
    """Download a file. """
    try:
        L.info('downloading %s', url)
        response = urllib2.urlopen(url)
        local_name = '%s/tmp_%s' % (base, pth.basename(url))
        with open(local_name, "wb") as local_file:
            local_file.write(response.read())
        return local_name
    except urllib2.HTTPError, err:
        msg = 'HTTP Error [%r]: %r' % (err.code, url)
        L.error(msg)
        raise LexorError(msg)
    except urllib2.URLError, err:
        msg = 'URL Error -> %r: %r' % (err.reason, url)
        L.error(msg)
        raise LexorError(msg)


def unzip_file(local_name):
    """Extract the contents of a zip file. """
    zfile = zipfile.ZipFile(local_name)
    dirname = zfile.namelist()[0].split('/')[0]
    zfile.extractall()
    return dirname


def _get_install_dir(arg):
    """Get the installation directory. """
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
    return install_dir


def _is_local_installation(style_file):
    """Check if the argument exists locally. """
    if '.py' not in style_file:
        style_file = '%s.py' % style_file
    if pth.exists(style_file):
        return pth.abspath(style_file)
    return None


def _parse_key(key):
        info = key.split('.')
        if len(info) == 3:
            return {
                'lang': info[0],
                'type': info[1],
                'style': info[2]
            }
        elif len(info) == 4:
            return {
                'lang': info[0],
                'type': info[1],
                'to_lang': info[2],
                'style': info[3]
            }
        else:
            types = ['lang.type.style', 'lang.type.to_lang.style']
            msg = 'invalid module, try %r' % types
            raise LexorError(msg)


def install_url(style, url, install_dir, version=''):
    """Download and install a zip file"""
    if version and version[0] != 'v':
        version = 'v{0}'.format(version)
    msg = 'installing %s %s ... \n'
    disp(msg % (style, version))
    try:
        local_name = download_file(url)
    except LexorError:
        L.error('something went wrong while downloading ...')
        return
    dirname = unzip_file(local_name)
    source = glob('%s/*.py' % dirname)
    key, ver = install_style(pth.abspath(source[0]), install_dir)
    L.info('removing %r and %r ...', local_name, dirname)
    os.remove(local_name)
    shutil.rmtree(dirname)
    L.info('clean up complete')
    return key, ver


def github_resolver(install_dir, source, target):
    return git_remote_resolver(install_dir, source, target)


def git_remote_resolver(install_dir, source, target):
    L.info('creating temporary directory ...')
    os.mkdir('tmp')
    os.chdir('tmp')
    exec_cmd('git init')
    if target != '*':
        L.info('git pull --tags %s %s', source, target)
        exec_cmd('git pull --tags %s %s' % (source, target))
        exec_cmd('git checkout %s' % target)
    else:
        exec_cmd('git pull %s' % source)
    os.chdir('..')
    source = glob('tmp/*.py')
    info = install_style(pth.abspath(source[0]), install_dir)
    L.info('removing temporary directory ...')
    shutil.rmtree('tmp')
    L.info('clean up complete')
    return info


def url_resolver(install_dir, source, _):
    return install_url(source, source, install_dir)


def local_resolver(install_dir, source, _):
    L.info('installing local module: %r', source)
    return install_style(source, install_dir)


def shorthand_resolver(install_dir, source, target):
    org, repo = source.split('/')
    return _get_github_archive(install_dir, org, repo, target)


def registry_resolver(install_dir, source, target):
    match_parameters = _parse_key(source)
    L.info('searching registry for %r', source)
    response = cloud_request('match', match_parameters)
    if len(response) == 0:
        L.error('no matches found for %r', source)
        return
    if len(response) > 1:
        msg = 'there are %d matches, how did this happen?'
        L.error(msg % len(response))
        return
    info = response[0]
    return _get_github_archive(
        install_dir, info['user'], info['repo'], target
    )


def _get_github_archive(install_dir, org, repo, target):
    if target == '*':
        endpoint = '/repos/{org}/{repo}/tags'.format(
            org=org,
            repo=repo
        )
        response = github.get(endpoint)
        if not isinstance(response, list):
            if 'message' in response:
                msg = 'message from github: %s' % response['message']
                L.error(msg)
            else:
                L.error('unable to git proper response from github.')
            return
        sha = {}
        for item in response:
            key = item['name']
            if key[0] == 'v':
                key = key[1:]
            sha[key] = item['commit']['sha']
        versions = sha.keys()
        versions = sorted(versions, key=parse_version)
        target = sha[versions[-1]]
        L.info('found versions %r', versions)
    url = 'https://github.com/{org}/{repo}/archive/{target}.zip'
    url = url.format(org=org, repo=repo, target=target)
    return install_url(repo, url, install_dir)


def get_resolver(source):
    """Get the resolver for the source. """
    # Git Case: git git+ssh, git+http, git+https
    #           .git at the end (probably ssh shorthand)
    #            git@ at the start
    if re.match('^git(\+(ssh|https?))?://', source) \
            or re.search('\.git/?$', source) \
            or re.match('^git@', source):
        source = re.sub('^git\+', '', source)
        if get_org_repo_pair(source):
            return [github_resolver, source]
        return [git_remote_resolver, source]
    # url
    if re.match('^https?://', source):
        return [url_resolver, source]
    # local
    if pth.exists(source) or pth.exists('%s.py' % source):
        source = source if '.py' in source else '%s.py' % source
        return [local_resolver, pth.abspath(source)]
    # shorthand
    parts = source.split('/')
    if len(parts) == 2:
        return [shorthand_resolver, source]
    # registry
    return [registry_resolver, source]


def handle_argument(install_dir, param, save):
    dec_endpoint = decompose(param)
    source = dec_endpoint['source']
    target = dec_endpoint['target']
    resolver, source = get_resolver(source)
    info = resolver(install_dir, source, target)
    if save:
        if info is None:
            return
        cfg = config.read_config()
        endpt = dec_endpoint
        if endpt['target'] != '*':
            endpt['target'] = '#{0}'.format(endpt['target'])
        else:
            endpt['target'] = ''
        source = '%s%s' % (endpt['source'], endpt['target'])
        dep = 'dependencies'
        try:
            cfg[dep][info[0]] = source
        except KeyError:
            cfg.add_section(dep)
            cfg[dep][info[0]] = source
        config.write_config(cfg)


def run():
    """Run the command. """
    arg = vars(config.CONFIG['arg'])
    install_dir = _get_install_dir(arg)

    if arg['style']:
        return handle_argument(install_dir, arg['style'], arg['save'])
    else:
        cfg = config.get_cfg(['dependencies'])
        for key in cfg['dependencies']:
            handle_argument(
                install_dir,
                cfg['dependencies'][key],
                False
            )
