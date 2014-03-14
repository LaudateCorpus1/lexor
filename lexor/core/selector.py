"""Selector

This module is trying to simulate jquery selectors. If some code
looks similar to that of the Sizzle CSS Selector engine it is because
the ideas were taken from it.

In short, credit goes to [Sizzle][1] and CSS for the seletor idea.

[1]: http://sizzlejs.com/

"""

import re
import sys
import types
PMOD = sys.modules['lexor.core.parser']
CORE = sys.modules['lexor.core.elements']
RQUICKEXPR = re.compile(r'^(?:#([\w-]+)|(\w+)|\.([\w-]+))$')


def clone_obj(obj, parser):
    """Utility function to create deep copies of objects used for the
    Selector object. A parser should be given in case the object is a
    string. """
    try:
        return obj.clone_node(True)
    except AttributeError:
        pass
    if hasattr(obj, '__iter__'):
        return [clone_obj(ele, parser) for ele in obj]
    parser.parse(str(obj))
    return parser.doc


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
                if elem and context.contains(elem):
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

    @staticmethod
    def _append_to(node, content, parser):
        """Helper function to append to a node. """
        if isinstance(content, Selector):
            node.extend_children(content.data)
        elif isinstance(content, CORE.Node):
            if content.name in ['#document', '#document-fragment']:
                node.extend_children(content)
            else:
                node.append_child(content)
        elif hasattr(content, '__iter__'):
            node.extend_children(content)
        else:
            parser.parse(str(content))
            node.extend_children(parser.doc)

    def append(self, *arg, **keywords):
        """Insert content, specified by the parameter, to the end of
        each element in the set of matched elements.

        Should behave similarly as https://api.jquery.com/append/.
        Major difference is in the function. When passing a function
        it should take 2 parameters: node, index. Where node will be
        the current element to which the return value will be
        appended to. """
        info = {
            'lang': 'html',
            'style': 'default',
            'defaults': None,
        }
        for key in keywords:
            info[key] = keywords[key]
        parser = PMOD.Parser(info['lang'], info['style'], info['defaults'])
        if len(arg) == 1 and isinstance(arg[0], types.FunctionType):
            for num, node in enumerate(self.data):
                self._append_to(node, arg[0](node, num), parser)
        else:
            for content in arg:
                if isinstance(content, str):
                    parser.parse(content)
                    content = parser.doc
                elif isinstance(content, list):
                    for num in xrange(len(content)):
                        if isinstance(content[num], str):
                            parser.parse(content[num])
                            content[num] = parser.doc
                for i in xrange(len(self.data) - 1):
                    clone = clone_obj(content, parser)
                    self._append_to(self.data[i], clone, parser)
                if self.data:
                    self._append_to(self.data[-1], content, parser)

    @staticmethod
    def _prepend_to(node, content, parser):
        """Helper function to append to a node. """
        if isinstance(content, Selector):
            node.extend_before(0, content.data)
        elif isinstance(content, CORE.Node):
            if content.name in ['#document', '#document-fragment']:
                node.extend_before(0, content)
            else:
                node.insert_before(0, content)
        elif hasattr(content, '__iter__'):
            print 'CONTENT = %r' % content
            node.extend_before(0, content)
        else:
            parser.parse(str(content))
            node.extend_before(0, parser.doc)

    def prepend(self, *arg, **keywords):
        """Insert content, specified by the parameter, to the
        beginning of each element in the setof matched elements.

        Should behave similarly as https://api.jquery.com/append/.
        Major difference is in the function. When passing a function
        it should take 2 parameters: node, index. Where node will be
        the current element to which the return value will be
        appended to. """
        info = {
            'lang': 'html',
            'style': 'default',
            'defaults': None,
        }
        for key in keywords:
            info[key] = keywords[key]
        parser = PMOD.Parser(info['lang'], info['style'], info['defaults'])
        if len(arg) == 1 and isinstance(arg[0], types.FunctionType):
            for num, node in enumerate(self.data):
                self._prepend_to(node, arg[0](node, num), parser)
        else:
            for content in arg:
                if isinstance(content, str):
                    parser.parse(content)
                    content = parser.doc
                elif isinstance(content, list):
                    for num in xrange(len(content)):
                        if isinstance(content[num], str):
                            parser.parse(content[num])
                            content[num] = parser.doc
                for i in xrange(len(self.data) - 1):
                    clone = clone_obj(content, parser)
                    self._prepend_to(self.data[i], clone, parser)
                if self.data:
                    self._prepend_to(self.data[-1], content, parser)

    def __iter__(self):
        for node in self.data:
            yield node

    def __len__(self):
        """Return the number of elements.

            x.__len__() <==> len(x)

        """
        return len(self.data)
