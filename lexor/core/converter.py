"""Converter Module

Provides the `Converter` object which defines the basic mechanism for
converting the objects defined in `lexor.core.elements`. This involves
using objects derived from the abstract class `NodeConverter`. See
`lexor.core.dev` for more information on how to write objects derived
from `NodeConverter` to be able to convert `Documents` in the way you
desire.

"""

import sys
import os.path as pth
from imp import load_source
from cStringIO import StringIO
from lexor.command.lang import get_style_module
from lexor.core.parser import _map_explanations, Parser
import lexor.core.elements as core
import lexor.command.config as config
import traceback


def get_converter_namespace():
    """Many converters may be defined during the convertion of a
    document. In some cases we may need to save references to objects
    in documents. If this is the case, then call this function to
    obtain the namespace where you can save those references. """
    return get_converter_namespace.namespace
if not hasattr(get_converter_namespace, 'namespace'):
    get_converter_namespace.namespace = dict()


class NodeConverter(object):
    """A node converter is an object which determines if the node
    will be copied (default). To avoid copying the node simply
    declare

        copy = False

    when deriving a node converter. Note that by default, the
    children of the node (if any) will be copied and assigned to the
    parent. To avoid copying the children then set

        copy_children = False

    """
    copy = True
    copy_children = True

    def __init__(self, converter):
        """A `NodeConverter` needs to be initialized with a converter
        object. If this method is to be overloaded then make sure
        that it only accepts one parameter: `converter`. This method
        is used by `Converter` and it calls it with itself as the
        parameter. """
        self.converter = converter

    def start(self, node):
        """This method gets called only if `copy` is set to True
        (default). By overloading this method you have access to the
        converter and the node. You can thus set extra variables in
        the converter or modify the node. DO NOT modify any of the
        parents of the node. If there is a need to modify any of
        parents of the node then set a variable in the converter
        to point to the node so that later on in the `convert` function
        it can be modified. """
        return node

    def end(self, node):
        """This method gets called after all the children have
        been copied. Make sure to return the node or the node
        replacement. """
        return node

    def msg(self, code, node, arg=None, uri=None):
        """Send a message to the converter. """
        self.converter.msg(self.__module__, code, node, arg, uri)


