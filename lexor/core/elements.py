"""
This module defines the elements of the document object model (DOM).
This implementation follows most of the recommendations of w3_.

.. _w3: http://www.w3.org/TR/2012/WD-dom-20121206/

Inheritance Tree
----------------

|   :class:`lexor.core.node.Node` (``__builtin__.object``)
|        :class:`.CharacterData`
|             :class:`.Text`
|             :class:`.ProcessingInstruction`
|             :class:`.Comment`
|             :class:`.CData`
|             :class:`.Entity`
|             :class:`.DocumentType`
|        :class:`.Element`
|             :class:`.RawText` (:class:`.Element`, :class:`.CharacterData`)
|             :class:`.Void`
|             :class:`.Document`
|                  :class:`.DocumentFragment`

----------------------------------------------------------------------

"""
import os
import sys
from lexor.core import Node
LC = sys.modules['lexor.core']
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-instance-attributes


class CharacterData(Node):
    """A simple interface to deal with strings. """

    __slots__ = ('data',)

    def __init__(self, text=''):
        """Set the data property to the value of `text` and set its
        name to ``'#character-data'``. """
        Node.__init__(self)
        self.name = '#character-data'
        self.data = text

    @property
    def node_value(self):
        """Return or set the value of the node. This property is a
        wrapper for the ``data`` attribute. """
        return self.data

    @node_value.setter
    def node_value(self, value):
        """Setter function for data attribute. """
        self.data = value


class Text(CharacterData):
    """A node to represent a string object."""

    __slots__ = ()

    def __init__(self, text=''):
        """Call its base constructor and set its name to ``'#text'``.
        """
        CharacterData.__init__(self, text)
        self.name = '#text'

    def clone_node(self, _=True):
        """Return a new ``Text`` node with the same data content. """
        return Text(self.data).set_position(self.line, self.column)


class ProcessingInstruction(CharacterData):
    """Represents a "processing instruction", used to keep
    processor-specific information in the text of the document. """
    __slots__ = ('_target', '_code')

    def __init__(self, target, data=''):
        """Create a `Text` node with its `data` set to data. """
        CharacterData.__init__(self, data)
        self.name = target
        self._target = target
        self._code = None

    @property
    def target(self):
        """The target of this processing instruction."""
        return self._target

    @property
    def code(self):
        """Return the compiled python code. This is only available
        after we call `compile_python`. """
        return self._code

    @target.setter
    def target(self, new_target):
        """Setter function. """
        self.name = new_target
        self._target = new_target

    def clone_node(self, _=True):
        """Returns a new PI with the same data content. """
        node = ProcessingInstruction(self._target, self.data)
        node.set_position(self.line, self.column)
        node._code = self._code
        return node

    def compile_python(self, uri='<?python>'):
        """Compiles the processing instruction to python bytecode.
        Since this is just a wrapper around the built in compile,
        this function may raise SyntaxError and TypeError exceptions.

        Note: Make sure to set the position of the node is set so that
        the correct line numbers appear on possible errors thrown by
        executing the instructions.
        """
        data = '{0}{1}'.format('\n'*(self.line-1), self.data)
        self._code = compile(data, uri, 'exec')


class Comment(CharacterData):
    """A node to store comments. """

    __slots__ = ('type',)

    def __init__(self, data=''):
        """Create a comment node. """
        CharacterData.__init__(self, data)
        self.name = '#comment'
        self.type = None

    @property
    def comment_type(self):
        """Type of comment. This property is meant to help with
        documents that support different styles of comments. """
        return self.type

    @comment_type.setter
    def comment_type(self, comment_type):
        """Setter function for comment_type. """
        self.type = comment_type

    def clone_node(self, _=True):
        """Returns a new comment with the same data content. """
        node = Comment(self.data)
        node.type = self.type
        node.set_position(self.line, self.column)
        return node


