"""
This module defines the basic object of the document object model
(DOM).

"""
import os
import sys
from cStringIO import StringIO
LC = sys.modules['lexor.core']
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-instance-attributes


def _write_node_info(node, strf):
    """`Node` helper function to write the node information in
    __repr__. """
    strf.write('%s%s' % ('    '*node.level, node.name))
    if not isinstance(node, LC.Element):
        strf.write('[0x%x]' % id(node))
    else:
        att = ' '.join(['%s="%s"' % (k, v) for k, v in node.items()])
        strf.write('[0x%x' % id(node))
        if att != '':
            strf.write(' %s]' % att)
        else:
            strf.write(']')
    if node.name == '#document':
        strf.write(': (%s:%s:%s)' % (node.uri, node.lang, node.style))
    else:
        strf.write(':')
    direction = 'r'
    if isinstance(node, LC.CharacterData):
        strf.write(' %r' % node.data)
    elif node.child:
        direction = 'd'
    strf.write('\n')
    return direction


def _set_owner_and_level(node, owner, level):
    """Helper method for increase_child_level. """
    if node.owner is not owner:
        if isinstance(node, LC.Element) and 'id' in node:
            try:
                del node.owner.id_dict[node['id']]
            except (KeyError, AttributeError):
                pass
            if owner:
                owner.id_dict[node['id']] = node
        node.owner = owner
    node.level = level
    if node.name == '#document':
        node.level = level - 1


