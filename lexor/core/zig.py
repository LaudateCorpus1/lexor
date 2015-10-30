"""

"""
import sys
LC = sys.modules['lexor.core']


class Zig(object):
    """Helper object to the Converter. It is meant to attach to a Node
    object and hold temporary information. A zig object should be
    removed after the Converter runs the post_link method on all of
    its directives.
    """

    def __init__(self, converter, node):
        node.zig = self
        self.converter = converter
        self.node = node
        self.directives = []
        self.shared_info = {
            'remove': [],
            'remove_children': [],
            'replace': [],
        }
        self.template_nodes = dict()
        self.requirements = dict()

    def get_directives(self):
        """Examine the zigs node and capture the directives that
        can be applied to the node.
        """
        if self._is_terminal(self.node.name, 'E'):
            return
        if not isinstance(self.node, LC.Element):
            return
        for att in self.node.attributes:
            if att == 'class':
                candidates = self.node['class'].split()
                for cls in candidates:
                    if self._is_terminal(cls, 'C'):
                        return
            elif self._is_terminal(att, 'A'):
                return

    def _is_terminal(self, directive, restrict):
        """Collect the directives and return ``True`` if the
        diretive is terminal.
        """
        trans = self.converter
        if not trans.has(directive):
            return None
        node_trans = trans.get(directive)
        if restrict not in node_trans.restrict:
            return None
        self._get_shared_info(directive, node_trans)
        priority = node_trans.priority
        directives = self.directives
        index = len(directives)
        while index > 0 and priority > directives[index-1][1]:
            index -= 1
        directives.insert(index, (directive, priority))
        if node_trans.terminal:
            return True

    def _get_shared_info(self, directive, node_trans):
        """Helper function to attach information on `info`. """
        info = self.shared_info
        if node_trans.remove:
            info['remove'].append(directive)
            values = ['compile', 'pre_link', 'post_link']
            try:
                new_val = values.index(node_trans.remove)
            except ValueError:
                new_val = 0
            if 'remove_after' in info:
                crt_val = values.index(info['remove_after'])
            else:
                info['remove_after'] = values[2]
                crt_val = 2
            if new_val < crt_val:
                info['remove_after'] = values[new_val]
        if node_trans.remove_children:
            info['remove_children'].append(directive)
        if node_trans.replace:
            info['replace'].append(directive)

    def get_requirement(self, req):
        """Find the given requirement in the zigs node. The
        requirement may be a string which will be parsed or an
        already parsed requirement.

        Returns a tuple containing the directive and the node where
        it was found.
        """
        node = self.node
        if isinstance(req, str):
            req = parse_requirement(req)
        for requirement in req:
            optional, level, directive = requirement
            if level in [-2, -1]:
                if level == -1:
                    for name, _ in self.directives:
                        if directive == name:
                            return directive, node
                crt = node
                while crt.parent is not None:
                    crt = crt.parent
                    for name, _ in crt.zig.directives:
                        if directive == name:
                            return directive, crt
            elif level == 0:
                for name, _ in self.directives:
                    if directive == name:
                        return directive, node
            else:
                crt = node
                parent_num = 0
                while crt.parent is not None and parent_num < level:
                    crt = crt.parent
                    parent_num += 1
                if parent_num == level:
                    for name, _ in crt.zig.directives:
                        if directive == name:
                            return directive, crt
            if optional:
                return directive, None
        raise LexorError('Requirement not found: %r' % req, req=req)

    def store_requirements(self, directive):
        node_trans = self.converter.get(directive)
        require = [
            self.get_requirement(r)
            for r in node_trans._require
        ]
        self.requirements[directive] = require
        return require


def _parse_requirement(req):
    """Helper function for ``parse_requirement"""
    optional = req[0] == '$'
    caret = int(optional)
    if req[caret] != '^':
        level = 0
    elif req[caret+1] == '^':
        level = -2
        caret += 2
    elif req[caret+1] == '(':
        caret += 2
        begin = caret
        while req[caret] != ')':
            caret += 1
        tmp = req[begin:caret]
        level = -1 if not tmp else int(tmp)
        caret += 1
    else:
        caret += 1
        begin = caret
        while req[caret].isdigit():
            caret += 1
        tmp = req[begin:caret]
        level = -1 if not tmp else int(tmp)
    directive = req[caret:]
    return optional, level, directive


def parse_requirement(req):
    """Parse a string ``req``. Each requiment can be prefixed with
    any of the following:

        (no prefix), $, ^, ^^, $^, $^^, ^N, $^N

    Returns the tuple ``(optional, level, directive)`` where

    - optional: boolean specifying if the requirement is
                optional, that is, not to raise an
                exception if the directive is not found.
    - level: 0 if the directive should be on the same node
             N if the directive should be on the Nth parent
             -1 if the directive may be found in the same
                node or any of the parents.
             -2 if the directive may be found in any of the
                parent nodes.
    - directive: The directive name

    The requirement may provide backup requirements by separating
    them with ``|``.
    """
    return [_parse_requirement(r) for r in req.split('|')]


def _encode_requirement(req):
    """Helper function for encode_requirement."""
    result = '$' if req[0] else ''
    if req[1] == -2:
        result += '^^'
    elif req[1] == -1:
        result += '^'
    elif req[1] > 0:
        result += '^(' + str(req[1]) + ')'
    result += req[2]
    return result


def encode_requirement(req):
    """Encode a parsed requirement."""
    return '|'.join([_encode_requirement(r) for r in req])
