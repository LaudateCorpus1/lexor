"""Parser Module

Provides the `Parser` object which defines the basic mechanism for
parsing character sequences. This involves using objects derived from
the abstract class `NodeParser`.

"""

import re
import sys
from lexor.command import config
from lexor.command.lang import get_style_module, map_explanations
LC = sys.modules['lexor.core']


class NodeParser(object):
    """An object that has two methods: `makeNode` and `close`. The
    first method is required to be overloaded in derived objects."""

    def __init__(self, parser):
        """A `NodeParser` needs to be initialized with a `Parser`
        object. If this method is to be overloaded then make sure
        that it only accepts one parameter: `parser`. This method is
        used by `Parser` and it calls it with itself as the parameter.

        """
        self.parser = parser

    def make_node(self):
        """This method is required to be overloaded by the derived
        node parser. It returns `None` if the node parser will not be
        able to create a node from the current information in the
        parser. Otherwise it creates a `Node` object and returns it.

        When returning a node you have the option of informing the
        parser if the node is complete or not. For instance, if your
        node parser creates an Element and it does not have any
        children to be parsed then return a list containing only the
        single node. This will tell the parser that the node has been
        closed and it will not call the `close` method of the node
        parser. If the `Node` does not have a child, say
        `ProcessingInstruction`, `RawText`, or `Void` then there is
        no need to wrap the node in a list.

        The `Node` object that this method returns also needs
        to have the property `pos`. This is a list of two integers
        stating the line and column number where the node was
        encountered in the text that is being parsed. This property
        will be removed by the parser once the parser finishes all
        processing with the node.

        If this method is not overloaded as previously stated then
        a `NotImplementedError` exception will be raised.

        """
        msg = '%s did not implement `make_node`' % self.__class__
        raise NotImplementedError(msg)

    def close(self, _):
        """This method needs to be overloaded if the node parser
        returns a `Node` with the `make_node` method.

        This method will not get called if `make_node` returned a
        `Node` inside a `list`. The close function takes as input the
        `Node` object that `make_node` returned and it should decide
        if the node can be closed or not. If it is indeed time to
        close the `Node` then return a list with the position where
        the `Node` is being closed, otherwise return `None`.

        If this method is not overloaded then a `NotImplementedError`
        exception will be raised.

        """
        msg = '%s did not implement `close`' % self.__class__
        raise NotImplementedError(msg)

    def msg(self, code, pos, arg=None, uri=None):
        """Send a message to the parser. """
        self.parser.msg(self.__module__, code, pos, arg, uri)


