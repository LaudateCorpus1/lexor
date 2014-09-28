"""Config

This module is in charge of providing all the necessary settings to
the rest of the modules in lexor.

"""

import os
import sys
import argparse
import textwrap
import configparser
from lexor.command import error, import_mod


DESC = """View and edit a configuration file for lexor.

Some actions performed by lexor can be overwritten by using
configuration files.

To see the values that the configuration file can overwrite use the
`defaults` command. This will print a list of the keys and values
lexor uses for the given command.

"""

CONFIG = {
    'path': None,  # read only
    'name': None,  # read only
    'cfg_path': None,  # COMMAND LINE USE ONLY
    'cfg_user': None,  # COMMAND LINE USE ONLY
    'arg': None  # COMMAND LINE USE ONLY
}


def var_completer(**_):
    """var completer. """
    return ['SEC.KEY']


def value_completer(**_):
    """value completer. """
    return ['VALUE']


class ConfigDispAction(argparse.Action):  # pylint: disable=R0903
    """Derived argparse Action class to use when displaying the
    configuration file and location."""
    def __call__(self, parser, namespace, values, option_string=None):
        global CONFIG
        CONFIG['cfg_user'] = namespace.cfg_user
        CONFIG['cfg_path'] = namespace.cfg_path
        cfg_file = read_config()
        fname = '%s/%s' % (CONFIG['path'], CONFIG['name'])
        print('lexor configuration file: %s' % fname)
        cfg_file.write(sys.stdout)
        exit(0)


def add_parser(subp, fclass):
    "Add a parser to the main subparser. "
    tmpp = subp.add_parser('config', help='configure lexor',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('var', type=str,
                      help='Must be in the form of sec.key'
                      ).completer = var_completer
    tmpp.add_argument('value', type=str, nargs='?', default=None,
                      help='var value').completer = value_completer
    tmpp.add_argument('-v', action='store_true',
                      help='print config file location')
    tmpp.add_argument('--display', action=ConfigDispAction,
                      nargs=0,
                      help='print config file and exit')


def read_config():
    """Read a configuration file."""
    cfg_file = configparser.ConfigParser(allow_no_value=True)
    name = 'lexor.config'
    if CONFIG['cfg_user']:
        path = os.environ['HOME']
        name = '.lexor.config'
    elif CONFIG['cfg_path'] is None:
        path = '.'
        if not os.path.exists(name):
            if 'LEXOR_CONFIG_PATH' in os.environ:
                path = os.environ['LEXOR_CONFIG_PATH']
            else:
                path = os.environ['HOME']
                name = '.lexor.config'
    else:
        path = CONFIG['cfg_path']
        if not os.path.exists('%s/%s' % (path, name)):
            error("ERROR: %s/%s does not exist.\n" % (path, name))
    cfg_file.read('%s/%s' % (path, name))
    CONFIG['name'] = name
    CONFIG['path'] = path
    return cfg_file


def write_config(cfg_file):
    "Write the configuration file. "
    fname = '%s/%s' % (CONFIG['path'], CONFIG['name'])
    with open(fname, 'w') as tmp:
        cfg_file.write(tmp)


def run():
    "Run command. "
    arg = CONFIG['arg']
    cfg_file = read_config()
    try:
        command, var = arg.var.split('.', 1)
    except ValueError:
        error("ERROR: '%s' is not of the form sec.key\n" % arg.var)
    if arg.v:
        fname = '%s/%s' % (CONFIG['path'], CONFIG['name'])
        print('lexor configuration file: %s' % fname)
    if arg.value is None:
        try:
            print cfg_file[command][var]
        except KeyError:
            pass
        return
    try:
        cfg_file[command][var] = arg.value
    except KeyError:
        cfg_file.add_section(command)
        cfg_file[command][var] = arg.value
    write_config(cfg_file)


def update_single(cfg, name, defaults=None):
    "Helper function for get_cfg."
    if defaults:
        for var, val in defaults.iteritems():
            cfg[name][var] = os.path.expandvars(str(val))
    else:
        try:
            mod = import_mod('lexor.command.%s' % name)
            if hasattr(mod, "DEFAULTS"):
                for var, val in mod.DEFAULTS.iteritems():
                    cfg[name][var] = os.path.expandvars(val)
        except ImportError:
            pass


def _update_from_file(cfg, name, cfg_file):
    "Helper function for get_cfg."
    if name in cfg_file:
        for var, val in cfg_file[name].iteritems():
            cfg[name][var] = os.path.expandvars(val)


def _update_from_arg(cfg, argdict, key):
    "Helper function for get_cfg."
    for var in cfg[key]:
        if var in argdict and argdict[var] is not None:
            cfg[key][var] = argdict[var]


def get_cfg(names, defaults=None):
    "Obtain settings from the configuration file."
    cfg = {
        'lexor': {
            'path': ''
        }
    }
    cfg_file = read_config()
    if 'lexor' in cfg_file:
        for var, val in cfg_file['lexor'].iteritems():
            cfg['lexor'][var] = os.path.expandvars(val)
    cfg['lexor']['root'] = CONFIG['path']
    if isinstance(names, list):
        for name in names:
            cfg[name] = dict()
            update_single(cfg, name)
            _update_from_file(cfg, name, cfg_file)
    else:
        if names != 'lexor':
            cfg[names] = dict()
            update_single(cfg, names, defaults)
            _update_from_file(cfg, names, cfg_file)
    if CONFIG['arg']:
        argdict = vars(CONFIG['arg'])
        if argdict['parser_name'] in cfg:
            _update_from_arg(cfg, argdict, argdict['parser_name'])
        _update_from_arg(cfg, argdict, 'lexor')
        CONFIG['arg'] = None
    return cfg


def set_style_cfg(obj, name, defaults):
    """Given an obj, this can be a Parser, Converter or Writer. It
    sets the attribute defaults to the specified defaults in the
    configuration file or by the user by overwriting values in the
    parameter defaults."""
    obj.defaults = dict()
    if hasattr(obj.style_module, 'DEFAULTS'):
        mod_defaults = obj.style_module.DEFAULTS
        for var, val in mod_defaults.iteritems():
            obj.defaults[var] = os.path.expandvars(str(val))
    cfg_file = read_config()
    if name in cfg_file:
        for var, val in cfg_file[name].iteritems():
            obj.defaults[var] = os.path.expandvars(val)
    if defaults:
        for var, val in defaults.iteritems():
            obj.defaults[var] = val
