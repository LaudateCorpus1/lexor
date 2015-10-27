from lexor.core import Converter, NodeConverter
from lexor.core.elements import Element
from nose.tools import eq_, ok_, assert_raises


def test_init():
    """Converter(...)"""
    cvr = Converter()
    eq_(cvr.convert_from, 'lexor')
    eq_(cvr.convert_to, 'html')
    eq_(cvr.parser.language, 'lexor')


def test_change_convert_to():
    """converter.convert_to = 'new_lang'"""
    cvr = Converter()
    eq_(cvr._reload, True)
    cvr._reload = False

    cvr.convert_to = 'html'
    eq_(cvr._reload, False)

    cvr.convert_to = 'new_lang'
    eq_(cvr._reload, True)


def test_change_convert_from():
    """converter.convert_from = 'new_lang'"""
    cvr = Converter()
    eq_(cvr._reload, True)
    cvr._reload = False

    cvr.convert_from = 'lexor'
    eq_(cvr._reload, False)

    cvr.convert_from = 'new_lang'
    eq_(cvr._reload, True)


def test_change_style():
    """converter.converting_style = 'new_style'"""
    cvr = Converter()
    eq_(cvr._reload, True)
    cvr._reload = False

    cvr.converting_style = 'default'
    eq_(cvr._reload, False)

    cvr.converting_style = 'new_style'
    eq_(cvr._reload, True)


def test_change_defaults():
    """converter.options = {}"""
    cvr = Converter()
    eq_(cvr._reload, True)
    cvr._reload = False

    opt = cvr.options
    cvr.options = opt
    eq_(cvr._reload, False)

    opt = cvr.options = {'arg': 'val'}
    eq_(cvr._reload, True)
    eq_(opt['arg'], 'val')

    opt['arg'] = 'VAL'
    eq_(cvr.options['arg'], 'VAL')


def test_set():
    """converter.set(lang, style, options)"""
    cvr = Converter()
    eq_(cvr._reload, True)
    cvr._reload = False

    cvr.set('from_lang', 'to_lang', 'new_style', {'a': 'b'})
    eq_(cvr._reload, True)
    eq_(cvr.options['a'], 'b')
    eq_(cvr.parser.language, 'from_lang')


def test__parse_requirement():
    """converter._parse_requirement(...)"""
    parse = Converter._parse_requirement
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
    """converter.parse_requirement(...)"""
    parse = Converter.parse_requirement
    eq_(
        parse('directive|^other_directive'),
        [(False, 0, 'directive'), (False, -1, 'other_directive')]
    )
    eq_(
        parse('$^2directive|^100other_directive'),
        [(True, 2, 'directive'), (False, 100, 'other_directive')]
    )


def test_get_requirement():
    """converter.get_requirement(node, req)"""
    get_req = Converter.get_requirement
    root = Element('lvl0').append_child(
        Element('lvl1').append_child(
            Element('lvl2').append_child(
                Element('lvl3')
            )
        )
    )
    root.__directives__ = [
        ('l0-1', 0), ('l0-2', 0), ('l0-3', 0), ('other', 0)
    ]
    root[0].__directives__ = [
        ('l1-1', 0), ('l1-2', 0), ('l1-3', 0)
    ]
    root[0][0].__directives__ = [
        ('l2-1', 0), ('l2-2', 0)
    ]
    root[0][0][0].__directives__ = [
        ('l3-1', 0), ('l3-2', 0), ('other', 0)
    ]
    node = root[0][0][0]

    eq_(node.name, 'lvl3')
    eq_(get_req(node, 'l3-1'), ('l3-1', node))
    eq_(get_req(node, '^other'), ('other', node))
    eq_(get_req(node, '^^other'), ('other', root))
    eq_(get_req(node, 'gone|other'), ('other', node))
    eq_(get_req(node, '^1l2-2'), ('l2-2', root[0][0]))
    eq_(get_req(node, '^3l0-2'), ('l0-2', root))
    eq_(get_req(node, '$^2l0-2'), ('l0-2', None))
    eq_(get_req(node, '^2l1-2'), ('l1-2', root[0]))
    eq_(get_req(node, '^1l2-2'), ('l2-2', node.parent))
    eq_(get_req(node, '^(1)l2-2'), ('l2-2', root[0][0]))
    eq_(get_req(node, '^(3)l0-2'), ('l0-2', root))
    eq_(get_req(node, '$^(2)l0-2'), ('l0-2', None))
    eq_(get_req(node, '^(2)l1-2'), ('l1-2', root[0]))
    eq_(get_req(node, '^(1)l2-2'), ('l2-2', node.parent))


def test_encode_requirement():
    """converter.encode_requirement(...)"""
    encode = Converter._encode_requirement
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
        Converter.encode_requirement(
            [(False, 100, 'directive'), (False, 1, 'directive')],
        ),
        '^(100)directive|^(1)directive'
    )
