"""Selector

"""

from lexor.core import elements as core


class Selector(object):
    """JQuery like object. """

    def __init__(self, node):
        self.data = list()
        self.root = node

    def _get_direction(self, crt):
        """Returns the direction in which the traversal should go. """
        if crt.child:
            return 'd'
        return 'r'

    def find(self, exp):
        pass
        #direction = 'd'
        #crt = self.root
        #direction = self._get_direction(crt)
        #while True:
        #    if direction == 'd':
        #        pass

    def __iter__(self):
        for node in self.data:
            yield node
