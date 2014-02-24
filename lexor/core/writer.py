"""Writer Module

Provides the `Writer` object which defines the basic mechanism for
writing the objects defined in `lexor.core.elements`. This involves
using objects derived from the abstract class `NodeWriter`. See
`lexor.core.dev` for more information on how to write objects derived
from `NodeWriter` to be able to write `Documents` in the way you
desire.

"""

import re
from cStringIO import StringIO
from lexor.command.lang import get_style_module
import lexor.command.config as config
import lexor.core.elements
RE = re.compile(" ")


def _replacer(*key_val):
    """Helper function for replace.

    Source: <http://stackoverflow.com/a/15221068/788553>
    """
    replace_dict = dict(key_val)
    replacement_function = lambda match: replace_dict[match.group(0)]
    pattern = re.compile("|".join([re.escape(k) for k, _ in key_val]), re.M)
    return lambda string: pattern.sub(replacement_function, string)


def replace(string, *key_val):
    """Replacement of strings done in one pass. Example:

        >>> replace("a < b && b < c", ('<', '&lt;'), ('&', '&amp;'))
        'a &lt; b &amp;&amp; b &lt; c'

    Source: <http://stackoverflow.com/a/15221068/788553>

    """
    return _replacer(*key_val)(string)


def find_whitespace(line, start, lim):
    """Attempts to find the index of the first whitespace before
    lim, if its not found, then it looks ahead. """
    index = line.rfind(' ', start, lim+1)
    if index != -1:
        return index
    index = line.find(' ', lim)
    if index != -1:
        return index
    return len(line)


class NodeWriter(object):
    """A node writer is an object which writes a node in three steps:
    `start`, `data/child`, `end`.

    """

    def __init__(self, writer):
        """A `NodeWriter` needs to be initialized with a writer
        object. If this method is to be overloaded then make sure
        that it only accepts one parameter: `writer`. This method is
        used by `Writer` and it calls it with itself as the parameter.

        """
        self.writer = writer

    def write(self, string):
        """Writes the string to a file object. The file object is
        determined by the `Writer` object that initialized this
        object (`self`). """
        self.writer.strwrite(string)

    def wrap(self, string, **keywords):
        """Writes the string to a file object by wrapping the text at
        `width`. The file object is determined by the `Writer` object
        that initialized this object (`self`). """
        self.writer.wrap(string, **keywords)

    def start(self, node):
        """Overload this method to write part of the `Node` object in
        the first encounter with the `Node`. """
        pass

    def data(self, node):
        """This method gets called only by `CharacterData` nodes.
        This method should be overloaded to write their attribute
        `data`, otherwise it will write the node's data as it is. """
        self.writer.strwrite(node.data)

    @classmethod
    def child(cls, _):
        """This method gets called for `Elements` that have children.
        If it gets overwritten then it will not traverse through
        child nodes unless you return something other than None.

        This method by default returns `True` so that the `Writer`
        can traverse through the child nodes. """
        return True

    def end(self, node):
        """Overload this method to write part of the `Node` object in
        the last encounter with the `Node`. """
        pass


class DefaultWriter(NodeWriter):
    """If the language does not define a NodeWriter for __default__
    then the writer will use this default writer.

    """

    def start(self, node):
        """Write the start of the node as a xml tag. """
        att = ' '.join(['%s="%s"' % (k, v) for k, v in node.items()])
        if att != '':
            self.write('<%s %s>' % (node.name, att))
        else:
            self.write('<%s>' % node.name)

    def end(self, node):
        """Write the end of the node as an xml end tag. """
        self.write('</%s>' % node.name)


