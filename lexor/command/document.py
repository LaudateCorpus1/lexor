"""
Routine to create an xml file with the documentation of a lexor
style.

"""
# pylint: disable=star-args
import re
import os
import sys
import textwrap
import inspect
import lexor
import os.path as pth
from imp import load_source
from lexor.core import elements as core
from lexor.command import config
from lexor.command.to import style_parameters


def xml_style(lang_str):
    """Parses a style string. """
    input_style = style_parameters(lang_str)
    if input_style['name'] == '':
        input_style['name'] = '_'
    return input_style


DEFAULTS = {
    'path': '.',
}
DESC = """
Generate an xml file with the documentation of a lexor language style.

"""


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('document', help='document a style',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('style', type=xml_style, nargs='?',
                      help='the xml style to write the documentation')
    tmpp.add_argument('--path', type=str,
                      help='search for styles in this directory')
    tmpp.add_argument('--output-dir', type=str, default='', metavar="DIR",
                      help='writes to file in the specified dir if set')


def run():
    """Run the command. """
    arg = config.CONFIG['arg']
    dirpath, fname = check_filename(arg)

    moddir = os.path.splitext(fname)[0]
    base, _ = os.path.split(moddir)
    if base == '':
        base = '.'

    mod = load_source('tmp-module', fname)
    doc = core.Document()
    if not hasattr(mod, 'INFO') or 'lang' not in mod.INFO:
        filename = fname[:-3] + '.xml'
        doc.append_child(make_module_node(mod, "main"))
    else:
        info = mod.INFO
        if info['to_lang']:
            filename = '%s/lexor.%s.%s.%s.%s-%s.xml'
            filename = filename % (dirpath, info['lang'],
                                   info['type'], info['to_lang'],
                                   info['style'], info['ver'])
        else:
            filename = '%s/lexor.%s.%s.%s-%s.xml'
            filename = filename % (dirpath, info['lang'],
                                   info['type'], info['style'],
                                   info['ver'])
        modules = append_main(doc, mod)
        #for mod_name in modules:
        #    doc.append_child(make_module_node(modules[mod_name]))

    warn('Writing %s ... ' % filename)
    if arg.output_dir == '':
        filename = None
    try:
        if arg.style:
            doc.style = arg.style['name']
            doc.defaults = arg.style['params']
        lexor.write(doc, filename)
    except IOError:
        error("\nERROR: unable to write file.\n"
              "xml writer default style missing?\n")
    else:
        warn('done\n')


def export_object(obj):
    """Process objects before they are exported into an xml document.
    Objects such as modules are exported as links in the restructured
    text format."""
    if isinstance(obj, str):
        return obj
    if inspect.ismodule(obj):
        return ':ref:`%s`' % obj.__name__
    if isinstance(obj, list):
        return [export_object(x) for x in obj]
    if isinstance(obj, dict):
        return {k: export_object(obj[k]) for k in obj}
    return obj


def get_info_node(info):
    """Generate the info node. """
    node_info = core.Element('info')
    for key in info:
        if info[key] is None or key == 'path':
            continue
        node = core.Element('info-entry')
        node['key'] = key
        if key == 'description':
            node.append_child(core.CData(str(info[key])))
        else:
            node.append_child(core.Text(str(info[key])))
        node_info.append_child(node)
    return node_info


def get_defaults_node(obj):
    """Obtain defaults node. """
    defaults_node = core.Element('defaults')
    for ele in obj:
        node = core.Element('entry')
        node['key'] = ele
        node.append_child(core.CData(repr(obj[ele])))
        defaults_node.append_child(node)
    return defaults_node


def get_mapping_node(mapping, repository=None):
    """Generate the mapping node. """
    if repository is None:
        repository = list()
    modules = dict()
    mapping_node = core.Element('mapping')
    keys = sorted(mapping.keys())
    for ele in keys:
        if isinstance(mapping[ele], tuple):
            entry = core.Element('mapping-entry')
            entry['key'] = ele
            entry.append_child(
                core.Element('checker').append_child(
                    core.CData(repr(mapping[ele][0]))
                )
            )
            for mod in mapping[ele][1]:
                node = core.Element('processor')
                if isinstance(mod, str):
                    for val in repository:
                        if val.__name__ == mod:
                            mod = val
                            break
                mod_name = mod.__module__
                node['module'] = mod_name
                node['name'] = mod.__name__
                mapping_node.append_child(node)
                if mod_name not in modules:
                    modules[mod_name] = sys.modules[mod_name]
                entry.append_child(node)
            mapping_node.append_child(entry)
        else:
            node = core.Element('entry')
            node['key'] = ele
            mod = mapping[ele]
            if isinstance(mod, str):
                for val in repository:
                    if val.__name__ == mod:
                        mod = val
                        break
            if isinstance(mod, str):
                node['from-entry'] = mod
                mapping_node.append_child(node)
                continue
            mod_name = mod.__module__
            node['module'] = mod_name
            node['name'] = mod.__name__
            if mod_name not in modules:
                modules[mod_name] = sys.modules[mod_name]
            mapping_node.append_child(node)
    return modules, mapping_node


def separate_objects(mod, remove=None):
    """Given a module, it separates the objects into a dictionary. """
    info = {
        'class': [],
        'function': [],
        'module': [],
        'data': [],
        'other': [],
    }
    mod_dict = dict(mod.__dict__)
    if remove is None:
        remove = list()
    for ele in mod_dict:
        if ele in remove or ele[0] == '_':
            continue
        if inspect.isfunction(mod_dict[ele]):
            if mod_dict[ele].__module__ == mod.__name__:
                info['function'].append(mod_dict[ele])
            else:
                info['other'].append([ele, mod_dict[ele]])
        elif inspect.isclass(mod_dict[ele]):
            if mod_dict[ele].__module__ == mod.__name__:
                info['class'].append(mod_dict[ele])
            else:
                info['other'].append([ele, mod_dict[ele]])
        elif inspect.ismodule(mod_dict[ele]):
            info['module'].append([ele, mod_dict[ele]])
        elif inspect.isbuiltin(mod_dict[ele]):
            info['other'].append([ele, mod_dict[ele]])
        else:
            info['data'].append([ele, mod_dict[ele]])
    return info


def get_function_node(func):
    """Return a function node. """
    node = core.Element('function')
    node['name'] = func.__name__
    argspec = inspect.getargspec(func)
    node_argspec = core.Element('argspec')
    node_argspec['varargs'] = str(argspec[1])
    node_argspec['keywords'] = str(argspec[2])
    node_args = core.Element('args')
    for item in argspec[0]:
        node_args.append_child(core.Void('arg', {'name': item}))
    if argspec[3] is not None:
        largs = len(argspec[0])
        ldefs = len(argspec[3])
        num = 0
        for index in xrange(largs-ldefs, largs):
            node_args[index]['default'] = argspec[3][num]
            num += 1
    node_argspec.append_child(node_args)
    node.append_child(node_argspec)
    doc = inspect.getdoc(func)
    if doc is not None:
        node.append_child(
            core.Element('doc').append_child(
                core.CData(doc)
            )
        )
    # return core.Text(func.__name__)
    return node


def get_property_node(prop):
    """Return a property node. """
    node = core.Element('property')
    node['name'] = prop[0]
    doc = inspect.getdoc(prop[1])
    if doc is not None:
        node.append_child(
            core.Element('doc').append_child(
                core.CData(doc)
            )
        )
    return node


def get_member_node(member):
    """Return a property node. """
    node = core.Element('member')
    node['name'] = member.__name__
    return node


def full_class_name(cls):
    """Obtain the full class name. """
    if 'tmp' in cls.__module__:
        return cls.__name__
    return cls.__module__ + "." + cls.__name__


def _update_class_tree(tree, cls, mro):
    """Helper function for get_class_node. It updates the tree. """
    for name, val in inspect.getmembers(cls):
        for mod in mro:
            if name in mod.__dict__:
                if inspect.ismethod(val):
                    if val.im_self is None:
                        tree[mod]['method'].append(val)
                    else:
                        tree[mod]['cls_method'].append(val)
                elif inspect.isdatadescriptor(val):
                    if val.__class__.__name__ == 'property':
                        tree[mod]['property'].append([name, val])
                    else:
                        tree[mod]['member'].append(val)


def _update_node(node, tree, mro):
    """Helper function for get_class_node. Updates the node. """
    for index in xrange(len(mro)):
        tmp = core.Element('cls_method_block')
        tmp['from'] = full_class_name(mro[index])
        for func in tree[mro[index]]['cls_method']:
            tmp.append_child(get_function_node(func))
        if len(tmp) > 0:
            node.append_child(tmp)

        tmp = core.Element('method_block')
        tmp['from'] = full_class_name(mro[index])
        for func in tree[mro[index]]['method']:
            tmp.append_child(get_function_node(func))
        if len(tmp) > 0:
            node.append_child(tmp)

        tmp = core.Element('property_block')
        tmp['from'] = full_class_name(mro[index])
        for prop in tree[mro[index]]['property']:
            tmp.append_child(get_property_node(prop))
        if len(tmp) > 0:
            node.append_child(tmp)

        tmp = core.Element('member_block')
        tmp['from'] = full_class_name(mro[index])
        for member in tree[mro[index]]['member']:
            tmp.append_child(get_member_node(member))
        if len(tmp) > 0:
            node.append_child(tmp)


def get_class_node(cls):
    """Return a class node. Assumes that cls is a valid class. """
    node = core.Element('class')
    node['name'] = cls.__name__

    tmp = core.Element('bases')
    for base in cls.__bases__:
        tmp.append_child(
            core.Void('base', {'name': full_class_name(base)})
        )
    node.append_child(tmp)

    mro = inspect.getmro(cls)
    tmp = core.Element('mro')
    for base in mro:
        tmp.append_child(
            core.Void('class', {'name': full_class_name(base)})
        )
    node.append_child(tmp)

    doc = inspect.getdoc(cls)
    if doc is not None:
        node.append_child(
            core.Element('doc').append_child(
                core.CData(doc)
            )
        )

    tree = dict()
    for mod in mro:
        tree[mod] = {
            'cls_method': [],
            'method': [],
            'property': [],
            'member': [],
        }
    _update_class_tree(tree, cls, mro)
    _update_node(node, tree, mro)
    return node


def append_main(doc, mod):
    """Append the main module. Return a dictionary containing all the
    modules used in the style. """
    module = core.Element('module')
    module['name'] = 'main'

    module.append_child(
        core.Element('doc').append_child(
            core.CData(str(mod.__doc__))
        )
    )
    module.append_child(get_info_node(mod.INFO))
    
    if hasattr(mod, 'DEFAULTS'):
        module.append_child(get_defaults_node(mod.DEFAULTS))
    if hasattr(mod, 'REPOSITORY'):
        repository = mod.REPOSITORY
    else:
        repository = None
    modules, m_node = get_mapping_node(mod.MAPPING, repository)
    module.append_child(m_node)
    info = separate_objects(mod, ['INFO', 'DEFAULTS',
                                  'MAPPING', 'DESCRIPTION'])

    node = core.Element('classes')
    for cls in info['class']:
        node.append_child(get_class_node(cls))
    module.append_child(node)

    node = core.Element('functions')
    for func in info['function']:
        node.append_child(get_function_node(func))
    module.append_child(node)

    node = core.Element('data_block')
    for ele in info['data']:
        if ele[0][0] == '_':
            continue
        tmp = core.Element('data', {'name': ele[0]})
        if isinstance(ele[1], type(re.compile(''))):
            tmp.append_child(core.CData(repr(ele[1].pattern)))
        else:
            tmp.append_child(core.CData(repr(export_object(ele[1]))))
        node.append_child(tmp)
    if len(node) > 0:
        module.append_child(node)

    node = core.Element('imports')
    for ele in info['module']:
        node.append_child(
            core.Void('module', {'name': ele[0],
                                 'fullname': ele[1].__name__})
        )
    for ele in info['other']:
        node.append_child(
            core.Void('other', {'name': ele[0],
                                'fullname': full_class_name(ele[1]),
                                'type': ele[1].__class__.__name__})
        )
    module.append_child(node)
    doc.append_child(module)
    return modules


def make_module_node(mod, name=None):
    """Create a module node documenation. """
    module = core.Element('module')
    if name is None:
        name = mod.__name__
    module['name'] = name

    module.append_child(
        core.Element('doc').append_child(
            core.CData(str(mod.__doc__))
        )
    )

    info = separate_objects(mod)

    node = core.Element('classes')
    for cls in info['class']:
        node.append_child(get_class_node(cls))
    module.append_child(node)

    node = core.Element('functions')
    for func in info['function']:
        node.append_child(get_function_node(func))
    module.append_child(node)

    node = core.Element('data_block')
    for ele in info['data']:
        if ele[0][0] == '_':
            continue
        tmp = core.Element('data', {'name': ele[0]})
        if isinstance(ele[1], type(re.compile(''))):
            tmp.append_child(core.CData(repr(ele[1].pattern)))
        else:
            tmp.append_child(core.CData(repr(ele[1])))
        node.append_child(tmp)
    if len(node) > 0:
        module.append_child(node)

    node = core.Element('imports')
    for ele in info['module']:
        node.append_child(
            core.Void('module', {'name': ele[0],
                                 'fullname': ele[1].__name__})
        )
    for ele in info['other']:
        node.append_child(
            core.Void('other', {'name': ele[0],
                                'fullname': full_class_name(ele[1]),
                                'type': ele[1].__class__.__name__})
        )
    module.append_child(node)
    return module


def check_filename(arg):
    """Check if the inputfile exists. """
    cfg = config.get_cfg('document', DEFAULTS)
    root = cfg['lexor']['root']
    path = cfg['document']['path']

    fname = arg.inputfile
    if path[0] in ['/', '.']:
        dirpath = path
    else:
        dirpath = '%s/%s' % (root, path)

    if '.py' not in fname:
        fname = '%s.py' % fname
    if not pth.exists(pth.join(dirpath, fname)):
        error("ERROR: %r not found.\n" % (pth.join(dirpath, fname)))
    return dirpath, fname
