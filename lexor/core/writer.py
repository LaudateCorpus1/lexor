"""
Provides the |Writer| object which defines the basic mechanism for
writing the objects defined in :mod:`lexor.core.elements`. This
involves using objects derived from the abstract class |NodeWriter|.

.. |Writer| replace:: :class:`~.Writer`
.. |NodeWriter| replace:: :class:`~.NodeWriter`
.. |Node| replace:: :class:`~lexor.core.node.Node`
.. |CharData| replace:: :class:`~lexor.core.elements.CharacterData`
.. |Element| replace:: :class:`~lexor.core.elements.Element`

"""
import re
from cStringIO import StringIO
from lexor.command.lang import get_style_module
from lexor.command import config
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

    Source: http://stackoverflow.com/a/15221068/788553

    """
    return _replacer(*key_val)(string)


def find_whitespace(line, start, lim):
    """Attempts to find the index of the first whitespace before
    `lim`, if its not found, then it looks ahead. """
    index = line.rfind(' ', start, lim+1)
    if index != -1:
        return index
    index = line.find(' ', lim)
    if index != -1:
        return index
    return len(line)


class NodeWriter(object):
    """A node writer is an object which writes a node in three steps:

    - `start`
    - `data/child`
    - `end`

    """

    def __init__(self, writer):
        """A |NodeWriter| needs to be initialized with a |Writer|
        object. If this method is to be overloaded then make sure
        that it only accepts one parameter: `writer`. This method is
        used by the |Writer| and it calls it with itself as the
        parameter."""
        self.writer = writer

    def write(self, string, split=False):
        """Writes the string to a file object. The file object is
        determined by the |Writer| object that initialized this
        object (`self`). """
        self.writer.write_str(string, split)

    def start(self, node):
        """Overload this method to write part of the |Node| object in
        the first encounter with the |Node|. """
        pass

    def data(self, node):
        """This method gets called only by |CharData| nodes and
        should be overloaded to write their attribute ``data``,
        otherwise it will write the node's data as it is. """
        self.writer.write_str(node.data)

    @classmethod
    def child(cls, _):
        """This method gets called for |Element| nodes that have
        children. If it is overwritten then it will not traverse
        through child nodes unless you return something other than
        ``None``.

        This method by default returns ``True`` so that the |Writer|
        can traverse through the child nodes. """
        return True

    def end(self, node):
        """Overload this method to write part of the |Node| object in
        the last encounter with the |Node|. """
        pass


class DefaultWriter(NodeWriter):
    """If the language does not define a |NodeWriter| for
    ``__default__`` in the ``MAPPING`` dictionary then the writer
    will use this |NodeWriter|."""

    def start(self, node):
        """Write the start of the node as a XML tag. """
        att = ' '.join(['%s="%s"' % (k, v) for k, v in node.items()])
        if att != '':
            self.write('<%s %s>' % (node.name, att))
        else:
            self.write('<%s>' % node.name)

    def end(self, node):
        """Write the end of the node as an XML end tag. """
        self.write('</%s>' % node.name)