class CData(CharacterData):
    """Although this node has been deprecated from the DOM_, it
    seems that xml still uses it.

    .. _DOM: https://developer.mozilla.org/en-US/docs/Web/API/Node.nodeType

    """

    __slots__ = ()

    def __init__(self, data=''):
        """Create a CDATA node and set the node name to
        ``'#cdata-section'``."""
        CharacterData.__init__(self, data)
        self.name = '#cdata-section'

    def clone_node(self, _=True):
        """Returns a new ``CData`` node with the same data content.
        """
        return CData(self.data).set_position(self.line, self.column)


class Entity(CharacterData):
    """From merriam-webster definition_:

    - *Something that exists by itself*.
    - *Something that is separate from other things*.

    This node acts in the same way as a :class:`.Text` node but it
    has one main difference. The data it contains should contain no
    white spaces. This node should be reserved for special characters
    or words that have different meanings across different languages.
    For instance in HTML you have the ``&amp;`` to represent ``&``.
    In LaTeX you have to type ``\\$`` to represent ``$``. Using this
    node will help you handle these Entities hopefully more
    efficiently than simply finding and replacing them in a Text node.

    .. _definition: http://www.merriam-webster.com/dictionary/entity

    """

    __slots__ = ()

    def __init__(self, text=''):
        """Create an ``Entity`` node and set the node name to
        ``#entity``."""
        CharacterData.__init__(self, text)
        self.name = '#entity'

    def clone_node(self, _=True):
        """Returns a new ``Entity`` with the same data content. """
        return Entity(self.data).set_position(self.line, self.column)


class DocumentType(CharacterData):
    """A node to store the doctype declaration. This node will not
    follow the specifications at this point (May 30, 2013). It will
    simply recieve the string in between ``<!doctype`` and ``>``.

    Specs: http://www.w3.org/TR/2012/WD-dom-20121206/#documenttype

    """
    __slots__ = ()

    def __init__(self, data=''):
        """Create a ``DocumentType`` node and set its name to
        ``#doctype``. """
        CharacterData.__init__(self, data)
        self.name = '#doctype'
        # The next properties should be obtained from data
        # The specs do not mention type, instead they mention name.
        # The node name here is #doctype so that it can be easily
        # identified. The doctype "name" as they refer is called type.

    def clone_node(self, _=True):
        """Returns a new doctype with the same data content. """
        node = DocumentType(self.data)
        node.set_position(self.line, self.column)
        return node


