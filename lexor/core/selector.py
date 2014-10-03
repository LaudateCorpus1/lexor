"""
This module is trying to simulate jquery selectors. If some code
looks similar to that of the Sizzle CSS Selector engine it is because
the ideas were taken from it.

In short, credit goes to Sizzle_ and CSS for the selector idea.

.. warning::

    This module is far from complete. Some of the functions specified
    here lack functionality.

.. _Sizzle: http://sizzlejs.com/

"""

import re
import sys
import types
from datetime import datetime
from time import mktime
LC = sys.modules['lexor.core']


def get_date():
    """Obtain an integer representation of the date. """
    date = datetime.utcnow()
    return int(mktime(date.timetuple()))


def mark_function(fnc):
    """Mark a function for special use by Sizzle. """
    fnc.expando = True
    return fnc


BOOLEANS = "checked|selected|async|autofocus|autoplay|controls|" + \
           "defer|disabled|hidden|ismap|loop|multiple|open|" + \
           "readonly|required|scoped"
WHITESPACE = "[\\x20\\t\\r\\n\\f]"
CHAR_ENCODING = "(?:\\\\.|[\\w-]|[^\\x00-\\xa0])+"
IDENTIFIER = CHAR_ENCODING.replace("w", "w#")
ATTRIBUTES = "\\[" + WHITESPACE + "*(" + CHAR_ENCODING + ")" + \
             WHITESPACE + "*(?:([*^$|!~]?=)" + WHITESPACE + \
             "*(?:(['\"])((?:\\\\.|[^\\\\])*?)\\3|(" + \
             IDENTIFIER + ")|)|)" + WHITESPACE + "*\\]"
PSEUDOS = ":(" + CHAR_ENCODING + \
          ")(?:\\(((['\"])((?:\\\\.|[^\\\\])*?)\\3|((?:\\\\.|" + \
          "[^\\\\()[\\]]|" + ATTRIBUTES.replace("3", "8") + \
          ")*)|.*)\\)|)"
RCOMMA = re.compile("^" + WHITESPACE + "*," + WHITESPACE + "*")
RCOMBINATORS = re.compile("^" + WHITESPACE + "*([>+~]|" +
                          WHITESPACE + ")" + WHITESPACE + "*")
# Use .findall instead of search or match since this regex had the
# global attribute
RATTRIBUTEQUOTE = re.compile("=" + WHITESPACE + "*([^\\]'\"]*?)" +
                             WHITESPACE + "*\\]")
RPSEUDO = re.compile(PSEUDOS)
RIDENTIFIER = re.compile("^" + IDENTIFIER + "$")
MATCH_EXPR = {
    "ID": re.compile("^#(" + CHAR_ENCODING + ")"),
    "CLASS": re.compile("^\\.(" + CHAR_ENCODING + ")"),
    "TAG": re.compile("^(" + CHAR_ENCODING.replace("w", "w*") + ")"),
    "ATTR": re.compile("^" + ATTRIBUTES),
    "PSEUDO": re.compile("^" + PSEUDOS),
    "CHILD": re.compile("^:(only|first|last|nth|nth-last)-" +
                        "(child|of-type)(?:\\(" + WHITESPACE +
                        "*(even|odd|(([+-]|)(\\d*)n|)" + WHITESPACE +
                        "*(?:([+-]|)" + WHITESPACE + "*(\\d+)|))" +
                        WHITESPACE + "*\\)|)", re.IGNORECASE),
    "bool": re.compile("^(?:" + BOOLEANS + ")$", re.IGNORECASE),
    # For use in libraries implementing .is()
    # We use this for POS matching in `select`
    "needsContext": re.compile("^" + WHITESPACE +
                               "*[>+~]|:(even|odd|eq|gt|lt|nth|" +
                               "first|last)(?:\\(" + WHITESPACE +
                               "*((?:-\\d)?\\d*)" + WHITESPACE +
                               "*\\)|)(?=[^-]|$)", re.IGNORECASE),
}
RQUICKEXPR = re.compile(r'^(?:#([\w-]+)|(\w+)|\.([\w-]+))$')
RUNESCAPE = re.compile("\\\\([\\da-f]{1,6}" + WHITESPACE + "?|(" +
                       WHITESPACE + ")|.)", re.IGNORECASE)