# The default of 7 attributes for class is too restrictive.
# pylint: disable=R0902
class Writer(object):
    """To see the languages available to the writer see the
    :mod:`lexor.command.lang` module. """

    def __init__(self, lang='xml', style='default', defaults=None):
        """Create a new writer by specifying the language and the
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
        self._reload = True  # Create new NodeWriters

        self._raw = None
        self._wrap = None
        self._buffer = None
        self._break_hint = None
        self._indent = None
        self._indent_empty = None
        self.pos = None
        self.width = None

        self.root = None   # The node to be written
        self.prev_str = None  # Reference to the last string printed

    def __getitem__(self, name):
        """Return the specified |NodeWriter|. """
        return self._nw.get(name, self._nw['__default__'])

    @property
    def filename(self):
        """
        .. admonition:: Read-Only Property
            :class: note

            The name of the file to which a |Node| object was last
            written to."""
        return self._filename

    @property
    def language(self):
        """The language in which the |Writer| writes |Node| objects.
        """
        return self._lang

    @language.setter
    def language(self, value):
        """_lang setter method. """
        self._lang = value
        self._reload = True

    @property
    def indent(self):
        """The indentation at the beginning of each line. """
        return self._indent

    @indent.setter
    def indent(self, value):
        """_indent setter method. """
        self.flush_buffer(tail=False)
        self._indent = value

    @property
    def writing_style(self):
        """The style in which the |Writer| writes a |Node| object. """
        return self._style

    @writing_style.setter
    def writing_style(self, value):
        """_style setter method. """
        self._style = value
        self._reload = True

    @property
    def string_buffer(self):
        """The current string buffer. This is the string that will
        be printed after its length exceeds the writer's width. """
        return self._buffer

    @string_buffer.setter
    def string_buffer(self, value):
        """_indent setter method. """
        self._buffer = value

    def set(self, lang, style, defaults=None):
        """Set the language and style in one call. """
        self._style = style
        self._lang = lang
        self.defaults = defaults
        self._reload = True

    def __str__(self):
        """Attempts to retrieve the last written string. """
        if self._filename is None and self._file is not None:
            return self._file.getvalue()
        if self._filename is not None:
            tmp = open(self._filename, 'r')
            val = tmp.read()
            tmp.close()
            return val
        return None

    def _write_str(self, string):
        """Helper function for write_str. """
        if string != '':
            self.prev_str = string
            self._file.write(string)
            nlines = string.count('\n')
            self.pos[0] += nlines
            if nlines > 0:
                self.pos[1] = len(string) - string.rfind('\n')
            else:
                self.pos[1] += len(string)

    def write_str(self, string, split=False):
        """The write function is meant to be used with |Node|
        objects. Use this function to write simple strings while the
        file descriptor is open. """
        if self._raw:
            self._write_str(string)
            return
        if not self._wrap:
            if self._indent != '':
                lines = string.split('\n')
                if self.pos[1] == 1:
                    if lines[0] != '' or self._indent_empty:
                        lines[0] = self._indent + lines[0]
                for num in range(1, len(lines)):
                    if lines[num] != '' or self._indent_empty:
                        lines[num] = self._indent + lines[num]
                self._write_str('\n'.join(lines))
            else:
                self._write_str(string)
            return
        if split:
            self._break_hint.append(string)
        lines = string.split('\n')
        num = 0
        while num < len(lines) - 1:
            self._buffer += lines[num]
            self.normalize_buffer()
            self.flush_buffer()
            self._write_str('\n')
            num += 1
        self._buffer += lines[num]
        self.normalize_buffer()

    def flush_buffer(self, tail=True):
        """Empty the contents of the buffer. """
        if not tail and self._buffer.endswith(' '):
            self._buffer = self._buffer[:-1]
        if self.pos[1] == 1:
            if self._buffer.startswith(' '):
                self._buffer = self._buffer[1:]
            if self._buffer != '':
                self._write_str(self._indent + self._buffer)
            elif self._indent_empty:
                self._write_str(self._indent)
        else:
            self._write_str(self._buffer)
        self._buffer = ''

    def normalize_buffer(self):
        """The term normalize means that the length of the buffer
        will be less than or equal to the wrapping width. Anything
        that exceeds the limit will be flushed. """
        line = self._buffer
        indent = self._indent
        if self.pos[1] > 1:
            indent = ''
        limit = self.width - self.pos[1] - len(indent) + 1
        while len(line) > limit:
            start = 0
            if line[start] == ' ':
                start += 1
            end = find_whitespace(line, start, limit)
            while self._break_hint:
                index = line.find(self._break_hint[0], start)
                del self._break_hint[0]
                if index > -1 and index <= limit:
                    if end > limit or index > end:
                        end = index
            if end == len(line):
                break
            self._write_str(indent + line[start:end] + '\n')
            if line[end:end+1] == ' ':
                line = line[end+1:]
            else:
                line = line[end:]
            indent = self._indent
            limit = self.width - self.pos[1] - len(indent) + 1
        self._buffer = line

    def enable_wrap(self):
        """Use this to set the writing in wrapping mode. """
        self._wrap = True

    def disable_wrap(self):
        """Turn off wrapping. """
        self.flush_buffer()
        self._wrap = False

    def enable_raw(self):
        """Use this to set the writing in raw mode. """
        self.flush_buffer()
        self._raw = True

    def disable_raw(self):
        """Turn off raw mode. """
        self._raw = False

    def raw_enabled(self):
        """Determine if raw mode is enabled or not. """
        return self._raw

    def wrap_enabled(self):
        """Determine if wrap mode is enabled or not. """
        return self._wrap

    def endl(self, force=True, tot=1, tail=False):
        """Insert a new line character. By setting `force` to
        ``False`` you may omit inserting a new line character if the
        last character printed was already the new line character."""
        prev_str = self.last()
        self.flush_buffer(tail)
        if force or (not prev_str.endswith('\n') and
                     prev_str != self._indent):
            self._write_str('\n'*tot)

    def last(self):
        """Returns the last written string with the contents of the
        buffer. """
        if self.pos[1] == 1 and self._buffer.startswith(' '):
            return self.prev_str + self._buffer[1:]
        return self.prev_str + self._buffer

    def write(self, node, filename=None, mode='w'):
        """Write node to a file or string. To write to a string use
        the default parameters, otherwise provide a `filename`. If
        `filename` is provided you have the option of specifying the
        mode: ``'w'`` or ``'a'``.

        You may also provide a file you may have opened yourself in
        place of filename so that the writer writes to that file.

        Use the :meth:`__str__` function to retrieve the contents
        written to a string."""
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
        self._raw = True
        self._wrap = False
        self._buffer = ''
        self._break_hint = []
        self._indent = ''
        self._indent_empty = False
        self.pos = [1, 1]
        self.width = 70
        self.prev_str = '\n'
        if self._reload:
            self._set_node_writers(self._lang, self._style, self.defaults)
            self._reload = False
        self._set_node_writers_writer()
        if hasattr(self.style_module, 'pre_process'):
            self.style_module.pre_process(self, node)
        self._write(node)
        self.flush_buffer()
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
        self._nw['#cdata-section'] = nw_obj
        str_key = list()
        for key, val in self.style_module.MAPPING.iteritems():
            if isinstance(val, str):
                str_key.append((key, val))
            else:
                self._nw[key] = val(self)
        for key, val in str_key:
            self._nw[key] = self._nw[val]

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
        if hasattr(crt, 'data'):
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
        if hasattr(crt, 'data'):
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