# The default of 7 attributes max in a class is too restrictive.
# pylint: disable=R0902
class Parser(object):
    """To see the languages that it is able to parse see the
    `lexor.lang` module. """

    def __init__(self, lang='xml', style='default', defaults=None):
        """Create a new parser by specifying the language and the
        style in which text will be parsed. """
        if defaults is None:
            defaults = dict()
        self._lang = lang
        self._style = style
        self._np = None
        self._next_check = None
        self._in_progress = None
        self._uri = None
        self._reload = True
        self.style_module = None
        self.text = None
        self.end = None
        self.pos = None
        self.caret = None
        self.doc = None
        self.log = None
        self.defaults = defaults
        self._node_parser = None

    def _set_node_parser(self, val):
        """Helper function to create a node parser and store it
        in dictionary. """
        if isinstance(val, str):
            return self._node_parser[val]
        name = val.__name__
        self._node_parser[name] = val(self)
        return self._node_parser[name]

    def __getitem__(self, name):
        """Return a Node parser. """
        return self._node_parser[name]

    def _set_node_parsers(self, lang, style, defaults=None):
        """Imports the correct module based on the language and style. """
        self.style_module = get_style_module('parser', lang, style)
        name = '%s-parser-%s' % (lang, style)
        config.set_style_cfg(self, name, defaults)
        self._next_check = dict()
        self._np = dict()
        self._node_parser = dict()
        if hasattr(self.style_module, 'REPOSITORY'):
            for val in self.style_module.REPOSITORY:
                self._set_node_parser(val)
        if hasattr(self.style_module, 'parser_setup'):
            self.style_module.parser_setup(self)
        str_key = list()
        for key, val in self.style_module.MAPPING.iteritems():
            self._next_check[key] = re.compile('.*?[%s]' % val[0])
            if isinstance(val, str):
                str_key.append((key, val))
            else:
                self._np[key] = [self._set_node_parser(p) for p in val[1]]
        for key, val in str_key:
            self._np[key] = self._np[val]

    def load_node_parsers(self):
        """Loads the node parsers. This function is called
        automatically when `parse` is called only if there was a
        change in the settings. """
        self._set_node_parsers(
            self._lang, self._style, self.defaults
        )
        self._reload = False

    def parse(self, text, uri=None):
        """parses the given `text`. To see the results of this method see
        the `document` and `log` property. If no `uri` is given then
        `document` will return a `DocumentFragment` node. """
        if self._reload:
            self.load_node_parsers()
        self.text = text
        self.end = len(text)
        self.pos = [1, 1]
        self.caret = 0
        self.doc = LC.Document(self._lang)
        if uri:
            self._uri = uri
        else:
            self._uri = 'string@0x%x' % id(text)
        self.doc.uri_ = self._uri
        self.log = LC.Document("lexor", "log")
        self.log.modules = dict()
        self.log.explanation = dict()
        if hasattr(self.style_module, 'pre_process'):
            self.style_module.pre_process(self)
        self._parse()
        if hasattr(self.style_module, 'post_process'):
            self.style_module.post_process(self)
        map_explanations(self.log.modules, self.log.explanation)

    @property
    def cdata(self):
        """The character sequence data that was last processed by the
        `parse` method. You may use the attribute access `text` if
        performance is an issue. """
        return self.text

    @property
    def uri(self):
        """The Uniform Resource Identifier. This is the name that was
        given to the text that was last parsed. """
        return self._uri

    @property
    def position(self):
        """Position of caret in the text in terms of line and column. i.e.
        returns [line, column]. You may use the attribute access `pos` if
        performance is an issue. """
        return self.pos

    @property
    def caret_position(self):
        """The index in the text the parser is processing. You may use
        the attribute access `caret` if performance is an issue. """
        return self.caret

    @property
    def lexor_log(self):
        """The `lexor_log` document. See this document after each
        call to `parse` to see warnings and errors in the text that
        was parsed. """
        return self.log

    @property
    def document(self):
        """The parsed document. This is a `Document` or
        `FragmentedDocument` created by the `parse` method. """
        return self.doc

    @property
    def language(self):
        """The language in which the `Parser` object will parse
        character sequences. """
        return self._lang

    @language.setter
    def language(self, value):
        """Setter function for style. """
        self._lang = value
        self._reload = True

    @property
    def parsing_style(self):
        """The style in which the `Parser` object will parse the
        character sequences. """
        return self._style

    @parsing_style.setter
    def parsing_style(self, value):
        """Setter function for style. """
        self._style = value
        self._reload = True

    def set(self, lang, style, defaults=None):
        """Set the language and style in one call. """
        if defaults is not None:
            self.defaults = defaults
        self._lang = lang
        self._style = style
        self._reload = True

    def copy_pos(self):
        """Returns a copy of the current position. """
        return list(self.pos)

    def update(self, index):
        """Changes the position of the `caret` and updates `pos`.
        This function assumes that you are moving forward. Do not
        update to an index which is less than the current position of
        the caret. """
        if index == self.caret:
            return
        nlines = self.text.count('\n', self.caret, index)
        self.pos[0] += nlines
        if nlines > 0:
            self.pos[1] = index - self.text.rfind('\n', self.caret, index)
        else:
            self.pos[1] += index - self.caret
        self.caret = index

    def compute(self, index):
        """Returns a position in the text `[line, column]` given an
        index. Note: This does not modify anything in the parser. It
        only gives you the line and column where the caret would be
        given the index. The same applies as in update. Do not use
        compute with an index less than the current position of the
        caret. """
        nlines = self.text.count('\n', self.caret, index)
        tmpline = self.pos[0] + nlines
        if nlines > 0:
            tmpcolumn = index - self.text.rfind('\n', self.caret, index)
        else:
            tmpcolumn = self.pos[1] + index - self.caret
        return [tmpline, tmpcolumn]

    # pylint: disable=R0913
    def msg(self, mod_name, code, pos, arg=None, uri=None):
        """Provide the name of module issuing the message, the code
        number, the position of caret and optional arguments and uri.
        This information gets stored in the log. """
        if uri is None:
            uri = self._uri
        if arg is None:
            arg = ()
        node = LC.Void('msg')
        node['module'] = mod_name
        node['code'] = code
        node['position'] = list(pos)
        node['uri'] = uri
        node['arg'] = arg
        if mod_name not in self.log.modules:
            self.log.modules[mod_name] = sys.modules[mod_name]
        self.log.append_child(node)

    def _get_np(self, node):
        """Get a node parser based on the name of the node. """
        return self._np.get(node.name, self._np['__default__'])

    def _get_next_checker(self, node):
        """Get the checker based on the name of the node. """
        return self._next_check.get(node.name, self._next_check['__default__'])

    def _get_next_check(self, node):
        """Locate the index where a processor might return Node. If
        there is no index then return -1."""
        match = self._get_next_checker(node).search(self.text, self.caret)
        if match is None:
            return -1
        return match.end(0)-1

    def _process_node(self, crt, node, processor):
        """Appends the node to crt. """
        if isinstance(node, LC.Text):
            if len(crt) > 0 and isinstance(crt[-1], LC.Text):
                crt[-1].data += node.data
            else:
                crt.append_child(node)
        elif isinstance(node, list):  # Empty Element
            crt.append_child(node[0])
        else:
            crt.append_child(node)
            if isinstance(node.child, list):
                self._in_progress.append((node, processor))
                return node
        return None

    def _process_text(self, crt):
        """When there is no node then we just read the text. """
        index = self._get_next_check(crt)
        if index == -1:
            content = self.text[self.caret:self.end]
            if len(crt) > 0 and isinstance(crt[-1], LC.Text):
                crt[-1].data += content
            else:
                crt.append_child(content)
            self.update(self.end)
            return
        elif index - self.caret == 0:
            index += 1
        content = self.text[self.caret:index]
        self.update(index)
        if len(crt) > 0 and isinstance(crt[-1], LC.Text):
            crt[-1].data += content
        else:
            crt.append_child(content)

    def _close_node(self):
        """Checks and closes a node that is in self._in_progress. """
        num = len(self._in_progress)
        autoclose = None
        for node, processor in reversed(self._in_progress):
            num -= 1
            autoclose = processor.close(node)
            if autoclose is not None:
                break
        if autoclose is not None:
            # Must go backwards since the list inprogress is
            # changing.
            for i in xrange(len(self._in_progress)-1, num, -1):
                name = self._in_progress[i][0].name
                self.msg(
                    self.__module__, 'W100',
                    self._in_progress[i][0].pos,
                    (name, autoclose[0], autoclose[1])
                )
                del self._in_progress[i][0].pos
                del self._in_progress[i]
            del self._in_progress[num]
            if self._in_progress:
                return self._in_progress[-1][0]
            else:
                return self.doc
        return None

    def _parse(self):
        """Main parsing function. This function depends on the
        node parsers of the language. """
        crt = self.doc
        self._in_progress = []
        while self.caret < self.end:
            tmp = self._close_node()
            if tmp is not None:
                crt = tmp
                continue
            match = False
            processor = None
            for processor in self._get_np(crt):
                node = processor.make_node()
                if node is not None:
                    match = True
                    break
                elif self.caret == self.end:
                    break
            if match is False:
                self._process_text(crt)
            elif self._process_node(crt, node, processor) is node:
                crt = node
        for node, processor in self._in_progress:
            self.msg(self.__module__, 'E100', node.pos, [node.name])
            del node.pos


MSG = {
    'E100': 'closing string for `Node` of name "{0}" not found',
    'W100': 'auto-closing `Node` of name "{0}" at {1}:{2:2}',
}
MSG_EXPLANATION = [
    """
    - The parser did not find a closing string for the given node.

    - This is a general error which is language dependent. Make sure
      to provide the required closing string for the node.

    The following are examples for HTML, LaTeX and Lexor:

    Okay: <node></node>
    Okay: \\begin{node}\\end{node}
    Okay: %%{node}%%

    E100: <node>
    E100: \\begin{node}
    E100: %%{node}
""",
    """
    - The parser was forced to automatically close the current node
      in progress due to the encounter of the closing sequence of a
      parent node.

    - This is a general warning which is language dependent. To get
      rid of this warning provide the closing sequence for the node
      before the closing sequence of the parent node.

    The following is an example in HTML:

    Okay: <a><p>stuff</p><p>stuff</p></a>
    Okay: <a><p>stuff<p>stuff</p></a>

    W100: <a><p>stuff</p><p>stuff</a>
    W100: <a><p>stuff<p>stuff</a>
""",
]
