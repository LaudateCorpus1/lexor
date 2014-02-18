"""lexor elements

This module defines the document object model (DOM). This
implementation follows most of the recommendations of [w3].

[w3]: http://www.w3.org/TR/2012/WD-dom-20121206/

"""

import os
from cStringIO import StringIO
import lexor.core.writer

__all__ = [
    'Node', 'CharacterData', 'Text', 'ProcessingInstruction', 'Comment',
    'DocumentType',
    'Element', 'RawText', 'Void', 'Document', 'DocumentFragment'
]


def _set_node_owner_level(node, owner, level):
    """`Node` helper function to write the HELPER-METHOD
    increase_child_level. """
    node.owner = owner
    if node.name == '#document':
        node.level = level - 1
    else:
        node.level = level
    if isinstance(node, CharacterData):
        return 'r'
    elif node.child:
        return 'd'
    return 'r'


def _write_node_info(node, strf):
    """`Node` helper function to write the node information in
    __repr__. """
    strf.write('%s%s' % ('    '*node.level, node.name))
    strf.write('@[0x%x]' % id(node))
    if node.name == '#document':
        strf.write(':(%s:%s)' % (node.lang, node.style))
    elif node.name == 'msg':
        pos = node['position']
        strf.write(':(%d, %d)' % (pos[0], pos[1]))
    else:
        strf.write(':')
    if isinstance(node, CharacterData):
        strf.write(repr(node.data))
        strf.write('\n')
        return 'r'
    elif node.child:
        strf.write('\n')
        return 'd'
    else:
        strf.write('\n')
        return 'r'