class Element(Node):
    """Node object configured to have child Nodes and attributes. """

    def __init__(self, name, data=None):
        """The parameter ``data`` should be a ``dict`` object. The
        element will use the keys and values to populate its
        attributes. You may modify the elements internal dictionary.
        However, this may unintentially overwrite the attributes
        defined by the ``__setitem__`` method. If you wish to add
        another attribute to the ``Element`` object use the
        convention of adding an underscore at the end of the
        attribute. i.e

        >>> strong = Element('strong')
        >>> strong.message_ = 'An internal message'
        >>> strong['message'] = 'Attribute message'

        """
        Node.__init__(self)
        if data is None:
            data = dict()
        self.__dict__.update(data)
        if isinstance(data, dict):
            self._order = data.keys()
        else:
            self._order = list()
            for key, _ in data:
                if key not in self._order:
                    self._order.append(key)
        self.name = name
        self.child = list()

    def __call__(self, selector):
        """Return a :class:`lexor.core.selector.Selector` object. """
        return LC.Selector(selector, self)

    def update_attributes(self, node):
        """Copies the attributes of the input node into the calling
        node. """
        for k in node._order:
            self.__dict__[k] = node.__dict__[k]
            if k not in self._order:
                self._order.append(k)

    def __getitem__(self, k):
        """Return the `k`-th child of this node if `k` is an integer.
        Otherwise return the attribute of name with value of `k`.

        >>> x.__getitem__(k) is x[k]
        True

        """
        if isinstance(k, str):
            return self.__dict__[k]
        return self.child[k]

    def get(self, k, val=''):
        """Return the attribute of name with value of `k`."""
        return self.__dict__.get(k, val)

    def __setitem__(self, k, val):
        """Overloaded array operator. Appends or modifies an
        attribute. See its base method
        :meth:`lexor.core.node.Node.__setitem__` for documentation on
        when `val` is not string.

            x.__setitem__(attname) = 'att' <==> x[attname] = 'att'

        """
        if isinstance(k, str):
            self.__dict__[k] = val
            if k not in self._order:
                self._order.append(k)
            if k == 'id' and self.owner:
                self.owner.id_dict[k] = self
        else:
            Node.__setitem__(self, k, val)

    def __delitem__(self, k):
        """Remove a child or attribute.

            x.__delitem__(k) <==> del x[k]

        """
        if isinstance(k, str):
            self.__dict__.__delitem__(k)
            self._order.remove(k)
        else:
            Node.__delitem__(self, k)

    def __contains__(self, obj):
        """Return ``True`` if `obj` is a node and it is a child
        of this element or if `obj` is an attribute of this
        element. Return ``False`` otherwise.

        >>> x.__contains__(obj) == obj in x
        True

        """
        if isinstance(obj, Node):
            return self.child.__contains__(obj)
        else:
            return self._order.__contains__(obj)

    def contains(self, obj):
        """Unlike ``__contains__``, this method returns ``True`` if
        `obj` is any of the desendents of the node. """
        if obj.level < self.level + 1:
            return False
        while obj.level > self.level + 1:
            obj = obj.parent
            if obj is None:
                return False
        return obj in self

    # def __iter__(self):
    #     """Iterate over the element attributes names.
    #
    #     >>> for attribute_name in node: ...
    #
    #     """
    #     for k in self._order:
    #         yield k

    @property
    def attlen(self):
        """The number of attributes. """
        return len(self._order)

    @property
    def attributes(self):
        """Return a list of the attribute names in the element. """
        return list(self._order)

    @property
    def values(self):
        """Return a list of the attribute values in the Element. """
        return [self.__dict__[k] for k in self._order]

    def attribute(self, index):
        """Return the name of the attribute at the specified index. """
        return self._order[index]

    def attr(self, index):
        """Return the value of the attribute at the specified index.
        """
        return self.__dict__[self._order[index]]

    def items(self):
        """return all the items. """
        return zip(self._order, self.values)

    def update(self, dict_):
        """update with the values of `dict_`. useful when the element
        is empty and you created an Attr object. then just update the
        values."""
        for key, val in dict_.items():
            self.__setitem__(key, val)

    def rename(self, old_name, new_name):
        """Renames an attribute. 

        >>> from lexor.core.elements import Element
        >>> node = Element('div')
        >>> node['att1'] = 'val1'
        >>> node
        div[0x10a090750 att1="val1"]:
        >>> node.rename('att1', 'new-att-name')
        >>> node
        div[0x10a090750 new-att-name="val1"]:
        
        """
        if isinstance(old_name, str):
            index = self._order.index(old_name)
        else:
            index = old_name  # Assume old_name
        self.__dict__[new_name] = self.__dict__[self._order[index]]
        del self.__dict__[self._order[index]]
        self._order[index] = new_name

    def clone_node(self, deep=False, normalize=True):
        """Returns a new node. When deep is True, it will clone also
        clone all the child nodes."""
        # May want to provide a node to which the clone will be
        # appended to. If this is done then we will not have to
        # traverse through all the elements of the node to adjust
        # the level of the child nodes when we move the node around
        node = Element(self.name)
        node.update_attributes(self)
        if hasattr(self, '__directives__'):
            node.__directives__ = self.__directives__
            node.__info__ = self.__info__
        node.set_position(self.line, self.column)
        if deep is False or not self.child:
            return node
        crt = self
        crtcopy = node
        direction = 'd'
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
                crtcopy = crtcopy.parent
                if normalize:
                    crtcopy.normalize()
                if crt.parent is self:
                    break
                if crt.parent.next is None:
                    crt = crt.parent
                    continue
                crt = crt.parent.next
                clone = crt.clone_node()
                crtcopy.parent.append_child(clone)
            crtcopy = clone
            if crt.child:
                direction = 'd'
            else:
                direction = 'r'
        return node

    def get_elements_by_class_name(self, classname):
        """Return a list of all child elements which have all of the
        given class names. """
        nodes = []
        if not self.child:
            return nodes
        patterns = set([i.strip() for i in classname.split()])
        crt = self
        direction = 'd'
        while True:
            if direction is 'd':
                crt = crt.child[0]
            elif direction is 'r':
                if crt.next is None:
                    direction = 'u'
                    continue
                crt = crt.next
            elif direction is 'u':
                if crt.parent is self:
                    break
                if crt.parent.next is None:
                    crt = crt.parent
                    continue
                crt = crt.parent.next
            if isinstance(crt, Element) and 'class' in crt:
                crtclass = [i.strip() for i in crt['class'].split()]
                if patterns.issubset(set(crtclass)):
                    nodes.append(crt)
            if crt.child:
                direction = 'd'
            else:
                direction = 'r'
        return nodes

    def children(self, children=None, **keywords):
        """Set the elements children by providing a list of nodes or
        a string. If using a string then you may provide any of the
        following keywords to dictate how to parse and convert:

        - parser_style: ``'_'``
        - parser_lang: ``'html``
        - parser_defaults: ``None``,
        - convert_style: ``'_'``,
        - convert_from: ``None``,
        - convert_to: ``'html'``,
        - convert_defaults: ``None``,
        - convert: ``'false'``

        If no children are provided then it returns a string of the children
        written in plain html. To change this behavior provide the
        following keywords:

        - writer_style: ``'plain'``
        - writer_lang: ``'html``

        .. important::

            This requires the installation of lexor styles.

        """
        if children is None:
            lang = keywords.get('writer_lang', 'html')
            style = keywords.get('writer_style', 'plain')
            writer = LC.Writer(lang, style)
            if self.owner is not None and self.owner.defaults is not None:
                for var, val in self.owner.defaults.iteritems():
                    writer.defaults[var] = os.path.expandvars(str(val))
            for var, val in keywords.iteritems():
                writer.defaults[var] = os.path.expandvars(str(val))
            result = ''
            for child in self.child:
                writer.write(child)
                result += str(writer)
            writer.close()
            return result
        if isinstance(children, str):
            info = {
                'parser_style': '_',
                'parser_lang': 'html',
                'parser_defaults': None,
                'convert_style': '_',
                'convert_from': None,
                'convert_to': 'html',
                'convert_defaults': None,
                'convert': 'false'
            }
            for att in keywords:
                info[att] = keywords[att]
            parser = LC.Parser(info['parser_lang'],
                               info['parser_style'],
                               info['parser_defaults'])
            parser.parse(children)
            if info['convert'] == 'true' and info['convert_to'] is not None:
                if info['convert_from'] is None:
                    info['convert_from'] = info['parser_lang']
                converter = LC.Converter(info['convert_from'],
                                         info['convert_to'],
                                         info['convert_style'],
                                         info['convert_defaults'])
                converter.convert(parser.doc)
                children = converter.doc.pop()
                converter.log.pop()
            else:
                children = parser.doc
            children.temporary = True
        self.remove_children()
        self.extend_children(children)


