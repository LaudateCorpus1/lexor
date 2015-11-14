from lexor.core import Converter, NodeConverter, zig
from lexor.core.elements import Element
from nose.tools import eq_, ok_, assert_raises


class NodeTrans(object):

    def __init__(self, name, **kwds):
        self.directive = name
        self.terminal = False
        self.priority = 0
        self.restrict = 'E'
        self.remove = False
        self.remove_children = False
        self.replace = False
        self.__dict__.update(kwds)


def test__parse_requirement():
    """zig._parse_requirement(...)"""
    parse = zig._parse_requirement
    eq_(parse('directive'), (False, 0, 'directive'))
    eq_(parse('$directive'), (True, 0, 'directive'))
    eq_(parse('^directive'), (False, -1, 'directive'))
    eq_(parse('^^directive'), (False, -2, 'directive'))
    eq_(parse('$^directive'), (True, -1, 'directive'))
    eq_(parse('$^^directive'), (True, -2, 'directive'))
    eq_(parse('^0directive'), (False, 0, 'directive'))
    eq_(parse('^1directive'), (False, 1, 'directive'))
    eq_(parse('^2directive'), (False, 2, 'directive'))
    eq_(parse('^3directive'), (False, 3, 'directive'))
    eq_(parse('^100directive'), (False, 100, 'directive'))
    eq_(parse('$^(0)directive'), (True, 0, 'directive'))
    eq_(parse('$^(1)directive'), (True, 1, 'directive'))
    eq_(parse('$^(2)directive'), (True, 2, 'directive'))
    eq_(parse('$^(3)directive'), (True, 3, 'directive'))
    eq_(parse('$^(100)directive'), (True, 100, 'directive'))

    eq_(parse('?$^100directive'), (False, 0, '?$^100directive'))
    eq_(parse('$^^^100directive'), (True, -2, '^100directive'))


def test_parse_requirement():
    """zig.parse_requirement(...)"""
    parse = zig.parse_requirement
    eq_(
        parse('directive|^other_directive'),
        [(False, 0, 'directive'), (False, -1, 'other_directive')]
    )
    eq_(
        parse('$^2directive|^100other_directive'),
        [(True, 2, 'directive'), (False, 100, 'other_directive')]
    )


def test_encode_requirement():
    """zig.encode_requirement(...)"""
    encode = zig._encode_requirement
    eq_(encode((False, 0, 'directive')), 'directive')
    eq_(encode((True, 0, 'directive')), '$directive')
    eq_(encode((False, -1, 'directive')), '^directive')
    eq_(encode((False, -2, 'directive')), '^^directive')
    eq_(encode((True, -1, 'directive')), '$^directive')
    eq_(encode((True, -2, 'directive')), '$^^directive')
    eq_(encode((False, 1, 'directive')), '^(1)directive')
    eq_(encode((False, 2, 'directive')), '^(2)directive')
    eq_(encode((False, 3, 'directive')), '^(3)directive')
    eq_(encode((False, 100, 'directive')), '^(100)directive')
    eq_(
        zig.encode_requirement(
            [(False, 100, 'directive'), (False, 1, 'directive')],
        ),
        '^(100)directive|^(1)directive'
    )


def test_get_requirement():
    """Zig.get_requirement(node, req)"""
    trans = Converter()
    root = Element('lvl0').append_child(
        Element('lvl1').append_child(
            Element('lvl2').append_child(
                Element('lvl3')
            )
        )
    )
    zig.Zig(trans, root)
    root.zig.directives = [
        ('l0-1', 0), ('l0-2', 0), ('l0-3', 0), ('other', 0)
    ]
    zig.Zig(trans, root[0])
    root[0].zig.directives = [
        ('l1-1', 0), ('l1-2', 0), ('l1-3', 0)
    ]
    zig.Zig(trans, root[0][0])
    root[0][0].zig.directives = [
        ('l2-1', 0), ('l2-2', 0)
    ]
    zig.Zig(trans, root[0][0][0])
    root[0][0][0].zig.directives = [
        ('l3-1', 0), ('l3-2', 0), ('other', 0)
    ]
    node = root[0][0][0]

    eq_(node.name, 'lvl3')
    eq_(node.zig.get_requirement('l3-1'), ('l3-1', node))
    eq_(node.zig.get_requirement('^other'), ('other', node))
    eq_(node.zig.get_requirement('^^other'), ('other', root))
    eq_(node.zig.get_requirement('gone|other'), ('other', node))
    eq_(node.zig.get_requirement('^1l2-2'), ('l2-2', root[0][0]))
    eq_(node.zig.get_requirement('^3l0-2'), ('l0-2', root))
    eq_(node.zig.get_requirement('$^2l0-2'), ('l0-2', None))
    eq_(node.zig.get_requirement('^2l1-2'), ('l1-2', root[0]))
    eq_(node.zig.get_requirement('^1l2-2'), ('l2-2', node.parent))
    eq_(node.zig.get_requirement('^(1)l2-2'), ('l2-2', root[0][0]))
    eq_(node.zig.get_requirement('^(3)l0-2'), ('l0-2', root))
    eq_(node.zig.get_requirement('$^(2)l0-2'), ('l0-2', None))
    eq_(node.zig.get_requirement('^(2)l1-2'), ('l1-2', root[0]))
    eq_(node.zig.get_requirement('^(1)l2-2'), ('l2-2', node.parent))


def test_get_directives():
    """Zig.get_directives()"""
    trans = Converter()
    trans._directives = {
        'e1': NodeTrans('e1', restrict='E'),
        'e2': NodeTrans('e2', restrict='E'),
        'a1': NodeTrans('a1', restrict='A', priority=1),
        'a2': NodeTrans('a2', restrict='A', terminal=True),
        'a3': NodeTrans('a3', restrict='A', priority=3),
        'c1': NodeTrans('c1', restrict='C', priority=1),
        'c2': NodeTrans('c2', restrict='C', terminal=True),
        'c3': NodeTrans('c3', restrict='C', priority=3),
    }

    node = Element('e1')
    zig.Zig(trans, node)
    node.zig.get_directives()
    eq_(node.zig.directives, [('e1', 0)])

    node = Element('e2')
    node['a1'] = 'a1'
    node['class'] = 'class1 c1 c3'
    zig.Zig(trans, node)
    node.zig.get_directives()
    eq_(
        node.zig.directives,
        [('c3', 3), ('a1', 1), ('c1', 1), ('e2', 0)]
    )

    node = Element('e2')
    node['a2'] = 'a2'
    node['class'] = 'class1 c1 c3'
    zig.Zig(trans, node)
    node.zig.get_directives()
    eq_(
        node.zig.directives,
        [('e2', 0), ('a2', 0)]
    )