# The default of 7 attributes for class is too restrictive.
# pylint: disable=R0902
class Converter(object):
    """To see the languages available to the `Converter` see the
    `lexor.lang` module. """

    def __init__(self, fromlang='xml', tolang='xml',
                 style='default', defaults=None):
        """Create a new `Converter` by specifying the language and the
        style in which `Node` objects will be written. """
        if defaults is None:
            defaults = dict()
        self._fromlang = fromlang
        self._tolang = tolang
        self._style = style
        self._nc = None
        self._node_converter = None
        self._convert_func = None
        self._reload = True
        self.style_module = None
        self.doc = list()
        self.log = list()
        self.defaults = defaults

    @property
    def convert_from(self):
        """The language from which the converter will convert. """
        return self._fromlang

    @convert_from.setter
    def convert_from(self, value):
        """Setter function for convert_from. """
        self._fromlang = value
        self._reload = True

    @property
    def convert_to(self):
        """The language to which the converter will convert. """
        return self._tolang

    @convert_to.setter
    def convert_to(self, value):
        """Setter function for convert_to. """
        self._tolang = value
        self._reload = True

    @property
    def converting_style(self):
        """The converter style. """
        return self._style

    @converting_style.setter
    def converting_style(self, value):
        """Setter function for converting_style. """
        self._style = value
        self._reload = True

    def set(self, fromlang, tolang, style, defaults=None):
        """Sets the languages and styles in one call. """
        if defaults is not None:
            self.defaults = defaults
        self._style = style
        self._tolang = tolang
        self._fromlang = fromlang
        self._reload = True

    @property
    def lexor_log(self):
        """The `lexorlog` document. See this document after each
        call to `convert` to see warnings and errors. """
        return self.log[-1]

    @property
    def document(self):
        """The parsed document. This is a `Document` or
        `FragmentedDocument` created by the `convert` method. """
        return self.doc[-1]

    def convert(self, doc, namespace=False):
        """Convert the `Document` doc. """
        if not isinstance(doc, (core.Document, core.DocumentFragment)):
            raise TypeError("The node is not a Document or DocumentFragment")
        if self._reload:
            self._set_node_converters(
                self._fromlang, self._tolang, self._style, self.defaults
            )
            self._reload = False
        self.log.append(core.Document("lexor", "log"))
        self.log[-1].modules = dict()
        self.log[-1].explanation = dict()
        self._convert(doc)
        if hasattr(self.style_module, 'convert'):
            self.style_module.convert(self, self.doc[-1])
        _map_explanations(self.log[-1].modules, self.log[-1].explanation)
        if not namespace:
            del self.doc[-1].namespace
        return self.doc[-1], self.log[-1]

    # pylint: disable=R0913
    def msg(self, mod_name, code, node, arg=None, uri=None):
        """Provide the name of module issuing the message, the code
        number, the node with the error, optional arguments and uri.
        This information gets stored in the log. """
        if uri is None:
            uri = self.doc[-1].uri_
        if arg is None:
            arg = ()
        node = core.Void('msg')
        node['module'] = mod_name
        node['code'] = code
        node['node_id'] = id(node)
        node.node = node
        node['uri'] = uri
        node['arg'] = arg
        if mod_name not in self.log[-1].modules:
            self.log[-1].modules[mod_name] = sys.modules[mod_name]
        self.log[-1].append_child(node)

    def _set_node_converter(self, val):
        """Helper function to create a node converter and store it in
        a dictionary. """
        if isinstance(val, str):
            return self._node_converter[val]
        name = val.__name__
        self._node_converter[name] = val(self)
        return self._node_converter[name]

    def __getitem__(self, name):
        """Return a Node converter. """
        return self._node_converter[name]

    def _set_node_converters(self, fromlang, tolang, style, defaults=None):
        """Imports the correct module based on the languages and
        style. """
        self.style_module = get_style_module(
            'converter', fromlang, style, tolang
        )
        name = '%s-converter-%s-%s' % (fromlang, tolang, style)
        config.set_style_cfg(self, name, defaults)
        self._nc = dict()
        self._node_converter = dict()
        if hasattr(self.style_module, 'REPOSITORY'):
            for val in self.style_module.REPOSITORY:
                self._set_node_converter(val)
        self._nc['__default__'] = self._set_node_converter(NodeConverter)
        str_key = list()
        for key, val in self.style_module.MAPPING.iteritems():
            if isinstance(val, str) and val not in self._node_converter:
                str_key.append((key, val))
            else:
                self._nc[key] = self._set_node_converter(val)
        for key, val in str_key:
            self._nc[key] = self._nc[val]

    def _start(self, node):
        """Evaluate the start function of the node converter based
        on the name of the node. """
        return self._nc.get(node.name, self._nc['__default__']).start(node)

    def _end(self, node):
        """Evaluate the end function of the node converter based
        on the name of the node. """
        return self._nc.get(node.name, self._nc['__default__']).end(node)

    def _copy(self, node):
        """Return the copy attribute of the node converter. """
        return self._nc.get(node.name, self._nc['__default__']).copy

    def _copy_children(self, node):
        """Return the copy_children attribute of the node converter. """
        return self._nc.get(node.name, self._nc['__default__']).copy_children

    def _get_direction(self, crt):
        """Returns the direction in which the traversal should go. """
        if isinstance(crt, core.CharacterData):
            return 'r'
        elif crt.child:
            if self._copy_children(crt):
                return 'd'
            return 'r'
        return 'r'

    def _convert(self, doc):
        """Main convert function. """
        direction = None
        # A doc needs to be copied by default. You may prohibit
        # to copy the children, but there must be a document.
        crt = doc
        self.doc.append(core.Document(doc.lang, doc.style))
        self.doc[-1].uri_ = doc.uri_
        self.doc[-1].namespace = dict()
        if hasattr(self.style_module, 'init_conversion'):
            self.style_module.init_conversion(self, self.doc[-1])
        crtcopy = self.doc[-1]
        crtcopy = self._start(crtcopy)
        if self._copy_children(crt):
            direction = 'd'
            root = doc
        else:
            return
        while True:
            if direction is 'd':
                crt = crt.child[0]
                clone = crt.clone_node()
                crtcopy.append_child(clone)
            elif direction is 'r':
                if crt.next is None:
                    direction = 'u'
                    continue
                crt = crt.next
                clone = crt.clone_node()
                crtcopy.parent.append_child(clone)
            elif direction is 'u':
                crtcopy = self._end(crtcopy.parent)
                if crt.parent is root:
                    break
                if crt.parent.next is None:
                    crt = crt.parent
                    continue
                crt = crt.parent.next
                clone = crt.clone_node()
                crtcopy.parent.append_child(clone)
            crtcopy = clone
            crtcopy = self._start(crtcopy)
            direction = self._get_direction(crt)

    def update_log(self, log):
        """Append the messages from a log document to the converters
        log. Note that this removes the children from log. """
        modules = log.modules
        for mname in modules:
            if mname not in self.log[-1].modules:
                self.log[-1].modules[mname] = modules[mname]
        self.log[-1].extend_children(log)

    # pylint: disable=W0122,E1103
    def exec_python(self, node, id_num, parser, error=True):
        """Executes the contents of the processing instruction. You
        must provide an id number identifying the processing
        instruction, the namespace where the execution takes place
        and a parser that will parse the output provided by the
        execution. If `error` is True then any errors generated
        during the execution will be appended to the output of the
        document."""
        get_current_node.current.append(node)
        include.converter.append(self)
        namespace = get_lexor_namespace()
        if '__NAMESPACE__' not in namespace:
            namespace['__NAMESPACE__'] = namespace
            namespace['import_module'] = import_module
            namespace['include'] = include
            namespace['echo'] = echo
        namespace['__FILE__'] = pth.realpath(include.converter[-1].doc.uri)
        namespace['__DIR__'] = pth.dirname(namespace['__FILE__'])
        namespace['__NODE__'] = get_current_node()
        original_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            exec(node.data, namespace)
        except BaseException:
            self.msg(self.__module__, 'E100', node, [id_num])
            if error:
                err_node = core.Element('python_pi_error')
                err_node['section'] = str(id_num)
                err_node.append_child(
                    core.CData(traceback.format_exc())
                )
                node.parent.insert_before(node.index, err_node)
        text = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = original_stdout
        parser.parse(text)
        node.parent.extend_before(node.index, parser.doc)
        del node.parent[node.index]
        if parser.log:
            self.msg(self.__module__, 'W101', node, [id_num])
            self.update_log(parser.log)
            self.msg(self.__module__, 'W102', node, [id_num])
        get_current_node.current.pop()
        include.converter.pop()
        if include.converter:
            namespace['__FILE__'] = pth.realpath(include.converter[-1].doc.uri)
            namespace['__DIR__'] = pth.dirname(namespace['__FILE__'])
            namespace['__NODE__'] = get_current_node()
        else:
            namespace['__FILE__'] = None
            namespace['__DIR__'] = None
            namespace['__NODE__'] = None


