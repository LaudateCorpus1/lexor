"""Document

Routine to create an xml file with the documentation of a lexor
style.

"""
#pylint: disable=W0142

import os
import textwrap
import lexor
from imp import load_source
from lexor.command import error, warn
import lexor.command.config as config
import lexor.core.elements as core

DEFAULTS = {
    'path': '.',
}
DESC = """
Generate an xml file with the documentation of a lexor style.

"""


def style_completer(**_):
    """Return the meta var. """
    return ['STYLE']


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('document', help='document a style',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('style', type=str,
                      help='name of style to document'
                      ).completer = style_completer
    tmpp.add_argument('--path', type=str,
                      help='documentation directory')


def append_info(doc, mod):
    """Append the module info. """
    info = mod.INFO
    del info['path']
    node_info = core.Element('INFO')
    for key in info:
        if info[key] is not None:
            node = core.Element(key)
            if key == 'description':
                node.append_child(core.CData(str(info[key])))
            else:
                node.append_child(core.Text(str(info[key])))
            node_info.append_child(node)
    doc.append_child(node_info)


#def process_tuple(mapping, key, info):
#    """Iterate through the dictionary and append its information. """
#    pass


def process_module(mapping, key, info):
    """Iterate through the list and append its information. """
    node = core.Element('ENTRY')
    node['key'] = key
    node.append_child(core.CData(str(info.__doc__)))
    mapping.append_child(node)


def append_doc_strings(doc, mod):
    """Append the module info. """
    style_doc = core.Element('STYLE_DOC')
    style_doc.append_child(core.CData(str(mod.__doc__)))
    doc.append_child(style_doc)
    #mod_node = core.Element('MOD')
    info = mod.MAPPING
    mapping = core.Element('MAPPING')
    for key in info:
        if isinstance(info[key], tuple):
            pass
            #process_tuple(mapping, key, info[key])
        else:
            process_module(mapping, key, info[key])
    doc.append_child(mapping)


def run():
    """Run the command. """
    arg = config.CONFIG['arg']
    cfg = config.get_cfg('document', DEFAULTS)
    root = cfg['lexor']['root']
    path = cfg['document']['path']

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
    base, _ = os.path.split(moddir)
    if base == '':
        base = '.'

    mod = load_source('tmp_name', style)
    info = mod.INFO
    if info['to_lang']:
        filename = '%s/lexor.%s.%s.%s.%s-%s.xml'
        filename = filename % (dirpath, info['lang'], info['type'],
                               info['to_lang'], info['style'], info['ver'])
    else:
        filename = '%s/lexor.%s.%s.%s-%s.xml'
        filename = filename % (dirpath, info['lang'], info['type'],
                               info['style'], info['ver'])

    warn('Writing %s ... ' % filename)
    doc = core.Document()
    append_info(doc, mod)
    append_doc_strings(doc, mod)
    try:
        lexor.write(doc, filename)
    except IOError:
        error("\nERROR: unable to write file.\n"
              "xml writer default style missing?\n")
    else:
        warn('done\n')