# There might be a thing as too many properties and methods.
# I don't believe this is the case. Deal with it.
# pylint: disable=R0904,R0902
class Node(object):
    """Primary datatype for the entire Document Object Model. """
    __slots__ = ('name', 'owner', 'parent', 'index',
                 'prev', 'next', 'child', 'level')

    def __init__(self):
        """Initializes all data descriptors to `None`. Each
        descriptor has an associeted READ-ONLY property. Read the
        comment on each property to see what each descriptor
        represents. """
        self.name = None
        self.owner = None
        self.parent = None
        self.index = None
        self.prev = None
        self.next = None
        self.child = None
        self.level = 0

    @property
    def node_name(self):
        """READ-ONLY: The name of this node. Value depends on its
        node type.

        PERFORMANCE-TIP: Consider accessing this property directly
        by accessing the attribute `name` in case of performance
        issues. """
        return self.name

    @property
    def owner_document(self):
        """READ-ONLY: The `Document` in which this node resides.

        PERFORMANCE-TIP: Consider accessing this property directly
        by accessing the attribute `owner` in case of performance
        issues. """
        return self.owner

    @property
    def parent_node(self):
        """READ-ONLY: The parent of this node. All nodes may have a
        parent. If the node has been just created or removed from a
        `Document` then this property is None.

        PERFORMANCE-TIP: Consider accessing this property directly
        by accessing the attribute `parent` in case of performance
        issues. """
        return self.parent

    def set_parent(self, parent, index):
        """HELPER-METHOD: Use this function to modify the parent
        node. """
        self.parent = parent
        self.index = index
        if self.name in ['#document', '#document-fragment']:
            self.level = parent.level
        else:
            self.level = parent.level + 1
        self.owner = parent.owner
        self.increase_child_level()

    @property
    def node_index(self):
        """READ-ONLY: The number of preceding siblings.

            x <==> x.parent_node[x.node_index]

        PERFORMANCE-TIP: Consider accessing this property directly
        by accessing the attribute `index` in case of performance
        issues. """
        return self.index

    @property
    def element_index(self):
        """READ-ONLY: The number of preceding element siblings. """
        index = 0
        crt = self
        while crt.prev is not None:
            crt = crt.prev
            if isinstance(crt, Element):
                index += 1
        return index

    @property
    def previous_sibling(self):
        """READ-ONLY: The node immediately preceding this node. If
        this property is not `None` then

            x.previous_sibling <==> x.parent_node[x.node_index - 1]

        PERFORMANCE-TIP: Consider accessing this property directly
        by accessing the attribute `prev` in case of performance
        issues. """
        return self.prev

    @property
    def previous_element(self):
        """READ-ONLY: The last sibling Element preceding this node.
        """
        crt = self
        while crt.prev is not None:
            crt = crt.prev
            if isinstance(crt, Element):
                break
        return crt

    def set_prev(self, node):
        """HELPER-METHOD: Use this function to set the `prev`
        attribute. """
        self.prev = node
        node.next = self

    @property
    def next_sibling(self):
        """READ-ONLY: The node immediately following this node. If
        this property is not `None` then

            x.next_sibling <==> x.parent_node[x.node_index + 1]

        PERFORMANCE-TIP: Consider accessing this property directly
        by accessing the attribute `next` in case of performance
        issues. """
        return self.next

    def set_next(self, node):
        """HELPER-METHOD: Use this function to set the `next`
        attribute. """
        self.next = node
        node.prev = self

    @property
    def node_level(self):
        """READ-ONLY: The node's level of containtment in a
        `Document` object.

        PERFORMANCE-TIP: Consider accessing this property directly
        by accessing the attribute `level` in case of performance
        issues. """
        return self.level

    def increase_child_level(self):
        """HELPER-METHOD: Use this function to set the level of the child
        nodes. """
        if self.child:
            crt = self
            direction = 'd'
            level = self.level
            owner = self.owner
        else:
            return
        while True:
            if direction is 'd':
                level += 1
                crt = crt.child[0]
            elif direction is 'r':
                if crt.next is None:
                    direction = 'u'
                    continue
                crt = crt.next
            elif direction is 'u':
                level -= 1
                if crt.parent is self:
                    break
                if crt.parent.next is None:
                    crt = crt.parent
                    continue
                crt = crt.parent.next
            direction = _set_node_owner_level(crt, owner, level)

    def disconnect(self):
        """HELPER-METHOD: Use this function to reset the node's attributes.
        """
        self.owner = None
        self.parent = None
        self.index = None
        self.prev = None
        self.next = None
        if self.name in ['#document', '#document-fragment']:
            self.level = -1
        else:
            self.level = 0
        self.increase_child_level()

    def __repr__(self):
        """x.__repr__() <==> repr(x)"""
        strf = StringIO()
        crt = self
        direction = _write_node_info(crt, strf)
        if direction is not 'd':
            return strf.getvalue()
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
            direction = _write_node_info(crt, strf)
        return strf.getvalue()

    def __str__(self):
        """x.__str__() <==> str(x)"""
        if self.owner is None:
            style = 'default'
            lang = 'xml'
        else:
            style = self.owner.style
            lang = self.owner.lang
        writer = lexor.core.writer.Writer(lang, style)
        if self.owner is not None and self.owner.defaults is not None:
            for var, val in self.owner.defaults.iteritems():
                writer.defaults[var] = os.path.expandvars(str(val))
        writer.write(self)
        val = str(writer)
        writer.close()
        return val

    def append_child(self, new_child):
        """Adds the node new_child to the end of the list of children
        of this node. If the node is a `DocumentFragment` then it
        appends its child nodes. Returns the calling node. """
        if not isinstance(new_child, Node):
            new_child = Text(str(new_child))
        elif isinstance(new_child, DocumentFragment):
            msg = "Use extend_children for DocumentFragment Nodes."
            raise TypeError(msg)
        if new_child.parent is not None:
            del new_child.parent[new_child.index]
        self.child.append(new_child)
        new_child.set_parent(self, len(self.child) - 1)
        try:
            new_child.set_prev(self.child[-2])
        except IndexError:
            return self
        return self

    def extend_children(self, new_children):
        """Extend the list of children by appending children from an
        iterable containing nodes. """
        if isinstance(new_children, DocumentFragment):
            for i in xrange(len(new_children)):
                node = new_children[i]
                self.child.append(node)
                node.set_parent(self, len(self.child) - 1)
                try:
                    node.set_prev(self.child[-2])
                except IndexError:
                    pass
            return self
        else:
            for i in xrange(len(new_children)):
                self.append_child(new_children[i])

    def __len__(self):
        """Return the number of child nodes.

            x.__len__() <==> len(x)

        """
        if self.child is None:
            return 0
        return len(self.child)

    def __getitem__(self, i):
        """Return the i-th child of this node.

            x.__getitem__(i) <==> x[i]
            x.__getitem__(slice(i, j)) <==> x[i:j]
            x.__getitem__(slice(i, j, dt)) <==> x[i:j:dt]

        When using a slice, the __getitem__ function will return a list
        with references to the requested nodes. """
        return self.child[i]

    def _get_indices(self, i):
        """PRIVATE-METHOD: Returns a slice and the range of indices
        to be replaced. `i` is assumed to be a slice or an int. """
        if isinstance(i, int):
            if i < 0:
                i += len(self.child)
                i = slice(i, i + 1)
            else:
                i = slice(i, i + 1)
        return i, xrange(*i.indices(len(self.child)))

    def __delitem__(self, index):
        """Delete child nodes.

            x.__delitem__(index) <==> del x[index]
            x.__delitem__(slice(i, j)) <==> del x[i:j]
            x.__delitem__(slice(i, j, dt)) <==> del x[i:j:dt]

        """
        index, indices = self._get_indices(index)
        if index.step is None or index.step > 0:
            indices = reversed(indices)
        for index in indices:
            self.child[index].disconnect()
            del self.child[index]
            if index > 0:
                try:
                    self.child[index].set_prev(self.child[index - 1])
                except IndexError:
                    self.child[index - 1].next = None
            elif self.child:
                self.child[index].prev = None
        for i in xrange(index, len(self.child)):
            self.child[i].index = i

    def __setitem__(self, index, node):
        """Replace child nodes.

            x.__setitem__(index) = node <==> x[index] = node
            x.__setitem__(slice(i, j)) = dfrag <==> x[i:j] = dfrag
            x.__setitem__(slice(i, j, dt)) = dfrag <==> x[i:j:dt] = dfrag

        When using slices the nodes to be assigned to the indices
        need to be contained in a `DocumentFragment` node. This
        function does not support insertion as the regular slice for
        list does. To insert use `insert_prev`."""
        indices = self._get_indices(index)
        if not isinstance(node, Node):
            raise TypeError("items must be Nodes")
        if node is self:
            raise TypeError("A node cannot have itself as a child.")
        if not isinstance(node, DocumentFragment):
            nodes = DocumentFragment(node)
        else:
            nodes = node
        if len(indices) != len(nodes):
            msg = "attempt to assign sequence of size %d to extended" \
                  "slice of size %d" % (len(nodes), len(indices))
            raise ValueError(msg)
        for i in xrange(len(nodes)):
            index = indices[i]
            node = nodes[i]
            if node.parent is self:
                raise ValueError("Node is already the child at index %d" %
                                 node.index)
            if node.parent is not None:
                del node.parent[node.index]
            # Disconnect the current Node
            self.child[index].disconnect()
            # Assign and connect the new Node
            self.child[index] = node
            node.set_parent(self, index)
            try:
                node.set_next(self.child[index + 1])
            except IndexError:
                pass
            try:
                node.set_prev(self.child[index - 1])
            except IndexError:
                pass
        return node