EXPANDO = 'sizzle'+str(get_date())


def _pre_filter_attr(match):
    """function for EXPR['pre_filter']['ATTR']"""
    # match[0] = match[0].replace(runescape, funescape);
    # match[0] = re.sub(runescape, funescape, match[0])
    # Move the given value to match[3] whether quoted or unquoted
    match[2] = match[3] or match[4] or ""
    # match[2] = match[2].replace(runescape, funescape);
    if match[1] == "~=":
        match[2] = " " + match[2] + " "
    return match[:4]


def _pre_filter_child(match):
    """function for EXPR['pre_filter']['CHILD']"""
    match[0] = match[0].lower()
    if match[0].slice[:3] == "nth":
        # nth-* requires argument
        if not match[2]:
            print 'ERROR'
            sys.exit(2)
            # Should raise an error showing match[0]
        # numeric x and y parameters for Expr.filter.CHILD
        # remember that false/true cast respectively to 0/1
        # ML: Possible +=
        if match[4]:
            match[4] = match[5] + (match[6] or 1)
        else:
            match[4] = 2*(match[3] == "even" or match[3] == "odd")
        match[5] = ((match[7] + match[8]) or match[3] == "odd")
    # other types prohibit arguments
    elif match[3]:
        print 'ERROR'
        sys.exit(2)
    return match


def _filter_tag(node_name_selector):
    name = node_name_selector
    if node_name_selector == '*':
        return lambda: True
    else:
        return lambda elem: elem and elem.name.lower() == name


def _filter_class(class_name):
    try:
        pattern = _filter_class.cache[class_name]
        return pattern
    except KeyError:
        pass
    pattern = re.compile("(^|" + WHITESPACE + ")" + class_name + "(" + WHITESPACE + "|$)")
    _filter_class.cache[class_name] = lambda elem: pattern.search(elem['class']) if 'class' in elem else None
    return _filter_class.cache[class_name]
_filter_class.cache = dict()

EXPR = {
    'create_pseudo': mark_function,
    'match': MATCH_EXPR,
    'attr_handle': {},
    'find': {},
    'relative': {
        '>': {'dir': "parent_node", 'first': True},
        ' ': {'dir': "parent_node"},
        '+': {'dir': "previous_sibling", 'first': True},
        '~': {'dir': "previous_sibling"}
    },
    'pre_filter': {
        'ATTR': _pre_filter_attr,
        'CHILD': _pre_filter_child,
    },
    'filter': {
        'TAG': _filter_tag,
        'CLASS': _filter_class,
    }
}


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


def sizzle(selector, context, results=None, seed=None):
    """Function shamelessly borrowed and partially translated to
    python from http://sizzlejs.com/. """
    if results is None:
        results = list()
    if not selector or not isinstance(selector, str):
        return results
    if not isinstance(context, LC.Element):
        return list()
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
        elif isinstance(context, LC.Element):  # sizzle('.CLASS')
            results.extend(context.get_elements_by_class_name(match[2]))
        return results
    return select(selector.strip(), context, results, seed)


def select(selector, context, results, seed):
    """A low-level selection function that works with Sizzle's
    compiled selector functions

    :``selector``: A selector or a pre-compiled selector function
        built with ``Sizzle.compile``
    :``context``: An :class:`lexor.core.elements.Element` object.
    :``results``: A ``list``.
    :``seed``: A ``list`` of elements to match against.
    """
    # compiled = typeof selector === "function" && selector
    # selector = compiled.selector or selector
    match = not seed and tokenize(selector)
    results = results or list()
    if len(match) == 1:
        # Other complicated stuff
        pass
    compile_selector(selector, match)(seed, context, results)
    return results


def matcher_from_tokens(tokens):
    """
    .. warning::

        Missing documentation.
    """
    pass


def matcher_from_group_matchers(element_matchers, set_matchers):
    """
    .. warning::

        Missing documentation.
    """
    pass