class RawText(Element, CharacterData):
    """A few elements do not have children, instead they have data.
    Such elements exist in HTML: ``script``, ``title`` among
    others."""

    def __init__(self, name, data='', att=None):
        """You may provide `att` as a ``dict`` object. """
        CharacterData.__init__(self, data)
        Element.__init__(self, name, att)
        self.child = None

    def clone_node(self, deep=True, normalize=True):
        """Returns a new ``RawText`` element"""
        node = RawText(self.name)
        node.set_position(self.line, self.column)
        node.update_attributes(self)
        if deep is True:
            node.data = self.data
        return node


class Void(Element):
    """An element with no children. """

    def __init__(self, name, att=None):
        """You may provide `att` as a `dict` object. """
        Element.__init__(self, name, att)
        self.child = None

    def clone_node(self, _=True, normalize=True):
        """Returns a new ``Void`` element. """
        node = Void(self.name)
        node.set_position(self.line, self.column)
        node.update_attributes(self)
        return node


class Document(Element):
    """Contains information about the document that it holds. """

    def __init__(self, lang='xml', style='default'):
        """Creates a new document object and sets its name to
        ``#document``."""
        Element.__init__(self, '#document')
        self.level = -1
        self.owner = self
        self.lang = lang
        self.style = style
        self.uri_ = None
        self.defaults = None
        self.id_dict = dict()
        self.meta = dict()
        self.temporary = True

    def clone_node(self, deep=False, normalize=True):
        """Returns a new Document. Note: it does not copy
        the default values. """
        node = Document(self.lang, self.style)
        node.update_attributes(self)
        node.uri_ = self.uri_
        node.meta.update(self.meta)
        node.set_position(self.line, self.column)
        if deep is False or not self.child:
            return node
        clone = Element.clone_node(self, deep, normalize)
        clone.name = ''  # not a document
        node.extend_children(clone)
        return node

    @property
    def language(self):
        """The current document's language. This property is used by
        the writer to determine how to write the document.

        This property is a wrapper for the ``lang`` attribute. """
        return self.lang

    @language.setter
    def language(self, val):
        """Setter function for language. """
        self.lang = val

    @property
    def writing_style(self):
        """The current document's style. This property is used by
        the writer to determine how to write the document.

        This property is a wrapper for the ``style`` attribute.
        """
        return self.style

    @writing_style.setter
    def writing_style(self, val):
        """Docstring for setter. """
        self.style = val

    @property
    def uri(self):
        """The Uniform Resource Identifier. This property may become
        useful if the document represents a file. This property
        should be set by the a :class:`~lexor.core.parser.Parser`
        object telling us the location of the file that it parsed
        into the Document object. """
        return self.uri_

    @staticmethod
    def create_element(tagname, data=None):
        """Utility function to avoid having to import
        ``lexor.core.elements`` module. Returns an element object. """
        return Element(tagname, data)

    def get_element_by_id(self, element_id):
        """Return the first element, in tree order, within the
        document whose ID is element_id, or None if there is none. """
        return self.id_dict.get(element_id, None)


