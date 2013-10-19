"""Config

Read and write the configuration file using the configparser module.

"""

import os
from lexor.dev import error
import configparser

__all__ = ['run', 'read_config', 'write_config']


def read_config():
    """Read the configuration file ~/.lexorconfig"""
    config = configparser.ConfigParser(allow_no_value=True)
    try:
        config.read(os.path.expanduser('~/.lexorconfig'))
    except IOError:
        return None
    return config


def write_config(config):
    """Write the configuration file ~/.lexorconfig"""
    with open(os.path.expanduser('~/.lexorconfig'), 'w') as cfile:
        config.write(cfile)


def run(argp):
    """Configure lexor by editing ~/.lexorconfig"""
    config = read_config()
    try:
        sec, key = argp.key.split('.', 1)
    except ValueError:
        error("error: key does not contain a section: %s\n" % argp.key)
    if argp.value is None:
        try:
            print config[sec][key]
            return
        except KeyError:
            return
    try:
        config[sec][key] = argp.value
    except KeyError:
        config.add_section(sec)
        config[sec][key] = argp.value
    write_config(config)