def compile_selector(selector, match=None):
    """
    .. warning::

        Missing documentation.
    """
    try:
        return compile_selector.cache[selector]
    except KeyError:
        pass
    set_matchers = list()
    element_matchers = list()
    if match is None:
        match = tokenize(selector)
    i = len(match) - 1
    while i:
        cached = matcher_from_tokens(match[i])
        if cached[EXPANDO]:
            set_matchers.append(cached)
        else:
            element_matchers.append(cached)
    cached = matcher_from_group_matchers(element_matchers, set_matchers)
    compile_selector.cache[selector] = cached
    # cached.selector = selector
    return cached
compile_selector.cache = dict()


def tokenize(selector, parse_only=False):
    """
    .. warning::

        Missing documentation.
    """
    try:
        cached = tokenize.cache[selector]
    except KeyError:
        pass
    else:
        return 0 if parse_only else cached
    so_far = selector
    groups = list()
    pre_filters = EXPR['pre_filter']
    matched = False
    while so_far:
        match = RCOMMA.match(so_far)
        if not matched or match:
            if match:
                match = match.groups()
                so_far = so_far[len(match[0]):] or so_far
            tokens = list()
            groups.append(tokens)
        matched = False
        match = RCOMBINATORS.match(so_far)
        if match:
            matched = match.group(0)
            match = list(match.groups())
            tokens.append({
                'value': matched,
                'type': match[0].strip(),
            })
            so_far = so_far[len(matched):]
        for ftype in EXPR['filter']:
            match = MATCH_EXPR[ftype].match(so_far)
            if match:
                matched = match.group(0)
                match = list(match.groups())
                # match = pre_filters[ftype](match).groups()
                tokens.append({
                    'value': matched,
                    'type': ftype,
                    'matches': match,
                })
                so_far = so_far[len(matched):]
        if not matched:
            break
    if parse_only:
        return len(so_far)
    else:
        tokenize.cache[selector] = groups
        return tokenize.cache[selector]
if not hasattr(tokenize, 'cache'):
    tokenize.cache = dict()


