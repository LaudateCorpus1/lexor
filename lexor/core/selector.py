"""Selector

This module is trying to simulate jquery selectors. If some code
looks similar to that of the Sizzle CSS Selector engine it is because
the ideas were taken from it.

In short, credit goes to [Sizzle][1] and CSS for the seletor idea.

[1]: http://sizzlejs.com/

"""

import re
import sys
CORE = sys.modules['lexor.core.elements']
RQUICKEXPR = re.compile(r'^(?:#([\w-]+)|(\w+)|\.([\w-]+))$')


def sizzle(selector, context, results=None):
    """Function shamelessly borrowed and partially translated to
    python from http://sizzlejs.com/. """
    if results is None:
        results = list()
    match = RQUICKEXPR.match(selector)
    if match is not None:  # Shortcuts
        match = match.groups()
        element_id = match[0]
        if element_id:  # sizzle('#ID')
            if context.name == '#document':
                elem = context.get_element_by_id(element_id)
                if elem:
                    results.append(elem)
            elif context.owner:
                elem = context.owner.get_element_by_id(element_id)
                if elem in context:
                    results.append(elem)
        elif match[1]:  # sizzle('TAG')
            results.extend(context.get_nodes_by_name(selector))
        elif isinstance(context, CORE.Element):  # sizzle('.CLASS')
            results.extend(context.get_elements_by_class_name(match[2]))
        return results
    raise NotImplementedError


class Selector(object):
    """JQuery like object. """

    def __init__(self, selector, node, results=None):
        self.data = sizzle(selector, node, results)

    def __getitem__(self, k):
        """Return the k-th element selected.

            x.__getitem__(k) <==> x[k]

        """
        return self.data[k]

    def find(self, selector):
        """Get the descendants of each element in the current set of
        matched elements, filtered by a selector. """
        current = self.data
        self.data = list()
        for node in current:
            sizzle(selector, node, self.data)
        return self

    def contents(self):
        """Get the children of each element in the set of matched
        elements, including text and comment nodes."""
        current = self.data
        self.data = list()
        for node in current:
            if node:
                self.data.extend(node.child)
        return self

    def __iter__(self):
        for node in self.data:
            yield node
