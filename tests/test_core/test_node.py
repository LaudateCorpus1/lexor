""""
Testing each of the methods for `Node`.

"""
import sys
from nose.tools import eq_, ok_, assert_raises
from cStringIO import StringIO
LC = sys.modules['lexor.core']


def noop(*_):
    """No operation function, using this to wrap statements that are
    supposed to fail.
    """
    pass


def traverse_node(root, on_enter, on_exit, level=-1):
    """Utility function to traverse through a node and execute a
    function when the node is first encountered and on its last
    encounter. Each function takes in the node and the level
    on the tree. You may optionally state the starting level.
    """
    crt = root
    on_enter(crt, level)
    direction = 'd' if crt.child else 'r'
    loop = direction is 'd'
    if direction is 'r':
        on_exit(crt, level)
    while loop:
        if direction is 'd':
            level += 1
            crt = crt[0]
            on_enter(crt, level)
            direction = 'd' if crt.child else 'r'
            if direction is 'r':
                on_exit(crt, level)
        elif direction is 'r':
            if crt.next is None:
                direction = 'u'
            else:
                crt = crt.next
                on_enter(crt, level)
                direction = 'd' if crt.child else 'r'
        else:
            level -= 1
            on_exit(crt.parent, level)
            if crt.parent is root:
                loop = False
            elif crt.parent.next is None:
                crt = crt.parent
            else:
                crt = crt.parent.next
                on_enter(crt, level)
                direction = 'd' if crt.child else 'r'


def traverse_node_short(root, on_enter, on_exit, level=-1):
    """An nicer node traversal function. """
    crt = root
    loop = True
    while loop:
        on_enter(crt, level)
        if crt.child:
            level += 1
            crt = crt[0]
        else:
            on_exit(crt, level)
            while loop and crt.next is None:
                level -= 1
                crt = crt.parent
                on_exit(crt, level)
                if crt is root:
                    loop = False
            crt = crt.next


def traverse_node_rec(root, on_enter, on_exit, level=-1):
    """Similar to `traverse_node` but this time we do it recursively.
    """
    on_enter(root, level)
    for child in root:
        traverse_node(child, on_enter, on_exit, level+1)
    on_exit(root, level)


def test_node_name():
    """node.node_name is node.name"""
    node = LC.Element('tagname')
    eq_(node.node_name, 'tagname')
    eq_(node.node_name, node.name)


def test_owner_document():
    """node.owner_document is node.owner"""
    doc = LC.Document()
    node = LC.Element('tagname')
    doc.append_child(node)
    ok_(node.owner_document is doc, 'misplaced owner')
    ok_(node.owner is node.owner_document)


def test_parent_node():
    """node.parent_node is node.parent"""
    parent = LC.Element('parent')
    node = LC.Void('child')
    parent.append_child(node)
    ok_(node.parent_node is parent, 'misplaced parent')
    ok_(node.parent is node.parent_node)


def test_node_index():
    """node.node_index is node.index"""
    parent = LC.Element('parent')
    children = [
        LC.Element('item'),
        LC.Element('item'),
        LC.Element('item'),
    ]
    for child in children:
        parent.append_child(child)
    for index, child in enumerate(children):
        eq_(child.index, index)
        ok_(child.parent is parent, 'misplaced parent')
        ok_(child.parent[child.index] is child, 'wrong index')


def test_node_level():
    """node.node_level is node.level"""
    doc = LC.Document()
    doc.append_child(LC.Element('lvl0'))

    def add_node(parent):
        lvl = parent.level + 1
        for i in xrange(lvl):
            parent.append_child(LC.Element('lvl%d' % lvl))

    add_node(doc[0])
    for child in doc[0]:
        add_node(child)
        for sub in child:
            add_node(sub)

    def on_enter(crt, level):
        if not isinstance(crt, LC.Document):
            eq_(crt.name, 'lvl%d' % level)
        eq_(crt.level, level)
        eq_(crt.level, crt.node_level)

    on_exit = on_enter
    traverse_node(doc, on_enter, on_exit)


def test_element_index():
    """node.element_index"""
    root = LC.Element('root')
    root.append_child(LC.Void('void'))
    root.append_child(LC.Text('text'))
    root.append_child(LC.Text('text'))
    root.append_child(LC.Element('elem'))
    root.append_child(LC.ProcessingInstruction('python'))
    root.append_child(LC.Text('text'))
    root.append_child(LC.Element('last'))
    eq_(root[0].element_index, 0)
    eq_(root[1].element_index, 1)
    eq_(root[2].element_index, 1)
    eq_(root[3].element_index, 1)
    eq_(root[4].element_index, 2)
    eq_(root[5].element_index, 2)
    eq_(root[6].element_index, 2)


def test_first_child():
    """node.first_child"""
    root = LC.Element('root')
    child = LC.Element('empty')
    root.append_child(child)
    ok_(root.first_child is child)
    ok_(root.first_child is root[0])
    ok_(child.first_child is None)
    with assert_raises(IndexError):
        noop(child[0])