class Selector(object):
    """JQuery like object. """

    def __init__(self, selector, node, results=None):
        self.data = sizzle(selector, node, results)

    def __getitem__(self, k):
        """Return the `k`-th element selected.

        >>> x.__getitem__(k) <==> x[k]

        """
        return self.data[k]

    def __repr__(self):
        """
        >>> x.__repr__() == repr(x)
        True

        """
        result = '\n----------\n'
        for node in self.data:
            result += repr(node)
            result += '\n----------\n'
        return result

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
    def _append(node, content, parser):
        """Helper function to `append` method. """
        if isinstance(content, Selector):
            node.extend_children(content.data)
        elif isinstance(content, LC.Node):
            if (content.name in ['#document', '#document-fragment']
                    and content.temporary):
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
        parser = LC.Parser(info['lang'], info['style'], info['defaults'])
        if len(arg) == 1 and isinstance(arg[0], types.FunctionType):
            for num, node in enumerate(self.data):
                self._append(node, arg[0](node, num), parser)
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
                    self._append(self.data[i], clone, parser)
                if self.data:
                    self._append(self.data[-1], content, parser)

    @staticmethod
    def _prepend(node, content, parser):
        """Helper function to `prepend` method. """
        if isinstance(content, Selector):
            node.extend_before(0, content.data)
        elif isinstance(content, LC.Node):
            if (content.name in ['#document', '#document-fragment']
                    and content.temporary):
                node.extend_before(0, content)
            else:
                node.insert_before(0, content)
        elif hasattr(content, '__iter__'):
            node.extend_before(0, content)
        else:
            parser.parse(str(content))
            node.extend_before(0, parser.doc)

    def prepend(self, *arg, **keywords):
        """Insert content, specified by the parameter, to the
        beginning of each element in the set of matched elements.

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
        parser = LC.Parser(info['lang'], info['style'], info['defaults'])
        if len(arg) == 1 and isinstance(arg[0], types.FunctionType):
            for num, node in enumerate(self.data):
                self._prepend(node, arg[0](node, num), parser)
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
                    self._prepend(self.data[i], clone, parser)
                if self.data:
                    self._prepend(self.data[-1], content, parser)

    @staticmethod
    def _after(node, content, parser):
        """Helper function to `after` method. """
        if isinstance(content, Selector):
            node.append_nodes_after(content.data)
        elif isinstance(content, LC.Node):
            if content.name in ['#document', '#document-fragment']:
                node.append_nodes_after(content)
            else:
                node.append_after(content)
        elif hasattr(content, '__iter__'):
            node.append_nodes_after(content)
        else:
            parser.parse(str(content))
            node.append_nodes_after(parser.doc)

    def after(self, *arg, **keywords):
        """Insert content, specified by the parameter, after each
        element in the set of matched elements.

        .. code::

            .after(content [,content])

        :param content:
            html string or Element or Array or jQuery string, Node,
            array of Node, or Selector object to insert after each
            element in the set of matched elements.

        :param content:
            html string or Element or Array or jQuery One or more
            additional DOM elements, arrays of elements, HTML
            strings, or jQuery objects to insert after each element
            in the set of matched elements.

        .. code::

            .after(function(node, index))

        :param function(node,index):
            A function that returns a string, DOM element(s), or
            Selector object to insert after each element in the set
            of matched elements. Receives the element in the set and
            its index position in the set as its arguments.

        .. code::

            .after(..., lang='html', style='default', 'defaults'=None)

        :param lang:
            The language in which strings will be parsed in.

        :param style:
            The style in which strings will be parsed in.

        :param defaults:
            A dictionary with string keywords and values specifying
            options for the particular style.
        """
        info = {
            'lang': 'html',
            'style': 'default',
            'defaults': None,
        }
        for key in keywords:
            info[key] = keywords[key]
        parser = LC.Parser(info['lang'], info['style'], info['defaults'])
        if len(arg) == 1 and isinstance(arg[0], types.FunctionType):
            for num, node in enumerate(self.data):
                self._after(node, arg[0](node, num), parser)
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
                    self._after(self.data[i], clone, parser)
                if self.data:
                    self._after(self.data[-1], content, parser)

    @staticmethod
    def _before(node, content, parser):
        """Helper function to `after` method. """
        if isinstance(content, Selector):
            node.prepend_nodes_before(content.data)
        elif isinstance(content, LC.Node):
            if content.name in ['#document', '#document-fragment']:
                node.prepend_nodes_before(content)
            else:
                node.prepend_before(content)
        elif hasattr(content, '__iter__'):
            node.prepend_nodes_before(content)
        else:
            parser.parse(str(content))
            node.prepend_nodes_before(parser.doc)

    def before(self, *arg, **keywords):
        """Insert content, specified by the parameter, before each
        element in the set of matched elements.

        .. code::

            .before(content [,content])

        :param content:
            html string or Element or Array or jQuery string, Node,
            array of Node, or Selector object to insert before each
            element in the set of matched elements.

        :param content:
            html string or Element or Array or jQuery One or more
            additional DOM elements, arrays of elements, HTML
            strings, or jQuery objects to insert before each element
            in the set of matched elements.

        .. code::

            .before(function(node, index))

        :param function(node,index):
            A function that returns a string, DOM element(s), or
            Selector object to insert before each element in the set
            of matched elements. Receives the element in the set and
            its index position in the set as its arguments.

        .. code::

            .before(..., lang='html', style='default', 'defaults'=None)

        :param lang:
            The language in which strings will be parsed in.

        :param style:
            The style in which strings will be parsed in.

        :param defaults:
            A dictionary with string keywords and values specifying
            options for the particular style.
        """
        info = {
            'lang': 'html',
            'style': 'default',
            'defaults': None,
        }
        for key in keywords:
            info[key] = keywords[key]
        parser = LC.Parser(info['lang'], info['style'], info['defaults'])
        if len(arg) == 1 and isinstance(arg[0], types.FunctionType):
            for num, node in enumerate(self.data):
                self._before(node, arg[0](node, num), parser)
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
                    self._before(self.data[i], clone, parser)
                if self.data:
                    self._before(self.data[-1], content, parser)

    def __iter__(self):
        """Iterate over the elements of the selector. """
        for node in self.data:
            yield node

    def __len__(self):
        """Return the number of elements.

        >>> x.__len__() == len(x)
        True

        """
        return len(self.data)
