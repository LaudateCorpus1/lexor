"""
This module is in charge of providing all the necessary settings to
the rest of the modules in lexor.

The config module comes with global variable ``CONFIG`` which is
meant to be read only. This variable is a dictionary with the
following keys:

- ``path``: The path to the configuration file
- ``name``: The name of the configuration file (lexor.config)
- ``cfg_path``
- ``cfg_user``
- ``arg``

The last three keys are meant to be used for the command line, but
they can come in handy in scripts if we need to specify the location
of the configuration file.

"""
import os
import sys
import argparse
import textwrap
import configparser
import os.path as pth
from lexor.util.logging import L
from lexor.command import import_mod, LexorError, disp


DESC = """
view and edit a configuration file for lexor.

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
    'arg': None,  # COMMAND LINE USE ONLY
    'cache': None,  # read_config USE ONLY
}


# pylint: disable=too-few-public-methods
class _ConfigDispAction(argparse.Action):
    """Derived argparse Action class to use when displaying the
    configuration file and location."""
    def __call__(self, parser, namespace, values, option_string=None):
        CONFIG['cfg_user'] = namespace.cfg_user
        CONFIG['cfg_path'] = namespace.cfg_path
        cfg_file = read_config()
        fname = '%s/%s' % (CONFIG['path'], CONFIG['name'])
        disp('lexor configuration file: %s\n' % fname)
        cfg_file.write(sys.stdout)
        exit(0)


def add_parser(subp, fclass):
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Add a parser to the main sub-parser.
    """
    tmpp = subp.add_parser('config', help='configure lexor',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('var', type=str,
                      help='Must be in the form of sec.key')
    tmpp.add_argument('value', type=str, nargs='?', default=None,
                      help='var value')
    tmpp.add_argument('-v', action='store_true',
                      help='print config file location')
    tmpp.add_argument('--display', action=_ConfigDispAction,
                      nargs=0,
                      help='print config file and exit')


def run():
    """
    .. admonition:: Command Line Utility Function
        :class: warning

        Run the command.
    """
    arg = CONFIG['arg']
    cfg_file = read_config()
    try:
        command, var = arg.var.split('.', 1)
    except ValueError:
        raise LexorError("'%s' is not of the form sec.key" % arg.var)
    if arg.v:
        fname = '%s/%s' % (CONFIG['path'], CONFIG['name'])
        disp('lexor configuration file: %s\n' % fname)
    if arg.value is None:
        L.info('displaying value for `%s` and exiting' % var)
        try:
            disp('%s\n' % cfg_file[command][var])
        except KeyError:
            pass
        return
    try:
        cfg_file[command][var] = arg.value
    except KeyError:
        L.info('adding section `%s`' % command)
        cfg_file.add_section(command)
        cfg_file[command][var] = arg.value
    L.info('added key `%s`' % var)
    L.info('writing configuration file')
    write_config(cfg_file)


def read_config(cache=True):
    """Read a configuration file. There are a few ways of specifying
    which configuration file to use.

    - Setting ``CONFIG['cfg_user']`` to ``True`` will read the file
      ``~/.lexor.config``. This variable is set to true in the
      command line by using ``--cfg-user``.

    - Specifying a path via ``CONFIG['cfg_path']`` reads the file
      ``lexor.config`` in the specified path. We can set this
      variable in the command line via the option ``--cfg``.

    - If no path is specified by ``CONFIG['cfg_path']`` then it
      searches for ``lexor.config`` in the current directory. If this
      fails then it will attempt to look for ``lexor.config`` in the
      path specified by the environmental variable
      ``LEXOR_CONFIG_PATH``.

    - If everything else fails then it searches for ``.lexor.config``
      in the home directory.

    This function may raise a :class:`~lexor.command.LexorError`
    exception if the configuration is not found when
    ``CONFIG['cfg_path']`` is set.

    .. note::

        If you must read a specific configuration file via a script
        you can import ``lexor.command.config`` and then set
        ``'cfg_path'``. For instance::

            from lexor.command import config
            config.CONFIG['cfg_path'] = 'path/to/config/file'
            print config.read_config()

        If only the ``CONFIG`` variable is imported then the changes
        will not propagate to the module. That is, if we were to
        do::

            from lexor.command.config import CONFIG
            CONFIG['cfg_path'] = 'path/to/config/file'
            print config.read_config()

        then the module will not be aware of the file since
        ``CONFIG`` is a copy of the ``CONFIG`` variable in the
        ``config`` module.

    """
    if cache and CONFIG['cache'] is not None:
        L.info('reading cached configuration')
        return CONFIG['cache']
    cfg_file = configparser.ConfigParser(allow_no_value=True)
    name = 'lexor.config'
    if CONFIG['cfg_user']:
        path = os.environ['HOME']
        name = '.lexor.config'
    elif CONFIG['cfg_path'] is None:
        path = '.'
        if not pth.exists(name):
            if 'LEXOR_CONFIG_PATH' in os.environ:
                path = os.environ['LEXOR_CONFIG_PATH']
            else:
                path = os.environ['HOME']
                name = '.lexor.config'
    else:
        path = CONFIG['cfg_path']
        if not pth.exists('%s/%s' % (path, name)):
            raise LexorError('%s/%s does not exist.' % (path, name))
    cfg_file.read('%s/%s' % (path, name))
    CONFIG['name'] = name
    CONFIG['path'] = path
    CONFIG['cache'] = cfg_file
    L.info('loaded configuration `%s` from `%s`', name, path)
    return cfg_file


def write_config(cfg_file):
    """Write the configuration file. The input to this function
    should be the object returned by :func:`read_config`. This will
    write the changes made to the configuration in the location
    specified by the ``CONFIG`` global variable in the config module.
    """
    fname = '%s/%s' % (CONFIG['path'], CONFIG['name'])
    with open(fname, 'w') as tmp:
        cfg_file.write(tmp)
    L.info('wrote configuration file `%s`', fname)


def update_single(cfg, name, defaults=None):
    """Update the specified section in configuration (``name``) with
    the ``defaults`` provided. If no defaults are provided then it
    will attempt to look for a lexor command and obtain its defaults
    so that ``cfg`` may be updated."""
    if defaults:
        for var, val in defaults.iteritems():
            cfg[name][var] = pth.expandvars(str(val))
    else:
        try:
            mod = import_mod('lexor.command.%s' % name)
            if hasattr(mod, "DEFAULTS"):
                for var, val in mod.DEFAULTS.iteritems():
                    cfg[name][var] = pth.expandvars(val)
        except ImportError:
            pass


def _update_from_file(cfg, name, cfg_file):
    "Helper function for get_cfg."
    if name in cfg_file:
        for var, val in cfg_file[name].iteritems():
            cfg[name][var] = pth.expandvars(val)


def _update_from_arg(cfg, argdict, key):
    "Helper function for get_cfg."
    for var in cfg[key]:
        if var in argdict and argdict[var] is not None:
            cfg[key][var] = argdict[var]


def get_cfg(names, defaults=None):
    """Obtain settings from the configuration file. Sometimes we may
    wish to only obtain certain sections from the configuration. When
    this is the case we can use this function and we specify a list
    of ``names`` or a single string to obtain specific sections from
    the configuration. We may optionally provide defaults in case we
    wish to override the defaults provided for each of the
    sections."""
    cfg = {
        'lexor': {
            'path': ''
        }
    }
    L.info('getting configuration for: %s' % names)
    cfg_file = read_config()
    if 'lexor' in cfg_file:
        for var, val in cfg_file['lexor'].iteritems():
            cfg['lexor'][var] = pth.expandvars(val)
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
    return cfg


def set_style_cfg(obj, name, defaults):
    """Given a |Parser|, |Converter| or |Writer| ``obj``, it sets its
    ``defaults`` attribute to the specified defaults in the
    configuration file or by the user by overwriting values in the
    parameter ``defaults``.

    .. |Parser| replace:: :class:`~lexor.core.parser.Parser`
    .. |Converter| replace:: :class:`~lexor.core.converter.Converter`
    .. |Writer| replace:: :class:`~lexor.core.writer.Writer`

    """
    L.info('configuring %r', obj.__class__)
    obj.defaults = dict()
    if hasattr(obj.style_module, 'DEFAULTS'):
        L.info('setting module defaults for %r', name)
        mod_defaults = obj.style_module.DEFAULTS
        for var, val in mod_defaults.iteritems():
            obj.defaults[var] = pth.expandvars(str(val))
    cfg_file = read_config()
    if name in cfg_file:
        L.info('setting defaults from configuration for %r', name)
        for var, val in cfg_file[name].iteritems():
            obj.defaults[var] = pth.expandvars(val)
    if defaults:
        L.info('overwriting default values from user for %r', name)
        for var, val in defaults.iteritems():
            obj.defaults[var] = val