def test_previous_sibling():
    """node.previous_sibling"""
    root = LC.Element('root')
    root.append_child(LC.Element('tag1'))
    root.append_child(LC.Element('tag2'))
    root.append_child(LC.Element('tag3'))
    ok_(root[2].previous_sibling is root[1])
    ok_(root[2].prev is root[1])
    ok_(root[2].prev is root[2].parent_node[root[2].index - 1])
    ok_(root[1].prev is root[0])
    ok_(root[0].prev is None)


def test_next_sibling():
    """node.next_sibling"""
    root = LC.Element('root')
    root.append_child(LC.Element('tag1'))
    root.append_child(LC.Element('tag2'))
    root.append_child(LC.Element('tag3'))
    ok_(root[0].next_sibling is root[1])
    ok_(root[0].next is root[1])
    ok_(root[0].next is root[0].parent_node[root[0].index + 1])
    ok_(root[1].next is root[2])
    ok_(root[2].next is None)


def test_previous_element():
    """node.previous_element"""
    root = LC.Element('root')
    root.append_child(LC.Void('void'))
    root.append_child(LC.Text('text'))
    root.append_child(LC.Text('text'))
    root.append_child(LC.Element('elem'))
    root.append_child(LC.ProcessingInstruction('python'))
    root.append_child(LC.Text('text'))
    root.append_child(LC.Element('last'))
    ok_(root[0].previous_element is None)
    ok_(root[1].previous_element is root[0])
    ok_(root[2].previous_element is root[0])
    ok_(root[3].previous_element is root[0])
    ok_(root[4].previous_element is root[3])
    ok_(root[5].previous_element is root[3])
    ok_(root[6].previous_element is root[3])


def test_next_element():
    """node.next_element"""
    root = LC.Element('root')
    root.append_child(LC.Void('void'))
    root.append_child(LC.Text('text'))
    root.append_child(LC.Text('text'))
    root.append_child(LC.Element('elem'))
    root.append_child(LC.ProcessingInstruction('python'))
    root.append_child(LC.Text('text'))
    root.append_child(LC.Element('last'))
    ok_(root[0].next_element is root[3])
    ok_(root[1].next_element is root[3])
    ok_(root[2].next_element is root[3])
    ok_(root[3].next_element is root[6])
    ok_(root[4].next_element is root[6])
    ok_(root[5].next_element is root[6])
    ok_(root[6].next_element is None)


def test_remove_children():
    """node.remove_children()"""
    elements = [
        LC.Void('void'),
        LC.Text('text'),
        LC.Text('text'),
        LC.Element('elem'),
        LC.ProcessingInstruction('python'),
        LC.Text('text'),
        LC.Element('last'),
    ]
    root = LC.Element('root')
    for elem in elements:
        root.append_child(elem)
    eq_(len(root), 7)
    for child in root:
        ok_(child.parent is root)
        ok_(child is root[child.index])
    root.remove_children()
    eq_(len(root), 0)
    for elem in elements:
        ok_(elem.parent is None)
        ok_(elem.index is None)
        ok_(elem.prev is None)
        ok_(elem.next is None)


def test_repr():
    """repr(node)"""
    doc = LC.Document()
    doc.append_child(LC.Element('lvl0'))
    doc.append_child(LC.Element('lvl0'))

    def add_node(parent):
        lvl = parent.level + 1
        for i in xrange(lvl):
            parent.append_child(LC.Element('lvl%d' % lvl))

    add_node(doc[0])
    for child in doc[0]:
        add_node(child)
        for sub in child:
            add_node(sub)

    add_node(doc[1])
    for child in doc[1]:
        add_node(child)
        for sub in child:
            add_node(sub)

    repr_str = repr(doc)

    def on_enter(node, lvl):
        strf.write('%s%s' % ('    '*lvl, node.name))
        if not isinstance(node, LC.Element):
            strf.write('[0x%x]' % id(node))
        else:
            items = node.items()
            att = ' '.join(['%s="%s"' % (k, v) for k, v in items])
            strf.write('[0x%x' % id(node))
            if att != '':
                strf.write(' %s]' % att)
            else:
                strf.write(']')
        if node.name == '#document':
            info = ': (%s:%s:%s)'
            strf.write(info % (node.uri, node.lang, node.style))
        else:
            strf.write(':')
        if isinstance(node, LC.CharacterData):
            strf.write(' %r' % node.data)
        strf.write('\n')

    def on_exit(*_):
        pass

    strf = StringIO()
    traverse_node(doc, on_enter, on_exit)
    repr_new = strf.getvalue()

    eq_(repr_str, repr_new)

    strf = StringIO()
    traverse_node_short(doc, on_enter, on_exit)
    repr_new = strf.getvalue()

    eq_(repr_str, repr_new)

    strf = StringIO()
    traverse_node_rec(doc, on_enter, on_exit)
    repr_new = strf.getvalue()

    eq_(repr_str, repr_new)


def test_str():
    """str(node)"""
    # TODO: depends on a writing style which may not be available
    pass