def get_lexor_namespace():
    """The execution of python instructions take place in the
    namespace provided by this function."""
    return get_lexor_namespace.namespace
if not hasattr(get_lexor_namespace, 'namespace'):
    get_lexor_namespace.namespace = dict()


def get_current_node():
    """Return the `Document` node containing the python embeddings
    currently being executed. """
    return get_current_node.current[-1]
if not hasattr(get_current_node, 'current'):
    get_current_node.current = list()


def echo(node):
    """Allows the insertion of Nodes generated within python
    embeddings.

        <?python
        comment = PI('!--', 'This is a comment')
        echo(comment)
        ?>

    """
    crt = get_current_node()
    if isinstance(node, str):
        crt.parent.insert_before(crt.index, core.Text(node))
    elif isinstance(node, core.Node):
        crt.parent.insert_before(crt.index, node)
    elif isinstance(node, list):
        for item in node:
            echo(item)
    else:
        while node:
            echo(node[0])


def include(input_file, **keywords):
    """Inserts a file into the current node. """
    parent_converter = include.converter[-1]
    if input_file[0] != '/':
        input_file = pth.join(pth.dirname(parent_converter.doc.uri),
                              input_file)
    info = {
        'parser_style': 'default',
        'parser_lang': None,
        'parser_defaults': None,
        'convert_style': 'default',
        'convert_from': None,
        'convert_to': None,
        'convert_defaults': None,
        'adopt': True,
    }
    for key in keywords:
        info[key] = keywords[key]
    if info['parser_lang'] is None:
        path = pth.realpath(input_file)
        name = pth.basename(path)
        name = pth.splitext(name)
        info['parser_lang'] = name[1][1:]
    with open(input_file, 'r') as tmpf:
        text = tmpf.read()
    parser = Parser(info['parser_lang'],
                    info['parser_style'],
                    info['parser_defaults'])
    parser.parse(text, input_file)
    if parser.log:
        parent_converter.update_log(parser.log)
    crt = get_current_node()
    if info['convert_to'] is not None:
        if info['convert_from'] is None:
            info['convert_from'] = info['parser_lang']
        converter = Converter(info['convert_from'],
                              info['convert_to'],
                              info['convert_style'],
                              info['convert_defaults'])
        converter.convert(parser.doc)
        if converter.log:
            parent_converter.update_log(converter.log)
        doc = converter.document
    else:
        doc = parser.doc
    if info['adopt']:
        crt.parent.extend_before(crt.index, doc)
    else:
        crt.parent.insert_before(crt.index, doc)
if not hasattr(include, 'converter'):
    include.converter = list()


def import_module(mod_path, mod_name=None):
    """Return a module from a path. If no name is provided then the
    name of the file loaded will be assigned to the name. When using
    relative paths, it will find the module relative to the file
    executing the python embedding. """
    converter = include.converter[-1]
    if not mod_path.endswith('.py'):
        mod_path += '.py'
    if mod_path[0] != '/':
        mod_path = pth.join(pth.dirname(converter.doc.uri), mod_path)
    if mod_name is None:
        mod_name = pth.basename(mod_path)
    if mod_name.endswith('.py'):
        mod_name = mod_name[:-3]
    return load_source(mod_name, mod_path)


MSG = {
    'E100': 'errors in python processing instruction section `{0}`',
    'W101': '--> begin ?python section `{0}` messages',
    'W102': '--> end ?python section `{0}` messages',
}
MSG_EXPLANATION = [
    """
    - This message is being shown because of E100.

    - The python processing instructions has mistakes. See the
      traceback generated to fix the errors.

    - If the traceback is not shown in the document it may be
      due to the option `error` being off.

""",
    """
    - Python embeddings may generate output to be adapted to the
      document. Such output also needs to be processed. When the
      ouput generates errors these errors get apended to the
      converter log document.

    - All messages between W101 and W102 are are simply errors of the
      parsed output.

""",
]
