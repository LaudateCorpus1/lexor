from lexor.core import Converter, NodeConverter


class RemoveNC(NodeConverter):
    directive = 'tmp'
    remove = True


class NC1(NodeConverter):
    directive = 'nc1'
    restrict = 'EA'


class NC2(NodeConverter):
    directive = 'nc2'
    restrict = 'EA'


class NC3(NodeConverter):
    directive = 'nc3'
    restrict = 'EA'


def test_1():
    """should capture element requirement in """
    converter = Converter()
    converter._nc = {
        ''
    }