class CharacterData(Node):
    """A simple interface to deal with strings. """

    __slots__ = ('data')

    def __init__(self, text=''):
        """Set the data property to the value of `text`. """
        Node.__init__(self)
        self.name = '#character-data'
        self.data = text

    @property
    def node_value(self):
        """Return or set the value of the current node.

        PERFORMANCE-TIP: Consider accessing this property directly
        by accessing the attribute `data` in case of performance
        issues. """
        return self.data

    @node_value.setter
    def node_value(self, value):
        """Setter function for data attribute. """
        self.data = value


class Text(CharacterData):
    """A node to represent a string object."""

    __slots__ = ()

    def __init__(self, text=''):
        """Create a `Text` node with its data set to `text`."""
        CharacterData.__init__(self, text)
        self.name = '#text'

    def clone_node(self, _=True):
        """Returns a new Text with the same data content. """
        return Text(self.data)


class ProcessingInstruction(CharacterData):
    """Represents a "processing instruction", used to keep
    processor-specific information in the text of the document. """
    __slots__ = ('_target')

    def __init__(self, target, data=''):
        """Create a `Text` node with its `data` set to data. """
        CharacterData.__init__(self, data)
        self.name = target
        self._target = target

    @property
    def target(self):
        """The target of this processing instruction."""
        return self._target

    @target.setter
    def target(self, new_target):
        """Setter function. """
        self._target = new_target

    def clone_node(self, _=True):
        """Returns a new PI with the same data content. """
        return ProcessingInstruction(self._target, self.data)


