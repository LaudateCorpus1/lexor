from lexor.core import Converter, NodeConverter
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
    """parser.set(lang, style, options)"""
    cvr = Converter()
    eq_(cvr._reload, True)
    cvr._reload = False

    cvr.set('from_lang', 'to_lang', 'new_style', {'a': 'b'})
    eq_(cvr._reload, True)
    eq_(cvr.options['a'], 'b')
    eq_(cvr.parser.language, 'from_lang')
