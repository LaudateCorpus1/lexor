from nose.tools import eq_, ok_, assert_raises
from lexor.core import Parser


def test_init():
    """Parser(...)"""
    parser = Parser()
    eq_(parser.language, 'lexor')
    eq_(parser.parsing_style, 'default')


def test_change_language():
    """parser.language = 'new_lang'"""
    parser = Parser()
    eq_(parser._reload, True)
    parser._reload = False

    parser.language = 'lexor'
    eq_(parser._reload, False)

    parser.language = 'new_lang'
    eq_(parser._reload, True)


def test_change_style():
    """parser.parsing_style = 'new_style'"""
    parser = Parser()
    eq_(parser._reload, True)
    parser._reload = False

    parser.parsing_style = 'default'
    eq_(parser._reload, False)

    parser.parsing_style = 'new_style'
    eq_(parser._reload, True)


def test_change_defaults():
    """parser.options = {}"""
    parser = Parser()
    eq_(parser._reload, True)
    parser._reload = False

    opt = parser.options
    parser.options = opt
    eq_(parser._reload, False)

    opt = parser.options = {'arg': 'val'}
    eq_(parser._reload, True)
    eq_(opt['arg'], 'val')

    opt['arg'] = 'VAL'
    eq_(parser.options['arg'], 'VAL')


def test_set():
    """parser.set(lang, style, options)"""
    parser = Parser()
    eq_(parser._reload, True)
    parser._reload = False

    parser.set('new_lang', 'new_style', {'a': 'b'})
    eq_(parser._reload, True)
    eq_(parser.options['a'], 'b')