class Comment(CharacterData):
    """A node to store comments. """

    __slots__ = ('type')

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
        return node


class CData(CharacterData):
    """Although this node has been deprecated from the [DOM][1], it seems
    that xml still uses it.

    [1]: https://developer.mozilla.org/en-US/docs/Web/API/Node.nodeType

    """

    __slots__ = ()

    def __init__(self, data=''):
        """Create a CDATA node"""
        CharacterData.__init__(self, data)
        self.name = '#cdata-section'

    def clone_node(self, _=True):
        """Returns a new CData with the same data content. """
        return CData(self.data)


class Entity(CharacterData):
    """From merriam-webster [definition][1]:

    - something that exists by itself.
    - something that is separate from other things.

    This node acts in the same way as a Text node but it has one main
    difference. The data it contains should contain no white spaces.
    This node should be reserved for special characters or words that
    have different meanings across different languages. For instance
    in HTML you have the `&amp;` to represent `&`. In LaTeX you have
    to type `\\$` to represent `$`. Using this node will help you
    handle these Entities hopefully more efficiently than simply
    finding and replacing them in a Text node.

    [1]: http://www.merriam-webster.com/dictionary/entity

    """

    __slots__ = ()

    def __init__(self, text=''):
        """Create an `Entity` node with its data set to `text`."""
        CharacterData.__init__(self, text)
        self.name = '#entity'

    def clone_node(self, _=True):
        """Returns a new Entiry with the same data content. """
        return Entity(self.data)


class DocumentType(CharacterData):
    """A node to store the doctype declaration. This node will not
    follow the specifications at this point (May 30, 2013). This node
    will simply recieve the string in between `<!doctype ` and `>`.

    Specs: http://www.w3.org/TR/2012/WD-dom-20121206/#documenttype

    """
    __slots__ = ()

    def __init__(self, data=''):
        """Create a `doctype` node with its `data` set to data. """
        CharacterData.__init__(self, data)
        self.name = '#doctype'
        # The next properties should be obtained from data
        # The specs do not mention type, instead they mention name.
        # The node name here is #doctype so that it can be easily
        # identified. The doctype "name" as they refer is called type.

    def clone_node(self, _=True):
        """Returns a new doctype with the same data content. """
        node = DocumentType(self.data)
        return node


