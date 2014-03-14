"""lexor node

This module defines the basic object of document object model (DOM).

"""
# This comment disables pylint warnings:
# - Properties and methods:
#       pylint: disable=R0904,R0902

import os
import sys
from cStringIO import StringIO
from lexor.core.writer import Writer
LCE = sys.modules['lexor.core.elements']


def _write_node_info(node, strf):
    """`Node` helper function to write the node information in
    __repr__. """
    strf.write('%s%s' % ('    '*node.level, node.name))
    if not isinstance(node, LCE.Element):
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
    if isinstance(node, LCE.CharacterData):
        strf.write(' %r' % node.data)
    elif node.child:
        direction = 'd'
    strf.write('\n')
    return direction


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
        if isinstance(self, LCE.Element) and 'id' in self:
            self.owner.id_dict[self['id']] = self
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
            if isinstance(crt, LCE.Element):
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
        """READ-ONLY: The last sibling LCE.Element preceding this
        node. """
        crt = self
        while crt.prev is not None:
            crt = crt.prev
            if isinstance(crt, LCE.Element):
                return crt
        return None

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

    @property
    def next_element(self):
        """READ-ONLY: The sibling LCE.Element after this node. """
        crt = self
        while crt.next is not None:
            crt = crt.next
            if isinstance(crt, LCE.Element):
                return crt
        return None

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
        """HELPER-METHOD: Use this function to set the level of the
        child nodes. """
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
            crt.owner = owner
            crt.level = level
            if crt.name == '#document':
                crt.level = level - 1
            if crt.child:
                direction = 'd'
            else:
                direction = 'r'

    def disconnect(self):
        """HELPER-METHOD: Use this function to reset the node's
        attributes. """
        if isinstance(self, LCE.Element) and 'id' in self:
            del self.owner.id_dict[self['id']]
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
        writer = Writer(lang, style)
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
            new_child = LCE.Text(str(new_child))
        elif isinstance(new_child, LCE.DocumentFragment):
            msg = "Use extend_before for LCE.DocumentFragment Nodes."
            raise TypeError(msg)
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
        while index < len(self.child):
            self[index].index = index
            index += 1
        return self

    def extend_before(self, index, new_children):
        """Inserts the contents of an iterable containing nodes just
        before the child specified by `index`. The following are
        equivalent:

            while doc:
                node.parent.insert_before(index, doc[0])

            node.extend_before(index, doc)

        The second form, however, has a more efficient reindexing
        method."""
        if isinstance(new_children, (list, LCE.DocumentFragment)):
            for node in new_children:
                if node.name == '#document' and node.temporary:
                    while node:
                        child = node[0]
                        del child.parent[child.index]
                        self.child.insert(index, child)
                        child.set_parent(self, index)
                        if index > 0:
                            child.set_prev(self.child[index-1])
                        try:
                            child.set_next(self.child[index+1])
                        except IndexError:
                            pass
                        self[index].index = index
                        index += 1
                else:
                    child = node
                    if child.parent is not None:
                        del child.parent[child.index]
                    self.child.insert(index, child)
                    child.set_parent(self, index)
                    if index > 0:
                        child.set_prev(self.child[index-1])
                    try:
                        child.set_next(self.child[index+1])
                    except IndexError:
                        pass
                    self[index].index = index
                    index += 1
        else:
            while new_children:
                child = new_children[0]
                del child.parent[child.index]
                self.child.insert(index, child)
                child.set_parent(self, index)
                if index > 0:
                    child.set_prev(self.child[index-1])
                try:
                    child.set_next(self.child[index+1])
                except IndexError:
                    pass
                self[index].index = index
                index += 1
        while index < len(self.child):
            self[index].index = index
            index += 1
        return self

    def append_child(self, new_child):
        """Adds the node new_child to the end of the list of children
        of this node. If the node is a `LCE.DocumentFragment` then it
        appends its child nodes. Returns the calling node. """
        if not isinstance(new_child, Node):
            new_child = LCE.Text(str(new_child))
        elif isinstance(new_child, LCE.DocumentFragment):
            msg = "Use extend_children for LCE.DocumentFragment Nodes."
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
        if isinstance(new_children, LCE.DocumentFragment):
            for i in xrange(len(new_children)):
                node = new_children[i]
                self.child.append(node)
                node.set_parent(self, len(self.child) - 1)
                try:
                    node.set_prev(self.child[-2])
                except IndexError:
                    pass
        elif isinstance(new_children, list):
            for node in new_children:
                self.append_child(node)
        else:
            while new_children:
                self.append_child(new_children[0])
        return self

    def normalize(self):
        """Removes empty Text nodes, and joins adjacent Text nodes."""
        if not self.child:
            return self
        crt = self.child[0]
        while crt is not None:
            if isinstance(crt, LCE.Text):
                if crt.data == '':
                    nextnode = crt.next
                    del crt.parent[crt.index]
                    crt = nextnode
                elif isinstance(crt.next, LCE.Text):
                    marked_node = crt.next
                    start = marked_node.index
                    while isinstance(marked_node, LCE.Text):
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

        When using a slice, the __getitem__ function will return a
        list with references to the requested nodes. """
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
        need to be contained in a `LCE.DocumentFragment` node. This
        function does not support insertion as the regular slice for
        list does. To insert use `insert_prev`."""
        indices = self._get_indices(index)
        if not isinstance(node, Node):
            raise TypeError("items must be Nodes")
        if node is self:
            raise TypeError("A node cannot have itself as a child.")
        if not isinstance(node, LCE.DocumentFragment):
            # Better take a look at this, DocFrag needs more development
            nodes = LCE.DocumentFragment(node)
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
        """Return a list of Nodes contained in the Node with the
        given name. """
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
