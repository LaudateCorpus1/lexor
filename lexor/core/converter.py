"""Converter Module

Provides the `Converter` object which defines the basic mechanism for
converting the objects defined in `lexor.core.elements`. This involves
using objects derived from the abstract class `NodeConverter`. See
`lexor.core.dev` for more information on how to write objects derived
from `NodeConverter` to be able to convert `Documents` in the way you
desire.

"""

import sys
import lexor.command.config as config
from lexor.command.lang import get_style_module
from lexor.core.elements import Document, DocumentFragment
from lexor.core.elements import CharacterData, Element, Void
from lexor.core.parser import _map_explanations


# The default of at least 2 methods is too restrictive.
# pylint: disable=R0903
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

    def process(self, node):
        """This method gets called only if `copy` is set to True
        (default). By overloading this method you have access to the
        converter and the node. You can thus set extra variables in
        the converter or modify the node. DO NOT modify any of the
        parents of the node. If there is a need to modify any of
        parents of the node then set a variable in the converter
        to point to the node so that later on in the `convert` function
        it can be modified. """
        pass

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
        self._init_converter = None
        self._nc = None
        self._convert_func = None
        self._reload = True
        self.style_module = None
        self.doc = None
        self.log = None
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
        call to `parse` to see warnings and errors in the text that
        was parsed. """
        return self.log

    @property
    def document(self):
        """The parsed document. This is a `Document` or
        `FragmentedDocument` created by the `parse` method. """
        return self.doc

    def convert(self, doc):
        """Convert the `Document` doc. """
        if not isinstance(doc, (Document, DocumentFragment)):
            raise TypeError("The node is not a Document or DocumentFragment")
        if self._reload:
            self._set_node_converters(
                self._fromlang, self._tolang, self._style
            )
            self._reload = False
        self.log = Document("lexor", "log")
        self.log.modules = dict()
        self.log.explanation = dict()
        self._init_converter(self)
        self._convert(doc)
        self._convert_func(self, self.doc)
        _map_explanations(self.log.modules, self.log.explanation)

    # pylint: disable=R0913
    def msg(self, mod_name, code, node, arg=None, uri=None):
        """Provide the name of module issuing the message, the code
        number, the node with the error, optional arguments and uri.
        This information gets stored in the log. """
        if uri is None:
            uri = self.doc.uri_
        if arg is None:
            arg = ()
        node = Void('msg')
        node['module'] = mod_name
        node['code'] = code
        node['node_id'] = id(node)
        node.node = node
        node['uri'] = uri
        node['arg'] = arg
        if mod_name not in self.log.modules:
            self.log.modules[mod_name] = sys.modules[mod_name]
        self.log.append_child(node)

    def _set_node_converters(self, fromlang, tolang, style, defaults=None):
        """Imports the correct module based on the languages and style. """
        self.style_module = get_style_module('converter', fromlang,
                                             style, tolang)
        name = '%s-converter-%s-%s' % (fromlang, tolang, style)
        config.set_style_cfg(self, name, defaults)
        self._nc = dict()
        self._nc['__default__'] = NodeConverter(self)
        for key, val in self.style_module.MAPPING.iteritems():
            self._nc[key] = val(self)
        self._convert_func = self.style_module.convert
        self._init_converter = self.style_module.init_converter

    def _process(self, node):
        """Evaluate the process function of the node converter based
        on the name of the node. """
        self._nc.get(node.name, self._nc['__default__']).process(node)

    def _copy(self, node):
        """Return the copy attribute of the node converter. """
        return self._nc.get(node.name, self._nc['__default__']).copy

    def _copy_children(self, node):
        """Return the copy_children attribute of the node converter. """
        return self._nc.get(node.name, self._nc['__default__']).copy_children

    def _get_direction(self, crt):
        """Returns the direction in which the traversal should go. """
        if isinstance(crt, CharacterData):
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
        self.doc = Document(doc.lang, doc.style)
        self.doc.uri_ = doc.uri_
        crtcopy = self.doc
        self._process(crtcopy)
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
                crtcopy = clone
                self._process(crtcopy)
            elif direction is 'r':
                if crt.next is None:
                    direction = 'u'
                    continue
                crt = crt.next
                clone = crt.clone_node()
                crtcopy.parent.append_child(clone)
                crtcopy = clone
                self._process(crtcopy)
            elif direction is 'u':
                if crt.parent is root:
                    break
                if crt.parent.next is None:
                    crt = crt.parent
                    crtcopy = crtcopy.parent
                    continue
                crt = crt.parent.next
                clone = crt.clone_node()
                crtcopy.parent.parent.append_child(clone)
                crtcopy = clone
                self._process(crtcopy)
            direction = self._get_direction(crt)