class Element(Node):
    """Node object configured to have child Nodes and attributes. """

    def __init__(self, name, data=None):
        """The parameter `data` should be a `dict` object. The
        element will use the keys and values to populate its
        attributes. You may modify the elements internal dictionary.
        However, this may unintentially overwrite the attributes
        defined by the `__setitem__` method. If you wish to add
        another attribute to the `Element` object use the convention
        of adding an underscore at the end of the attribute. i.e

            >> strong = Element('strong')
            >> strong.message_ = 'An internal message'
            >> strong['message'] = 'Attribute message'

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

    def update_attributes(self, node):
        """Copies the attributes of the node into the calling node. """
        for k in node:
            self.__dict__[k] = node.__dict__[k]
            if k not in self._order:
                self._order.append(k)

    def __getitem__(self, k):
        """Return the k-th child of this node if `k` is an integer.
        Otherwise return the attribute of name with value of `k`.

            x.__getitem__(k) <==> x[k]

        """
        if isinstance(k, str):
            return self.__dict__[k]
        if self.child:
            return self.child[k]
        return None

    def __setitem__(self, k, val):
        """
        x.__setitem__(index) = node <==> x[index] = node
        x.__setitem__(slice(i, j)) = [...] <==> x[i:j] = [...]
        x.__setitem__(slice(i, j, dt)) = [...] <==> x[i:j:dt] = [...]

        Note: When using slices the nodes to be assigned to the indices need
        to be contained in a builtin list. The size of this list must be
        the same as the slice. This function does not support insertion as
        the regular slice for list does. To insert an object use insert.

        x.__setitem__(attname) = 'att' <==> x[attname] = 'att'

        Note: The behaviour of Attribute still applies to a Proper Node.
        """
        if isinstance(k, str):
            self.__dict__[k] = val
            if k not in self._order:
                self._order.append(k)
        else:
            Node.__setitem__(self, k, val)

    def __delitem__(self, k):
        if isinstance(k, str):
            self.__dict__.__delitem__(k)
            self._order.remove(k)
        else:
            Node.__delitem__(self, k)

    def __contains__(self, obj):
        """Return true if `obj` is a Node and it is a child of this `Element`.
        Return true if `obj` is an attribute of this `Element`. Return false
        otherwise.

            x.__contains__(obj) <==> obj in x

        """
        if isinstance(obj, Node):
            return self.child.__contains__(obj)
        else:
            return self._order.__contains__(obj)

    def __iter__(self):
        for k in self._order:
            yield k

    @property
    def attributes(self):
        """Return a list of all the attributes in the Element. """
        return list(self._order)

    def items(self):
        """return all the items. """
        return zip(self._order, self.values)

    @property
    def values(self):
        """Return a list of the attribute values in the Element. """
        return [self.__dict__[k] for k in self._order]

    def update(self, dict_):
        """update with the values of dict_. useful when the element
        is empty and you created an Attr object. then just update the
        values."""
        for key, val in dict_.items():
            self.__setitem__(key, val)

    @property
    def attlen(self):
        """The number of attributes. """
        return len(self._order)

    def attr(self, index):
        """obj.attr(num)"""
        return self.__dict__[self._order[index]]

    def clone_node(self, deep=False):
        """Returns a new element"""
        node = Element(self.name)
        node.update_attributes(self)
        if deep is False:
            return node
        # Tree traversal goes here
        return node


class RawText(Element, CharacterData):
    """Docstring for raw text"""

    def __init__(self, name, data=''):
        CharacterData.__init__(self, data)
        Element.__init__(self, name)
        self.child = None

    def clone_node(self, deep=True):
        """Returns a new element"""
        node = RawText(self.name)
        node.update_attributes(self)
        if deep is True:
            node.data = self.data
        return node


class Void(Element):
    """Docstring for raw Void"""
    def __init__(self, name, data=None):
        Element.__init__(self, name, data)
        self.child = None


class Document(Element):
    """Contains information about the document that it holds. """

    def __init__(self, lang='xml', style='default'):
        Element.__init__(self, '#document')
        self.level = -1
        self.owner = self
        self.lang = lang
        self.style = style
        self.uri_ = None
        self.defaults = None

    @property
    def language(self):
        """The current document's language. This property is used by
        the writer to determine how to write the document.

        PERFORMANCE-TIP: Consider accessing this property directly
        by accessing the attribute `lang` in case of performance
        issues. """
        return self.lang

    @language.setter
    def language(self, val):
        """Setter function for language. """
        self.lang = val

    @property
    def writing_style(self):
        """The current document's style. This property is used by
        the writer to determine how to write the document.

        For performance simply use self.style.
        """
        return self.style

    @property
    def uri(self):
        """The Uniform Resource Identifier. This property may become
        useful if the document represents a file. This property
        should be set by the a Parser object telling you the location
        of the file that it parsed into the Document object. """
        return self.uri_

    @writing_style.setter
    def writing_style(self, val):
        """Docstring for setter. """
        self.style = val


class DocumentFragment(Document):
    """Takes in an element and "steals" its children. This element
    should only be used as a temporary container. Note that the
    __str__ function may not yield the expected results since all the
    function will do is use the __str__ function in each of its
    children. First assign this object to an actual Document. """

    def __init__(self, lang='xml', style='default'):
        Document.__init__(self, lang, style)
        self.name = '#document-fragment'

    def append_child(self, new_child):
        """Adds the node new_child to the end of the list of children
        of this node. The children contained in a `DocumentFragment`
        only have a parent (the `DocumentFragment`). As opposed as
        the `Node` append_child which also takes care of the `prev`
        and `next` attributes. """
        if isinstance(new_child, str):
            new_child = Text(new_child)
        elif not isinstance(new_child, Node):
            raise TypeError("Only Nodes can be appended.")
        if new_child.parent is not None:
            del new_child.parent[new_child.index]
        self.child.append(new_child)
        new_child.parent = self
        new_child.owner = self
        return new_child

    def __repr__(self):
        """x.__repr__() <==> repr(x)"""
        return ''.join([repr(node) for node in self.child])

    def __str__(self):
        """x.__str__() <==> str(x)"""
        return ''.join([str(node) for node in self.child])