class Node(object):
    """Primary datatype for the entire Document Object Model. """
    __slots__ = ('name', 'owner', 'parent', 'index',
                 'prev', 'next', 'child', 'level')

    def __init__(self):
        """Initializes all data descriptors to ``None``. Each
        descriptor has an associated `READ-ONLY` property. Read the
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
        """
        .. admonition:: Read-Only Property
            :class: note

            The name of this node. Its value depends on the node
            type. This property is associated with the attribute
            ``name``. """
        return self.name

    @property
    def owner_document(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The :class:`~lexor.core.elements.Document` in which this
            node resides. This property is associated with the
            attribute ``owner``. """
        return self.owner

    @property
    def parent_node(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The parent of this node. If the node has been just
            created or removed from a ``Document`` then this property
            is ``None``. This property is associated with the
            attribute ``parent``. """
        return self.parent

    @property
    def node_index(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The number of preceding siblings.

            >>> x is x.parent_node[x.node_index]
            True

            This property is associated with the attribute ``index``.
            """
        return self.index

    @property
    def node_level(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The nodes level of containtment in a
            :class:`~lexor.core.elements.Document` object.

            This property is associated with the attribute ``level``.
            """
        return self.level

    @property
    def element_index(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The number of preceding element siblings."""
        index = 0
        crt = self
        while crt.prev is not None:
            crt = crt.prev
            if isinstance(crt, LC.Element):
                index += 1
        return index

    @property
    def previous_sibling(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The node immediately preceding this node. If this
            property is not `None` then

            >>> x.previous_sibling <==> x.parent_node[x.node_index - 1]

            This property is associated with the attribute
            ``prev``."""
        return self.prev

    @property
    def next_sibling(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The node immediately following this node. If this
            property is not `None` then

            >>> x.next_sibling <==> x.parent_node[x.node_index + 1]

            This property is associated with the attribute
            ``next``."""
        return self.next

    @property
    def previous_element(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The last sibling :class:`~lexor.core.elements.Element`
            preceding this node.

        """
        crt = self
        while crt.prev is not None:
            crt = crt.prev
            if isinstance(crt, LC.Element):
                return crt
        return None

    @property
    def next_element(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The sibling :class:`~lexor.core.elements.Element` after
            this node. """
        crt = self
        while crt.next is not None:
            crt = crt.next
            if isinstance(crt, LC.Element):
                return crt
        return None

    def remove_children(self):
        """Remove all the child nodes. """
        for child in self.child:
            child.disconnect()
        del self.child[:]

    def __repr__(self):
        """>>> x.__repr__() == repr(x)
        True
        """
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
        """>>> x.__str__() == str(x)
        True
        """
        if self.owner is None:
            style = 'default'
            lang = 'xml'
        else:
            style = self.owner.style
            lang = self.owner.lang
        writer = LC.Writer(lang, style)
        if self.owner is not None and self.owner.defaults is not None:
            for var, val in self.owner.defaults.iteritems():
                writer.defaults[var] = os.path.expandvars(str(val))
        writer.write(self)
        val = str(writer)
        writer.close()
        return val

    def insert_before(self, index, new_child):
        """Inserts `new_child` to the list of children just before
        the child specified by `index`. """
        if not isinstance(new_child, Node):
            new_child = LC.Text(str(new_child))
        elif isinstance(new_child, LC.DocumentFragment):
            msg = "Use extend_before for LC.DocumentFragment Nodes."
            raise TypeError(msg)
        index = self.insert_node_before(index, new_child)
        while index < len(self.child):
            self[index].index = index
            index += 1
        return self

    def extend_before(self, index, new_children):
        """Inserts the contents of an iterable containing nodes just
        before the child specified by `index`. The following are
        equivalent:

        >>> while doc: node.parent.insert_before(index, doc[0])

        >>> node.extend_before(index, doc)

        The second form, however, has a more efficient reindexing
        method. """
        if isinstance(new_children, (list, LC.DocumentFragment)):
            for node in new_children:
                if node.name == '#document' and node.temporary:
                    if self.owner:
                        self.owner.meta.update(node.meta)
                        node.meta = dict()
                    while node:
                        index = self.insert_node_before(index, node[0])
                else:
                    index = self.insert_node_before(index, node)
        else:
            if new_children.name == '#document':
                if new_children.temporary and self.owner:
                    self.owner.meta.update(new_children.meta)
                    new_children.meta = dict()
            while new_children:
                index = self.insert_node_before(index, new_children[0])
        while index < len(self.child):
            self[index].index = index
            index += 1
        return self

    def append_child(self, new_child):
        """Adds the node `new_child` to the end of the list of
        children of this node. If the node is a
        :class:`~lexor.core.elements.DocumentFragment` then it
        appends its child nodes. Returns the calling node. """
        if not isinstance(new_child, Node):
            new_child = LC.Text(str(new_child))
        elif isinstance(new_child, LC.DocumentFragment):
            msg = "Use extend_children for `DocumentFragment` Nodes."
            raise TypeError(msg)
        self.append_child_node(new_child)
        return self

    def extend_children(self, new_children):
        """Extend the list of children by appending children from an
        iterable containing nodes. """
        if isinstance(new_children, (list, LC.DocumentFragment)):
            for node in new_children:
                if node.name == '#document' and node.temporary:
                    if self.owner:
                        self.owner.meta.update(node.meta)
                        node.meta = dict()
                    while node:
                        self.append_child_node(node[0])
                else:
                    self.append_child_node(node)
        else:
            if new_children.name == '#document':
                if new_children.temporary and self.owner:
                    self.owner.meta.update(new_children.meta)
                    new_children.meta = dict()
            while new_children:
                self.append_child_node(new_children[0])
        return self

    def append_after(self, new_child):
        """Place `new_child` after the node. """
        if self.index+1 == len(self.parent):
            self.parent.append_child(new_child)
        else:
            self.parent.insert_before(self.index+1, new_child)

    def append_nodes_after(self, new_children):
        """Place `new_children` after the node. """
        if self.index+1 == len(self.parent):
            self.parent.extend_children(new_children)
        else:
            self.parent.extend_before(self.index+1, new_children)

    def prepend_before(self, new_child):
        """Place `new_child` before the node. """
        self.parent.insert_before(self.index, new_child)

    def prepend_nodes_before(self, new_children):
        """Place `new_children` before the node. """
        self.parent.extend_before(self.index, new_children)

    def normalize(self):
        """Removes empty :class:`~lexor.core.elements.Text` nodes,
        and joins adjacent :class:`~lexor.core.elements.Text`
        nodes."""
        if not self.child:
            return self
        crt = self.child[0]
        while crt is not None:
            if isinstance(crt, LC.Text):
                if crt.data == '':
                    nextnode = crt.next
                    del crt.parent[crt.index]
                    crt = nextnode
                elif isinstance(crt.next, LC.Text):
                    marked_node = crt.next
                    start = marked_node.index
                    while isinstance(marked_node, LC.Text):
                        crt.data += marked_node.data
                        end = marked_node.index
                        marked_node = marked_node.next
                    crt = marked_node
                    del self[start:end+1]
                else:
                    crt = crt.next
            else:
                crt = crt.next
        return self

    def __len__(self):
        """Return the number of child nodes.

        >>> x.__len__() == len(x)
        True

        """
        if self.child is None:
            return 0
        return len(self.child)

    def __getitem__(self, i):
        """Return the `i`-th child of this node.

        >>> x.__getitem__(i) <==> x[i]
        >>> x.__getitem__(slice(i, j)) <==> x[i:j]
        >>> x.__getitem__(slice(i, j, dt)) <==> x[i:j:dt]

        When using a slice, the ``__getitem__`` function will return
        a list with references to the requested nodes. """
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

        >>> x.__delitem__(index) <==> del x[index]
        >>> x.__delitem__(slice(i, j)) <==> del x[i:j]
        >>> x.__delitem__(slice(i, j, dt)) <==> del x[i:j:dt]

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

        >>> x.__setitem__(index) = node <==> x[index] = node
        >>> x.__setitem__(slice(i, j)) = dfrag <==> x[i:j] = dfrag
        >>> x.__setitem__(slice(i, j, dt)) = dfrag <==> x[i:j:dt] = dfrag

        When using slices the nodes to be assigned to the indices
        need to be contained in a
        :class:`~lexor.core.elements.DocumentFragment` node. This
        function does not support insertion as the regular slice for
        list does. To insert use a node use :meth:`insert_before` or
        :meth:`append_after`."""
        indices = self._get_indices(index)
        if not isinstance(node, Node):
            raise TypeError("items must be Nodes")
        if node is self:
            raise TypeError("A node cannot have itself as a child.")
        if not isinstance(node, LC.DocumentFragment):
            # Better take a look at this, DocFrag needs more development
            nodes = LC.DocumentFragment(node)
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

    def get_nodes_by_name(self, name):
        """Return a ``list`` of child nodes that have the given
        `name`. """
        nodes = []
        if not self.child:
            return nodes
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
            if crt.name == name:
                nodes.append(crt)
            if crt.child:
                direction = 'd'
            else:
                direction = 'r'
        return nodes

    def iter_child_elements(self):
        """Iterate over child nodes which are
        :class:`~lexor.core.elements.Element` instances.

        >>> for ele in node.iter_child_elements(): ...

        """
        for k in self.child:
            if isinstance(k, LC.Element):
                yield k

    def set_parent(self, parent, index):
        """
        .. admonition:: Helper Method
            :class: caution

            Modifies the parent node and takes care of the child node
            levels. """
        self.parent = parent
        self.index = index
        if self.name in ['#document', '#document-fragment']:
            self.level = parent.level
        else:
            self.level = parent.level + 1
        self.owner = parent.owner
        if self.owner and isinstance(self, LC.Element) and 'id' in self:
            self.owner.id_dict[self['id']] = self
        self.increase_child_level()

    def disconnect(self):
        """
        .. admonition:: Helper Method
            :class: caution

            Reset its attributes.
        """
        if self.owner and isinstance(self, LC.Element):
            try:
                del self.owner.id_dict[self['id']]
            except (KeyError, AttributeError):
                pass
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

    def set_prev(self, node):
        """
        .. admonition:: Helper Method
            :class: caution

            Sets the ``prev`` attribute.
        """
        self.prev = node
        node.next = self

    def set_next(self, node):
        """
        .. admonition:: Helper Method
            :class: caution

            Sets the ``next`` attribute.
        """
        self.next = node
        node.prev = self

    def increase_child_level(self):
        """
        .. admonition:: Helper Method
            :class: caution

            Sets the level of the child nodes.
        """
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
            _set_owner_and_level(crt, owner, level)
            if crt.child:
                direction = 'd'
            else:
                direction = 'r'

    def append_child_node(self, new_child):
        """
        .. admonition:: Helper Method
            :class: caution

            Use this method to insert a node at a the end of the
            child list. See :meth:`append_child` and
            :meth:`extend_children` to see this method in
            action.
        """
        if new_child.parent is not None:
            del new_child.parent[new_child.index]
        self.child.append(new_child)
        new_child.set_parent(self, len(self.child) - 1)
        try:
            new_child.set_prev(self.child[-2])
        except IndexError:
            pass

    def insert_node_before(self, index, new_child):
        """
        .. admonition:: Helper Method
            :class: caution

            Insert a `new_child` at a given `index`. See
            :meth:`insert_before` and :meth:`extend_before` to see
            this method in action."""
        if new_child.parent is not None:
            del new_child.parent[new_child.index]
        self.child.insert(index, new_child)
        new_child.set_parent(self, index)
        if index > 0:
            new_child.set_prev(self.child[index-1])
        try:
            new_child.set_next(self.child[index+1])
        except IndexError:
            pass
        self[index].index = index
        index += 1
        return index