def test_insert_before():
    """node.insert_before(index, new_child)"""
    root1 = LC.Element('root')
    for i in xrange(10):
        root1.append_child(LC.Element('child%d' % i))
    root2 = LC.Element('root')
    for i in xrange(10):
        root2.append_child(LC.Element('child%d' % i))
    fail = LC.DocumentFragment()
    # cannot insert a document fragment
    with assert_raises(TypeError):
        root1.insert_before(5, fail)
    for i in xrange(5):
        root1.insert_before(5, root2[0])
    order = [0, 1, 2, 3, 4, 4, 3, 2, 1, 0, 5, 6, 7, 8, 9]
    for i in xrange(15):
        eq_(root1[i].index, i)
        eq_(root1[i].name, 'child%d' % order[i])
    for i in xrange(5):
        eq_(root2[i].index, i)
        eq_(root2[i].name, 'child%d' % (i+5))


def test_extend_before_list():
    """node.extend_before(index, [n1, n2, n3, ...])"""
    root1 = LC.Element('root')
    for i in xrange(10):
        root1.append_child(LC.Element('child%d' % i))
    root2 = LC.Element('root')
    for i in xrange(10):
        root2.append_child(LC.Element('child%d' % i))

    root1.extend_before(5, root2[4::-1])

    order = [0, 1, 2, 3, 4, 4, 3, 2, 1, 0, 5, 6, 7, 8, 9]
    for i in xrange(15):
        eq_(root1[i].index, i)
        eq_(root1[i].name, 'child%d' % order[i])
    for i in xrange(5):
        eq_(root2[i].index, i)
        eq_(root2[i].name, 'child%d' % (i+5))


def test_extend_before_element():
    """node.extend_before(elem)"""
    root = LC.Element('root')
    for i in xrange(10):
        root.append_child(LC.Element('child%d' % i))
    host = LC.Element('host')
    host.append_child(LC.Element('child10'))

    host.extend_before(0, root)

    eq_(len(root), 0)
    for i in xrange(11):
        eq_(host[i].index, i)
        eq_(host[i].name, 'child%d' % i)


def test_extend_before_doc_frag():
    """node.extend_before(doc_frag)"""
    root = LC.DocumentFragment()
    for i in xrange(10):
        root.append_child(LC.Element('child%d' % i))

    host = LC.Element('host')
    host.append_child(LC.Element('child10'))

    host.extend_before(0, root)

    eq_(len(root), 0)
    for i in xrange(11):
        eq_(host[i].index, i)
        eq_(host[i].name, 'child%d' % i)


def test_extend_before_host_doc_frag():
    """doc_frag.extend_before(doc_frag)"""
    root = LC.DocumentFragment()
    for i in xrange(10):
        root.append_child(LC.Element('child%d' % i))

    host = LC.DocumentFragment()
    host.append_child(LC.Element('child10'))

    host.extend_before(0, root)

    eq_(len(root), 0)
    for i in xrange(11):
        eq_(host[i].index, i)
        eq_(host[i].name, 'child%d' % i)


def test_append_child():
    """node.append_child(node)"""
    parent = LC.Element('parent')
    child = LC.Void('void-child')
    parent.append_child(child)
    with assert_raises(AttributeError):
        child.append_child('this should fail because of void element')


def test_extend_children():
    """node.extend_children([n1, n2, ...])"""
    root1 = LC.Element('root')
    for i in xrange(10):
        root1.append_child(LC.Element('child%d' % i))
    root2 = LC.Element('root')
    for i in xrange(10):
        root2.append_child(LC.Element('child%d' % i))

    root1.extend_children(root2[4::-1])

    order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 4, 3, 2, 1, 0]
    for i in xrange(15):
        eq_(root1[i].index, i)
        eq_(root1[i].name, 'child%d' % order[i])
    for i in xrange(5):
        eq_(root2[i].index, i)
        eq_(root2[i].name, 'child%d' % (i+5))


def test_extend_children_element():
    """node.extend_children(elem)"""
    root = LC.Element('root')
    for i in xrange(10):
        root.append_child(LC.Element('child%d' % i))
    host = LC.Element('host')
    host.append_child(LC.Element('child10'))

    host.extend_children(root)

    eq_(len(root), 0)
    for i in xrange(1, 11):
        eq_(host[i].index, i)
        eq_(host[i].name, 'child%d' % (i-1))


def test_extend_children_doc_frag():
    """node.extend_children(doc_frag)"""
    root = LC.DocumentFragment()
    for i in xrange(10):
        root.append_child(LC.Element('child%d' % (i+1)))

    host = LC.Element('host')
    host.append_child(LC.Element('child0'))

    host.extend_children(root)

    eq_(len(root), 0)
    for i in xrange(11):
        eq_(host[i].index, i)
        eq_(host[i].name, 'child%d' % i)


def test_extend_children_host_doc_frag():
    """doc_frag.extend_children(doc_frag)"""
    root = LC.DocumentFragment()
    for i in xrange(10):
        root.append_child(LC.Element('child%d' % (i+1)))

    host = LC.DocumentFragment()
    host.append_child(LC.Element('child0'))

    host.extend_children(root)

    eq_(len(root), 0)
    for i in xrange(11):
        eq_(host[i].index, i)
        eq_(host[i].name, 'child%d' % i)
