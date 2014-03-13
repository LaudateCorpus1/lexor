"""Edit

Module to open files with an editor.

"""

import textwrap
from os import listdir, system
from os.path import isfile, join, exists
from lexor.command import error
from lexor.command import config

DEFAULTS = {
    'editor': '$EDITOR',
    'path': '.'
}

DESC = """
Open a file if it is found in the path provided by the configuration
file.

"""


def valid_files(parsed_args, **_):
    """Return a list of valid files to edit."""
    config.CONFIG['arg'] = parsed_args
    cfg = config.get_cfg('edit', DEFAULTS)
    root = cfg['lexor']['root']
    paths = cfg['edit']['path'].split(':')
    choices = []
    for path in paths:
        if path[0] in ['/', '.']:
            abspath = path
        else:
            abspath = '%s/%s' % (root, path)
        try:
            choices.extend([fname for fname in listdir(abspath)
                            if isfile(join(abspath, fname))])
        except OSError:
            pass
    return choices


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('edit', help='edit a file',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('--path', type=str,
                      help='search path')
    tmpp.add_argument('--editor', type=str,
                      help='editor to open files')


def run():
    """Run the edit command. """
    arg = config.CONFIG['arg']
    cfg = config.get_cfg('edit', DEFAULTS)
    root = cfg['lexor']['root']
    paths = cfg['edit']['path'].split(':')

    fname = arg.inputfile
    found = False
    for path in paths:
        if path[0] in ['/', '.']:
            abspath = '%s/%s' % (path, fname)
        else:
            abspath = '%s/%s/%s' % (root, path, fname)
        if exists(abspath):
            found = True
            break
    if not found:
        error("ERROR: file not found.\n")
    cmd = '%s "%s" > /dev/null' % (cfg['edit']['editor'], abspath)    
    system(cmd)