# The default of 7 attributes for class is too restrictive.
# pylint: disable=R0902
class Writer(object):
    """To see the languages in which a `Writer` object is able to
    write see the `lexor.lang` module. """

    def __init__(self, lang='xml', style='default', defaults=None):
        """Create a new `Writer` by specifying the language and the
        style in which `Node` objects will be written. """
        if defaults is None:
            defaults = dict()
        self.defaults = defaults
        self.style_module = None
        self._lang = lang
        self._style = style
        self._filename = None
        self._file = None  # Points to a file object
        self._nw = None    # Array of NodeWriters
        self._break_hint = []
        self._reload = True  # Create new NodeWriters
        self.buffer = ''
        self._wrap = True
        self._raw = False
        self.pos = None
        self.width = 70
        self.root = None   # The node to be written
        self.prev_str = '\n'  # Reference to the last string printed

    @property
    def filename(self):
        """READ-ONLY: The name of the file to which a `Node` object
        was last written to. """
        return self._filename

    @property
    def language(self):
        """The language in which the `Writer` writes `Node` objects. """
        return self._lang

    @language.setter
    def language(self, value):
        """_lang setter method. """
        self._lang = value
        self._reload = True

    @property
    def writing_style(self):
        """The style in which the `Writer` writes a `Node` object. """
        return self._style

    @writing_style.setter
    def writing_style(self, value):
        """_style setter method. """
        self._style = value
        self._reload = True

    def set(self, lang, style, defaults=None):
        """Set the language and style in one call. """
        self._style = style
        self._lang = lang
        self.defaults = defaults
        self._reload = True

    def __str__(self):
        """Attempts to retrive the last written string. """
        if self._filename is None and self._file is not None:
            return self._file.getvalue()
        if self._filename is not None:
            tmp = open(self._filename, 'r')
            val = tmp.read()
            tmp.close()
            return val
        return None

    def strwrite(self, string):
        """The write function is meant to be used with Node objects.
        Use this function to write simple strings while the file
        descriptor is open. """
        if string != '':
            self.prev_str = string
            self._file.write(string)
            nlines = string.count('\n')
            self.pos[0] += nlines
            if nlines > 0:
                self.pos[1] = len(string) - string.rfind('\n')
            else:
                self.pos[1] += len(string)

    def flush_buffer(self, width):
        """If the `buffer` length plus the `caret` has exceed for
        more than `width` characters then it writes at most `width`
        characters from the buffer and a new line. It continues doing
        so until the buffer is less than `width` characters. """
        line = self.buffer
        while len(line) > width:
            start = 0
            if line[start] == ' ':
                start += 1
            end = find_whitespace(line, start, width) + 1
            while self._break_hint:
                index = line.find(self._break_hint[0], start)
                del self._break_hint[0]
                if index not in [-1, start] and index <= width:
                    if end > width or index > end:
                        end = index
            offset = 0
            if line[end-1:end] == ' ':
                offset = -1
            self.strwrite(line[start:end+offset])
            offset = 0
            if line[end:end+1] == ' ':
                offset = 1
            line = line[end+offset:]
            self.strwrite('\n')
        self.buffer = line

    def wrap(self, string, **keywords):
        """Writes a string by wrapping it at width. """
        if not self._wrap:
            self.strwrite(string)
            return
        if self._raw or keywords.get('raw', False):
            self.strwrite(self.buffer)
            index = string.rfind('\n')
            if index == -1:
                self.buffer = string
            else:
                self.strwrite(string[:index+1])
                self.buffer = string[index+1:]
            return
        width = keywords.get('width', self.width)
        if keywords.get('split', False):
            self._break_hint.append(string)
        lines = string.split('\n')
        line_num = 0
        while line_num < len(lines) - 1:
            self.buffer += lines[line_num]
            self.flush_buffer(width)
            self.strwrite('%s\n' % self.buffer)
            self.buffer = ''
            line_num += 1
        self.buffer += lines[line_num]
        self.flush_buffer(width)

    def enable_wrap(self):
        """Use this to set the writing in wrapping mode. """
        self._wrap = True

    def disable_wrap(self):
        """Turn off wrapping. """
        self._wrap = False
        if self.buffer != '':
            self.strwrite(self.buffer)
            self.buffer = ''

    def enable_raw(self):
        """Use this to set the writing in raw mode. """
        self._raw = True

    def disable_raw(self):
        """Turn off raw mode. """
        self._raw = False

    def endl(self, force=True):
        """Insert a new line character. By setting `force` to False
        you may ommit inserting a new line character if the last
        character printed was already the new line character."""
        if self.buffer:
            self.strwrite(self.buffer)
            self.buffer = ''
        if force or not self.prev_str.endswith('\n'):
            self.strwrite('\n')

    def write(self, node, filename=None, mode='w'):
        """Write node to a file or string. To write to a string use
        the default parameters, otherwise provide a file name. If
        filename is provided you have the option of especifying the
        mode: 'w' or 'a'.

        You may also provide a file you may have opened yourself in
        place of filename so that the writer writes to that file.

        Use the __str__ function to retrieve the contents written to
        a string.

        """
        if isinstance(filename, file):
            # Check for stdout, stderr
            self._filename = file
            self._file = filename
        elif filename is None:
            # Check for StringIO
            self._filename = None
            if self._file is not None:
                self._file.close()
            self._file = StringIO()
        else:
            self._filename = filename
            self._file = open(filename, mode)
        self.root = node
        if self._reload:
            self._set_node_writers(self._lang, self._style, self.defaults)
            self._reload = False
        self._set_node_writers_writer()
        if hasattr(self.style_module, 'pre_process'):
            self.style_module.pre_process(self, node)
        self.pos = [1, 1]
        self._write(node)
        self.strwrite(self.buffer)
        self.buffer = ''
        if hasattr(self.style_module, 'post_process'):
            self.style_module.post_process(self, node)
        if isinstance(filename, file):
            pass
        elif filename is not None:
            self._file.close()

    def close(self):
        """Close the file. """
        if self._filename is not file:
            self._file.close()

    def _set_node_writers(self, lang, style, defaults=None):
        """Imports the correct module based on the language and
        style. """
        self.style_module = get_style_module('writer', lang, style)
        name = '%s-writer-%s' % (lang, style)
        config.set_style_cfg(self, name, defaults)
        self._nw = dict()
        self._nw['__default__'] = DefaultWriter(self)
        nw_obj = NodeWriter(self)
        self._nw['#document'] = nw_obj
        self._nw['#document-fragment'] = nw_obj
        self._nw['#text'] = nw_obj
        self._nw['#entity'] = nw_obj
        str_key = list()
        for key, val in self.style_module.MAPPING.iteritems():
            if isinstance(val, str):
                str_key.append((key, val))
            else:
                self._nw[key] = val(self)
        for key, val in str_key:
            self._nw[key] = self._nw[val]

    def get_node_writer(self, name):
        """Return one of the NodeWriter objects available to the
        Writer."""
        return self._nw.get(name, self._nw['__default__'])

    def _set_node_writers_writer(self):
        """To be called before writing since the file will change. """
        for key in self._nw:
            self._nw[key].writer = self

    def _write_start(self, node):
        """To be called during tree traversal when node is first
        encountered. """
        self._nw.get(node.name, self._nw['__default__']).start(node)

    def _write_data(self, node):
        """To be called during tree traversal after _write_start if the
        node is a `CharacterData`. """
        self._nw.get(node.name, self._nw['__default__']).data(node)

    def _write_child(self, node):
        """To be called during tree traversal after _write_start if the
        node has children. """
        return self._nw.get(node.name, self._nw['__default__']).child(node)

    def _write_end(self, node):
        """To be called during tree traversal on last visit to node. """
        self._nw.get(node.name, self._nw['__default__']).end(node)

    def _get_direction(self, crt):
        """Returns the direction in which the traversal should go. """
        if isinstance(crt, lexor.core.elements.CharacterData):
            self._write_data(crt)
            self._write_end(crt)
            return 'r'
        elif crt.child:
            if self._write_child(crt) is None:
                return 'r'
            else:
                return 'd'
        else:
            self._write_end(crt)
            return 'r'

    def _write(self, root):
        """To be called during actual write function. """
        crt = root
        direction = None
        self._write_start(crt)
        if isinstance(crt, lexor.core.elements.CharacterData):
            self._write_data(crt)
            self._write_end(crt)
            return
        if crt.child:
            if self._write_child(crt) is None:
                return
            else:
                direction = 'd'
        else:
            self._write_end(crt)
            return
        while True:
            if direction is 'd':
                crt = crt.child[0]
            elif direction is 'r':
                if crt.next is None:
                    direction = 'u'
                    continue
                crt = crt.next
            elif direction is 'u':
                self._write_end(crt.parent)
                if crt.parent is root:
                    break
                if crt.parent.next is None:
                    crt = crt.parent
                    continue
                crt = crt.parent.next
            self._write_start(crt)
            direction = self._get_direction(crt)
