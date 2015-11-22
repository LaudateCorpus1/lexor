"""
Routine to create an xml file with the documentation of a lexor
style.

"""
import re
import sys
import textwrap
import inspect
import os.path as pth
import json
from imp import load_source
from lexor.command import config, LexorError, disp
from lexor.util.logging import L


DEFAULTS = {
    'path': '.',
}
DESC = """
Generate a json file with the documentation data of a lexor language
style.

Note: this command uses the inputfile argument to obtain the python
module to document. Make sure to not skip it.

"""


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('document', help='document a style',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('--path', type=str,
                      help='search for styles in this directory')
    tmpp.add_argument('--output-dir', type=str, default='',
                      metavar="DIR",
                      help='writes file in the specified dir if set')


def run():
    """Run the command. """
    arg = config.CONFIG['arg']
    dirpath, fname = check_filename(arg)
    L.info('style to document: %r', pth.join(dirpath, fname))

    mod = load_source('tmp-module', fname)
    doc_modules = {}
    if not hasattr(mod, 'INFO') or 'lang' not in mod.INFO:
        filename = fname[:-3] + '.json'
        append_module(doc_modules, mod, "main")
    else:
        info = mod.INFO
        if info['to_lang']:
            filename = '%s/lexor.%s.%s.%s.%s-%s.json'
            filename %= (dirpath, info['lang'], info['type'],
                         info['to_lang'], info['style'], info['ver'])
        else:
            filename = '%s/lexor.%s.%s.%s-%s.json'
            filename %= (dirpath, info['lang'], info['type'],
                         info['style'], info['ver'])
        modules = append_main_module(doc_modules, mod)
        for mod_name in modules:
            append_module(doc_modules, modules[mod_name])

    disp('Writing %s ... ' % filename)
    if arg.output_dir == '':
        filename = None
    if filename is None:
        json.dump(doc_modules, sys.stdout,
                  indent=2, separators=(',', ': '))
    else:
        with open(filename, 'w') as stream:
            json.dump(doc_modules, stream)
    disp('done\n')


def export_object(obj):
    """Process objects before they are exported into an xml document.
    Objects such as modules are exported as links in the restructured
    text format."""
    result = obj
    if isinstance(obj, str):
        pass
    elif inspect.ismodule(obj):
        result = ':ref:`%s`' % obj.__name__
    elif inspect.isclass(obj):
        result = ':ref:`%s`' % obj.__name__
    elif isinstance(obj, list):
        result = [export_object(x) for x in obj]
    elif isinstance(obj, dict):
        result = {k: export_object(obj[k]) for k in obj}
    else:
        try:
            json.dumps(obj)
        except TypeError:
            result = repr(obj)
    return result


def get_module_info(info):
    """Copy the info dictionary with the exception of those
    entries which are None or the `path` entry.
    """
    obj = {}
    for key in info:
        if info[key] is None or key == 'path':
            continue
        obj[key] = info[key]
    return obj


def get_module_defaults(defaults):
    """copy the defaults object"""
    obj = {}
    for key in defaults:
        obj[key] = defaults[key]
    return obj


def _append_module(modules, name):
    """Append a module only it is missing"""
    if name not in modules:
        modules[name] = sys.modules[name]


def get_module_mapping(mapping, repository=None):
    """Examine the mapping object and return an object with its
    information.
    """
    if repository is None:
        repository = list()
    modules = dict()
    obj = dict()
    keys = sorted(mapping.keys())
    for key in keys:
        info = obj[key] = dict()
        if isinstance(mapping[key], tuple):
            info['checker'] = mapping[key][0]
            info['processors'] = []
            for mod in mapping[key][1]:
                if isinstance(mod, str):
                    for val in repository:
                        if val.__name__ == mod:
                            mod = val
                            break
                mod_name = mod.__module__
                info['processors'].append({
                    'module': mod_name,
                    'name': mod.__name__
                })
                _append_module(modules, mod_name)
        else:
            mod = mapping[key]
            if isinstance(mod, str):
                for val in repository:
                    if val.__name__ == mod:
                        mod = val
                        break
            if isinstance(mod, str):
                info['fromEntry'] = mod
                continue
            mod_name = mod.__module__
            info['module'] = mod_name
            info['name'] = mod.__name__
            _append_module(modules, mod_name)
    return obj, modules


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


def get_function_obj(func):
    """Return the function information"""
    obj = {
        'name': func.__name__,
        'argspec': {}
    }
    argspec = inspect.getargspec(func)
    if argspec[1]:
        obj['argspec']['varargs'] = argspec[1]
    if argspec[2]:
        obj['argspec']['keywords'] = argspec[2]
    args = obj['argspec']['arg'] = []
    for item in argspec[0]:
        args.append({
            'name': item
        })
    if argspec[3] is not None:
        largs = len(argspec[0])
        ldefs = len(argspec[3])
        num = 0
        for index in xrange(largs-ldefs, largs):
            args[index]['default'] = argspec[3][num]
            num += 1
    doc = inspect.getdoc(func)
    if doc is not None:
        obj['doc'] = doc
    return obj


def get_property_obj(prop):
    """Return a property object"""
    print repr(prop)
    obj = {
        'name': prop[0]
    }
    doc = inspect.getdoc(prop[1])
    if doc is not None:
        obj['doc'] = doc
    return obj


def get_member_obj(member):
    """Return a member object"""
    return {
        'name': member.__name__
    }


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


def _update_obj(obj, tree, mro):
    """Helper function for get_class_obj. Updates the obj. """
    obj['cls_method_block'] = []
    obj['method_block'] = []
    obj['property_block'] = []
    obj['member_block'] = []
    for index in xrange(len(mro)):
        tmp = {
            'from': full_class_name(mro[index])
        }
        for func in tree[mro[index]]['cls_method']:
            tmp['function'] = get_function_obj(func)
        if len(tree[mro[index]]['cls_method']) > 0:
            obj['cls_method_block'].append(tmp)

        tmp = {
            'from': full_class_name(mro[index])
        }
        for func in tree[mro[index]]['method']:
            tmp['function'] = get_function_obj(func)
        if len(tree[mro[index]]['method']) > 0:
            obj['method_block'].append(tmp)

        tmp = {
            'from': full_class_name(mro[index])
        }
        for prop in tree[mro[index]]['property']:
            tmp['property'] = get_property_obj(prop)
        if len(tree[mro[index]]['property']) > 0:
            obj['property_block'].append(tmp)

        tmp = {
            'from': full_class_name(mro[index])
        }
        for member in tree[mro[index]]['member']:
            tmp['member'] = get_member_obj(member)
        if len(tree[mro[index]]['member']) > 0:
            obj['member_block'].append(tmp)


def get_class_obj(cls):
    """Return the class info. Assumes that cls is a valid class. """
    obj = dict()
    obj['name'] = cls.__name__

    obj['bases'] = []
    for base in cls.__bases__:
        obj['bases'].append({
            'base': full_class_name(base)
        })

    mro = inspect.getmro(cls)
    obj['mro'] = []
    for base in mro:
        obj['mro'].append({
            'class': full_class_name(base)
        })

    doc = inspect.getdoc(cls)
    if doc is not None:
        obj['doc'] = doc

    tree = dict()
    for mod in mro:
        tree[mod] = {
            'cls_method': [],
            'method': [],
            'property': [],
            'member': [],
        }
    _update_class_tree(tree, cls, mro)
    _update_obj(obj, tree, mro)
    return obj


def _append_info(main, info):
    """Helper function for `append_main_module` and `append_module`"""
    main['classes'] = []
    for cls in info['class']:
        main['classes'].append(get_class_obj(cls))
    main['functions'] = []
    for func in info['function']:
        main['functions'].append(get_function_obj(func))
    main['dataBlock'] = []
    for item in info['data']:
        if item[0][0] == '_':
            continue
        if isinstance(item[1], type(re.compile(''))):
            val = item[1].pattern
        else:
            val = export_object(item[1])
        main['dataBlock'].append({
            item[0]: val
        })
    main['imports'] = []
    for item in info['module']:
        main['imports'].append({
            'name': item[0],
            'fullname': item[1].__name__,
            'type': item[1].__class__.__name__
        })
    for item in info['other']:
        main['imports'].append({
            'name': item[0],
            'fullname': full_class_name(item[1]),
            'type': item[1].__class__.__name__
        })


def append_main_module(doc_module, mod):
    """Append the main module to `doc_module`"""
    main = doc_module['main'] = {}
    main['doc'] = str(mod.__doc__)
    main['info'] = get_module_info(mod.INFO)
    if hasattr(mod, 'DEFAULTS'):
        main['defaults'] = get_module_defaults(mod.DEFAULTS)
    if hasattr(mod, 'REPOSITORY'):
        repository = mod.REPOSITORY
    else:
        repository = None
    if hasattr(mod, 'MAPPING'):
        main['mapping'], modules = get_module_mapping(
            mod.MAPPING, repository
        )
    else:
        modules = None
    info = separate_objects(mod, [
        'INFO', 'DEFAULTS', 'MAPPING', 'DESCRIPTION'
    ])
    _append_info(main, info)
    return modules


def append_module(doc_module, mod, name=None):
    """Create a module node documenation. """
    if name is None:
        name = mod.__name__
    main = doc_module[name] = {}
    main['doc'] = str(mod.__doc__)
    info = separate_objects(mod)
    _append_info(main, info)


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
        raise LexorError("%r not found" % (pth.join(dirpath, fname)))
    return dirpath, fname