class DocumentFragment(Document):
    """Takes in an element and "steals" its children. This element
    should only be used as a temporary container. Note that the
    ``__str__`` method may not yield the expected results since all
    the function will do is use the ``__str__`` method in each of its
    children. First assign this object to an actual Document. """

    def __init__(self, lang='xml', style='default'):
        Document.__init__(self, lang, style)
        self.name = '#document-fragment'

    def append_child(self, new_child):
        """Adds the node new_child to the end of the list of children
        of this node. The children contained in a
        ``DocumentFragment`` only have a parent (the
        ``DocumentFragment``). As opposed as
        :meth:`lexor.core.node.Node.append_child` which also takes
        care of the ``prev`` and ``next`` attributes.
        """
        if isinstance(new_child, str):
            new_child = Text(new_child)
        elif not isinstance(new_child, Node):
            raise TypeError("Only Nodes can be appended.")
        if new_child.parent is not None:
            del new_child.parent[new_child.index]
        self.child.append(new_child)
        new_child.parent = self
        new_child.owner = self
        new_child.index = len(self.child) - 1
        new_child.next = None
        new_child.prev = None
        return new_child

    def __repr__(self):
        """
        >>> x.__repr__() is repr(x)

        """
        return ''.join([repr(node) for node in self.child])

    def __str__(self):
        """
        >>> x.__str__() is str(x)

        """
        return ''.join([str(node) for node in self.child])
