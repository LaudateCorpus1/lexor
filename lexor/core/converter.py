"""
Provides the |Converter| object which defines the basic mechanism for
converting the objects defined in :mod:`lexor.core.elements`. This
involves using objects derived from the abstract class
|NodeConverter|.

There are a couple of functions that have been written to be used
inside python embeddings. These are:

- :func:`echo`
- :func:`include`
- :func:`import_module`

When writing python embeddings there are several special variables
that can be used:

- ``__NAMESPACE__``: The namespace where the execution is taking place
- ``__NODE__``: The current processing instruction
- ``__FILE__``:  path of the document which is executing the
                 python embedding
- ``__DIR__``: equivalent to ``os.path.dirname(__FILE__)``


.. |Converter| replace:: :class:`~.Converter`
.. |Parser| replace:: :class:`~lexor.core.parser.Parser`
.. |NodeConverter| replace:: :class:`~.Converter`
.. |Document| replace:: :class:`~lexor.core.elements.Document`
.. |DocFrag| replace:: :class:`~lexor.core.elements.DocumentFragment`
.. |Text| replace:: :class:`~lexor.core.elements.Text`
.. |PI| replace:: :class:`~lexor.core.elements.ProcessingInstruction`

"""
import os
import sys
import os.path as pth
import traceback
import inspect
import lexor
from lexor import load_aux
from imp import load_source
from cStringIO import StringIO
from lexor.command import config, LexorError
from lexor.command.lang import get_style_module, map_explanations
from lexor.util.logging import L
LC = sys.modules['lexor.core']


class NodeConverter(object):
    """A node converter is an object which executes commands on
    some special elements in the document. The elements in which
    the node converter executes are determined by the directive
    name of the node converter. The following are some of the
    properties that you may define when deriving a ``NodeConverter``.

    - directive: This is the name which the node converter looks for
                 to determine if it should execute commands on a node.

    - restrict: A string specifying where to look for the directive
                name. The string is allowed to have any of the
                following charcters:

                'E': Search in the node name
                'A': Search in any of the attributes names.
                'C': Search in the class.

                By default we restrict a node directive to the
                element name.

    - priority: Sometimes it is necessary to specify the order in
                which directives are run, this is mainly when an
                attribute directive needs be ran before the element
                one. The priority is used to sort the directives
                before their compile functions get called. Priority
                is defined as a number. Directives with greater
                numerical priority are compiled first and their
                pre-link functions are also run in priority order.
                Directives with the same priority are ordered in the
                ordered in which they are declared. The default
                priority is 0.

    - remove: Boolean specifying if the node should be removed. Note
              that if another directive acts on a node and has the
              remove property set to ``True`` then only the compile
              method of this node converter will execute and the node
              will be removed. It only takes one to ruin everything.
              By default this property is set to ``False`` so be very
              careful when removing nodes and all its children.

    - remove_children: Boolean specifying if the children of the node
                       should be removed. Note that setting this to
                       True will remove the children during the
                       compile phase and those nodes will not be
                       available even if the tranclude property is
                       set. By default it is set to ``False`` and
                       as with the ``remove`` property, if another
                       directive has this property then none
                       of the other directives will have access
                       those children.

    - terminal: If set to true then the current directive will be the
                last one to execute.

    - template: A string co

    - auto_transclude: The name of an element in the template in which
                       the transcluded elements will be placed. Note
                       that this will remove the element itself and
                       replaced by the trancluded contents. For this
                       reason you have to choose a name that does not
                       collide with any other element in the template.
                       Also, if more than one elements are declared,
                       only the first one is used.

    - require: A list of required directives to get a handle on. Some
               times we may require another directive to be declared
               on the current node or perhaps in one of the parents.

               The require property is a list of directive names. Each
               name can be prefixed with

               * (no prefix) - Locate the required node converter on
                               the current element. Throw an error if
                               not found.
               * $ - Attempt to locate the required node converter or
                     pass None if not found.
               * ^ - Locate the required node converter by searching
                     the element and its parents. Throw an error if
                     not found.
               * ^^ - Locate the required node converter by searching
                      the element's parents. Throw an error if not
                      found.
               * $^ - Attempt to locate the required node converter
                      by searching the element and its parents or pass
                      None if not found.
               * $^^ - Attempt to locate the required node converter
                       by searching the element's parents, or pass
                       None if not found.
               * ^N - Locate the require node converter by searching
                      the Nth element's parent. Throw an error if not
                      found.
               * $^N - Attempt to locate the required node converter
                       by searching the Nth element's parent, or pass
                       None if not found.

               Additionally, if a node converter is not found you may
               try to recover by asking for another one by separating
               with `|`. For instance:

               require: ['?python|?py', '^1dir_name']

               This says, look for the directive of name '?python', if
               its not found, look for '?py', and the first parent
               must contain the directive 'dir_name'.

    NOTE: All nodes execute the compile method. The prelink and
    postlink however, those are only run by Elements.

    """
    directive = None
    directive_alias = []
    restrict = 'E'
    priority = 0
    remove = False
    remove_children = False
    terminal = False

    template = None
    template_uri = None
    template_parser = {
        'lang': 'lexor',
        'style': '_',
        'defaults': {
            'inline': 'on'
        }
    }
    _template = None
    replace = False

    transclude = False
    auto_transclude = False
    require = []
    _require = None

    def __init__(self, converter):
        """A node converter needs to be initialized with a converter
        object. If this method is to be overloaded then make sure
        that it only accepts one parameter: `converter`. This method
        is used by |Converter| and it calls it with itself as the
        parameter. """
        self.converter = converter

        if self.directive is None:
            raise LexorError('missing directive name')
        if isinstance(self.require, str):
            self.require = [self.require]
        parse = LC.parse_requirement
        self._require = [parse(r) for r in self.require]

    def compile(self, node, dir_info, t_node, required):
        """Method to run during the compilation phase. Here we can
        use the current ``node`` in which the directive is running.
        ``dir_info`` is a dictionary with the directive information,
        it mainly informs you if any other directives in the node
        will remove the node or any of the children. Then we get
        the ``t_node`` which is the compiled template that the
        directive declares. Finally ``required`` is an array
        containing the required directives for this node converter.
        """
        pass

    def pre_link(self, node, dir_info, trans_ele, required):
        pass

    def post_link(self, node, dir_info, trans_ele, required):
        pass

    def msg(self, code, node, arg=None, uri=None):
        """Send a message to the converter by providing one of the
        error codes defined in the style as well as the node
        where the error took place. Some error codes may provide
        arguments, this can be passed to `arg`. In case the error
        occurred somewhere not in the current document, perhaps in a
        string, then you may provide a new `uri` to denote the
        location.
        """
        self.converter.msg(self.__module__, code, node, arg, uri)


class NCContainer(object):

    def __init__(self, nc):
        self.nc_class = nc
        self.instance = None

    def get(self, converter):
        if self.instance is None:
            L.info('... initializing %r', self.nc_class)
            self.instance = self.nc_class(converter)
        return self.instance


class PythonNC(NodeConverter):
    """Append a node with python instructions to a list. """

    directive = '?python'
    directive_alias = ['?py']

    def __init__(self, converter):
        NodeConverter.__init__(self, converter)
        self.parser = LC.Parser(converter._fromlang, 'default')
        self.err = 'on'
        self.exe = 'on'
        if 'py_error' in converter.defaults:
            self.err = converter.defaults['py_error']
        if 'py_exec' in converter.defaults:
            self.exe = converter.defaults['py_exec']
        self.err = self.err not in ['off', 'false', '0']
        self.exe = self.exe not in ['off', 'false', '0']
        self.num = 0

    def compile(self, node, dir_info, t_node, required):
        self.num += 1
        ctr = self.converter
        if not self.exe:
            return node
        ctr.exec_python(node, self.num, self.parser, self.err)


# pylint: disable=R0903
class BaseLog(object):
    """A simple class to provide messages to a converter. You must
    derive an object from this class in the module which will be
    issuing the messages. For instance::

        class Log(BaseLog):
            pass

    After that you can create a new object and use it in a module::

        log = Log(converter)

    where `converter` is a |Converter| provided to the module. Make
    sure that the module contains the objects ``MSG`` and
    ``MSG_EXPLANATION``."""

    def __init__(self, converter):
        self.converter = converter

    def msg(self, code, arg=None, uri=None):
        """Send a message to the converter. """
        self.converter.msg(self.__module__, code, None, arg, uri)


# The default of 7 attributes for class is too restrictive.
# pylint: disable=R0902
class Converter(object):
    """To see the languages available to the converter see the
    :mod:`lexor.command.lang` module. """

    def __init__(self, fromlang='lexor', tolang='html',
                 style='default', defaults=None,
                 parser_info=None):
        """Create a new converter by specifying the language and the
        style in which node objects will be written. Each converter
        also comes with a parser, you may specify the parser info
        by setting the parameter `parser_info` to a dictionary
        containing the keys `[lang, style, defaults]. By default the
        parser takes on the language the converter is converting from.
        """
        if defaults is None:
            defaults = dict()
        if parser_info is None:
            parser_info = {
                'lang': fromlang,
                'style': 'default',
                'defaults': None
            }
        self._fromlang = fromlang
        self._tolang = tolang
        self._style = style

        self._nc_container = None
        self._directives = None
        self._node_converters = None

        self._convert_func = None
        self._reload = True
        self.parser = LC.Parser(**parser_info)
        self.style_module = None
        self.doc = list()
        self.log = list()
        self.defaults = defaults
        self.abort = False
        self.packages = []
        self._post_process_list = []

    def __contains__(self, name):
        """Weather or not the Converter has a node converter of
        the given class name"""
        return name in self._node_converters

    def __getitem__(self, name):
        """Return the specified |NodeConverter|. """
        return self._node_converters[name].get(self)

    def has(self, directive):
        """Weather or not the Converter has a node converter
        registered with the specified directive"""
        return directive in self._directives

    def get(self, directive):
        """Return the node converter with the specified directive."""
        return self._directives[directive].get(self)

    @property
    def convert_from(self):
        """The language from which the converter will convert. """
        return self._fromlang

    @convert_from.setter
    def convert_from(self, value):
        """Setter function for convert_from. """
        if self._fromlang != value:
            self._fromlang = value
            self._reload = True

    @property
    def convert_to(self):
        """The language to which the converter will convert. """
        return self._tolang

    @convert_to.setter
    def convert_to(self, value):
        """Setter function for convert_to. """
        if self._tolang != value:
            self._tolang = value
            self._reload = True

    @property
    def converting_style(self):
        """The converter style. """
        return self._style

    @converting_style.setter
    def converting_style(self, value):
        """Setter function for converting_style. """
        if self._style != value:
            self._style = value
            self._reload = True

    @property
    def options(self):
        """The default settings for the current converting style. This
        is a dictionary mapping keys to strings or array of strings.

        This property is associated with attribute `defaults`.
        """
        return self.defaults

    @options.setter
    def options(self, value):
        """Setter function for defaults. """
        if value is None:
            value = {}
        if self.defaults is not value:
            self.defaults = value
            self._reload = True

    def set(self, fromlang, tolang, style, defaults=None):
        """Sets the languages and styles in one call. """
        self.convert_from = fromlang
        self.convert_to = tolang
        self.converting_style = style
        self.options = defaults
        self.parser.language = fromlang

    def match_info(self, fromlang, tolang, style, defaults=None):
        """Check to see if the converter main information matches.
        This may help us decide if we need to create another converter
        or use the current one if the main information is the one we
        need.

        NOTE: Currently the default values are not being compared
              this means that if defaults are provided to this method
              then it will return False.
        """
        match = True
        if defaults is not None:
            # TODO: Compare the default values
            match = False
        elif fromlang != self._fromlang:
            match = False
        elif tolang != self._tolang:
            match = False
        elif style != self._style:
            match = False
        return match

    @property
    def lexor_log(self):
        """The `lexorlog` document. See this document after each
        call to :meth:`convert` to see warnings and errors. """
        return self.log[-1]

    @property
    def document(self):
        """The current document. This is a |Document| or |DocFrag|
        created by the :meth:`convert` method.
        """
        return self.doc[-1]

    @property
    def root_document(self):
        """The root converted document. This is a |Document|created
        by the :meth:`convert` method.
        """
        return self.doc[0]

    def pop(self):
        """Remove the last document and last log document and return
        them. """
        return self.doc.pop(), self.log.pop()

    def convert(self, doc, namespace=False):
        """Convert the |Document| or |DocFrag| doc. """
        if not isinstance(doc, (LC.Document, LC.DocumentFragment)):
            raise TypeError('Document or DocumentFragment required')
        self._set_node_converters(
            self._fromlang,
            self._tolang,
            self._style,
            self.defaults
        )
        self.log.append(LC.Document('lexor', 'log'))
        self.log[-1].modules = dict()
        self.log[-1].explanation = dict()
        doccopy = doc.clone_node()
        doccopy.namespace = dict()
        self.doc.append(doccopy)
        if hasattr(self.style_module, 'pre_process'):
            self.style_module.pre_process(self, doccopy)
        for pkg in self.packages:
            self.load_package(pkg, doccopy)
        self._compile_doc(doc, doccopy)
        if not self.abort:
            self._link_doc(doccopy)
            if hasattr(self.style_module, 'post_process'):
                self.style_module.post_process(self, doccopy)
            for post_process in self._post_process_list:
                post_process(self, doccopy)
        map_explanations(
            self.log[-1].modules,
            self.log[-1].explanation
        )
        if not namespace:
            del self.doc[-1].namespace
        self.doc[-1].lang = self._tolang
        self.doc[-1].style = 'default'
        return doccopy, self.log[-1]

    @staticmethod
    def remove_node(node):
        """Removes the node from the current document it is in.
        Returns the previous sibling is possible, otherwise it
        returns the parent node.
        """
        parent = node.parent
        index = node.index
        del parent[index]
        if -1 < index < len(parent):
            return parent[index]
        return parent

    # pylint: disable=R0913
    def msg(self, mod_name, code, node, arg=None, uri=None):
        """Provide the name of module issuing the message, the `code`
        number, the node with the error, optional arguments and
        `uri`. This information gets stored in the converters log. """
        if uri is None:
            uri = self.doc[-1].uri_
        if arg is None:
            arg = ()
        wnode = LC.Void('msg')
        wnode['module'] = mod_name
        wnode['code'] = code
        wnode['node_id'] = id(node)
        wnode.node = node
        if node.node_position != (0, 0):
            wnode['position'] = node.node_position
        try:
            wnode['uri'] = node['uri']
            del node['uri']
        except (KeyError, TypeError):
            wnode['uri'] = uri
        wnode['arg'] = arg
        if mod_name not in self.log[-1].modules:
            self.log[-1].modules[mod_name] = sys.modules[mod_name]
        self.log[-1].append_child(wnode)

    def register(self, nc_class, override=False):
        """Add a node converter class. This function takes in a
        class object derived rom `Node Converter`.
        """
        L.info('- adding `%s`', nc_class)
        container = NCContainer(nc_class)
        class_name = nc_class.__name__
        if not override:
            if class_name in self._node_converters:
                msg = 'overriding existing node converter class {0}'
                raise LexorError(msg.format(class_name))
            if nc_class.directive in self._directives:
                msg = 'overriding existing node directive {0}'
                L.info("DIRECTIVES: %r", self._directives.keys())
                raise LexorError(msg.format(nc_class.directive))
        self._node_converters[class_name] = container
        self._directives[nc_class.directive] = container
        for alias in nc_class.directive_alias:
            self._directives[alias] = container
        return container

    @staticmethod
    def find_node_converters(mod):
        clazz = NodeConverter
        result = []
        for name in dir(mod):
            obj = getattr(mod, name)
            try:
                if (obj != clazz) and issubclass(obj, clazz):
                    result.append(obj)
            except TypeError:
                pass
        return result

    def _set_node_converters(self, fromlang, tolang, style, defaults):
        """Imports the correct module based on the languages and
        style. """
        if self._reload is False:
            return
        name = '%s-converter-%s-%s' % (fromlang, tolang, style)
        L.info('setting node converters for `%s`', name)
        mod = self.style_module = get_style_module(
            'converter', fromlang, style, tolang
        )
        config.set_style_cfg(self, name, defaults)
        self._directives = dict()
        self._node_converters = dict()
        self.register(PythonNC)
        try:
            repo = mod.REPOSITORY
            L.info('found REPOSITORY in converting style')
        except AttributeError:
            path = pth.dirname(mod.INFO['path'])
            L.info('searching for converters in %r', path)
            repo = []
            converters = self.find_node_converters(mod)
            repo.extend(converters)
            aux = load_aux(mod.INFO)
            for key in aux:
                aux_mod = aux[key]
                try:
                    repo.extend(aux_mod.REPOSITORY)
                except AttributeError:
                    converters = self.find_node_converters(aux_mod)
                    repo.extend(converters)
        for nc_class in repo:
            self.register(nc_class)
        self._reload = False

    def _pre_link_node(self, crt):
        if crt.zig is None:
            return crt
        directives = crt.zig.directives
        info = crt.zig.shared_info
        for directive, priority in directives:
            node_trans = self.get(directive)
            if node_trans._template is not None:
                t_node = node_trans._template.clone_node(True)
                transcluded_elements = LC.DocumentFragment()
                transcluded_elements.extend_children(crt)
                crt.extend_children(t_node)
                if node_trans.auto_transclude:
                    target = crt.get_nodes_by_name(
                        node_trans.auto_transclude, 1
                    )[0]
                    target.append_nodes_after(transcluded_elements)
                    del target.parent[target.index]
                transcluded_elements = None
            else:
                transcluded_elements = None
            require = crt.zig.requirements[directive]
            node_trans.pre_link(crt, info, transcluded_elements, require)
        if info['replace']:
            crt.append_nodes_after(crt)
            new_crt = crt.next
            del crt.parent[crt.index]
            crt = new_crt
        return crt

    def _post_link_node(self, crt):
        if crt.zig is None:
            return crt
        directives = crt.zig.directives
        info = crt.zig.shared_info
        for directive, priority in reversed(directives):
            node_trans = self.get(directive)
            if node_trans._template is not None:
                t_node = node_trans._template.clone_node(True)
                transcluded_elements = LC.DocumentFragment()
                transcluded_elements.extend_children(crt)
                crt.extend_children(t_node)
                if node_trans.auto_transclude:
                    target = crt.get_nodes_by_name(
                        node_trans.auto_transclude, 1
                    )[0]
                    target.append_nodes_after(transcluded_elements)
                    del target.parent[target.index]
                transcluded_elements = None
            else:
                transcluded_elements = None
            require = crt.zig.requirements[directive]
            node_trans.post_link(crt, info, transcluded_elements, require)
        # TODO: replace?

    def _compile_node(self, clone):
        directives = clone.zig.directives
        info = clone.zig.shared_info
        for directive, priority in directives:
            node_trans = self.get(directive)
            if node_trans._template is None:
                if node_trans.template is not None:
                    # TODO: Adapt errors
                    if node_trans.template_parser is not None:
                        settings = node_trans.template_parser
                        self.parser.set(
                            settings['lang'],
                            settings['style'],
                            settings['defaults']
                        )
                    self.parser.parse(node_trans.template)
                    parser_doc = self.parser.doc
                    compiled_doc = parser_doc.clone_node()
                    self._compile_doc(parser_doc, compiled_doc)
                    node_trans._template = compiled_doc
                    tdoc = node_trans._template.clone_node(True)
                else:
                    tdoc = None
            else:
                tdoc = node_trans._template.clone_node(True)
            try:
                require = clone.zig.store_requirements(directive)
            except LexorError as exp:
                self.abort = exp
                return self.msg(
                    self.__module__, 'E200', clone, [
                        LC.encode_requirement(exp.data['req']),
                        directive
                    ]
                )
            node_trans.compile(clone, info, tdoc, require)
            # TODO: store tdoc in the clone zig, this will be used later

    def compile(self, node):
        """

        """
        root = node
        crt = root
        while True:
            zig = LC.Zig(self, crt)
            zig.get_directives()
            self._compile_node(crt)
            crt = self._remove_node_after('compile', crt)
            if crt.child:
                crt = crt[0]
            else:
                while crt.next is None:
                    if crt is root:
                        return root
                    crt = crt.parent
                crt = crt.next

    def _compile_doc(self, doc, doccopy):
        """Creates a copy of the document and calls the compile
        method on each of the template elements (if any).
        """
        root = doc
        crt = root
        crtcopy = doccopy
        if not crt.child:
            zig = LC.Zig(self, doccopy)
            zig.get_directives()
            self._compile_node(doccopy)
            return doccopy
        crt = crt[0]
        while True:
            clone = crt.clone_node()
            crtcopy.append_child(clone)
            zig = LC.Zig(self, clone)
            zig.get_directives()
            info = zig.shared_info
            self._compile_node(clone)
            if self.abort:
                return
            remove = info['remove']
            remove_children = info['remove_children']
            if remove and info['remove_after'] == 'compile':
                del crtcopy[clone.index]
                clone = None
            if (clone is not None and
                    not remove_children and crt.child):
                crtcopy = clone
                crt = crt[0]
            else:
                while crt.next is None:
                    crt = crt.parent
                    if crt is root:
                        return doccopy
                    crtcopy = crtcopy.parent
                    crtcopy.normalize(recurse=False)
                crt = crt.next

    def _link_doc(self, doccopy):
        """To be run after compiling the document.
        """
        root = doccopy
        crt = root
        while True:
            node_ref = self._pre_link_node(crt)
            while node_ref is not crt:
                crt = node_ref
                node_ref = self._pre_link_node(crt)
            crt = self._remove_node_after('pre_link', crt)
            if crt.child:
                crt = crt[0]
            else:
                self._post_link_node(crt)
                crt = self._remove_node_after('post_link', crt)
                while crt.next is None:
                    if crt is root:
                        return root
                    crt = crt.parent
                    self._post_link_node(crt)
                    crt = self._remove_node_after('post_link', crt)
                crt = crt.next

    def _remove_node_after(self, phase, node):
        if node.zig is not None:
            info = node.zig.shared_info
            remove = info['remove']
            if remove and info['remove_after'] == phase:
                node = self.remove_node(node)
        return node

    def update_log(self, log, after=True):
        """Append the messages from a `log` document to the
        converters log. This removes the children from `log`. """
        modules = log.modules
        explanation = log.explanation
        for mname in modules:
            if mname not in self.log[-1].modules:
                self.log[-1].modules[mname] = modules[mname]
            if mname not in self.log[-1].explanation:
                self.log[-1].explanation[mname] = explanation[mname]
        if after:
            self.log[-1].extend_children(log)
        else:
            self.log[-1].extend_before(0, log)

    def load_module(self, src):
        """Load the module specified by src. """
        name = pth.basename(src)
        name = pth.splitext(name)[0]
        if src[0] != '/':
            base = pth.dirname(self.doc[-1].uri_)
            if base != '':
                base += '/'
            path = '%s%s' % (base, src)
        else:
            path = src
        if not path.endswith('.py'):
            path += '.py'
        try:
            return load_source('lexor-package_%s' % name, path)
        except IOError:
            try:
                lexorinputs = os.environ['LEXORINPUTS']
            except KeyError:
                raise ImportError
            for directory in lexorinputs.split(':'):
                path = '%s/%s.py' % (directory, name)
                if pth.exists(path):
                    modname = 'lexor-package_%s' % name
                    return load_source(modname, path)
            raise ImportError

    def load_package(self, name, node):
        """Load a lexor package. """
        try:
            mod = self.load_module(name)
        except ImportError:
            return self.msg(self.__module__, 'E404', node, [name])
        try:
            repo = mod.REPOSITORY
        except AttributeError:
            repo = self.find_node_converters(mod)
        if hasattr(mod, 'post_process'):
            self._post_process_list.append(mod.post_process)
        for nc_class in repo:
            self.register(nc_class)

    # pylint: disable=W0122,E1103
    def exec_python(self, node, id_num, parser, error=True):
        """Executes the contents of the |PI| node. You must provide
        an id number identifying the processing instruction and a
        |Parser| that will parse the output provided by the
        execution. If `error` is True then any errors generated
        during the execution will be appended to the output of the
        document."""
        get_current_node.current.append(node)
        include.converter.append(self)
        namespace = get_lexor_namespace()
        if '__NAMESPACE__' not in namespace:
            namespace['__NAMESPACE__'] = namespace
            namespace['import_module'] = import_module
            namespace['include'] = include
            namespace['echo'] = echo
        namespace['__FILE__'] = pth.realpath(self.doc[-1].uri)
        namespace['__DIR__'] = pth.dirname(namespace['__FILE__'])
        namespace['__NODE__'] = get_current_node()
        namespace['__CONVERTER__'] = self
        original_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            exec(node.code, namespace)
        except BaseException:
            self.msg(self.__module__, 'E100', node, [id_num])
            if error:
                err_node = LC.Element('python_pi_error')
                err_node.set_position(*node.node_position)
                err_node['section'] = str(id_num)
                err_node.append_child(
                    LC.CData(traceback.format_exc())
                )
                node.parent.insert_before(node.index, err_node)
        text = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = original_stdout
        parser.parse(text)

        compiled_doc = parser.doc.clone_node()
        self._compile_doc(parser.doc, compiled_doc)

        node.parent.extend_before(node.index, compiled_doc)
        newnode = Converter.remove_node(node)
        if parser.log:
            self.msg(self.__module__, 'W101', node, [id_num])
            self.update_log(parser.log)
            self.msg(self.__module__, 'W102', node, [id_num])
        get_current_node.current.pop()
        include.converter.pop()
        if include.converter:
            doc = include.converter[-1].doc[-1]
            namespace['__FILE__'] = pth.realpath(doc.uri)
            namespace['__DIR__'] = pth.dirname(namespace['__FILE__'])
            namespace['__NODE__'] = get_current_node()
            namespace['__CONVERTER__'] = get_converter()
        else:
            namespace['__FILE__'] = None
            namespace['__DIR__'] = None
            namespace['__NODE__'] = None
            namespace['__CONVERTER__'] = None
        return newnode


def get_lexor_namespace():
    """The execution of python instructions take place in the
    namespace provided by this function."""
    return get_lexor_namespace.namespace
if not hasattr(get_lexor_namespace, 'namespace'):
    get_lexor_namespace.namespace = dict()


def get_current_node():
    """Return the document node containing the python embeddings
    currently being executed.
    """
    return get_current_node.current[-1]
if not hasattr(get_current_node, 'current'):
    get_current_node.current = list()


def echo(node):
    """Allows the insertion of Nodes generated within python
    embeddings::

        <?python
        comment = PI('!--', 'This is a comment')
        echo(comment)
        ?>

    """
    crt = get_current_node()
    if isinstance(node, str):
        crt.parent.insert_before(crt.index, LC.Text(node))
    elif isinstance(node, LC.Node):
        if node.name == '#document':
            crt.parent.extend_before(crt.index, node)
            return
        crt.parent.insert_before(crt.index, node)
    elif isinstance(node, list):
        for item in node:
            echo(item)
    else:
        while node:
            echo(node[0])


def get_converter():
    """Return the current converter being used to execute the python
    embeddings.
    """
    return include.converter[-1]


def include(input_file, **keywords):
    """Inserts a file into the current node. Absolute paths may be
    provided as well as relative. When using relative paths the files
    are found relative to the path of the calling document. You may
    use the following keywords:
    
    - parser_style: ``'default'``
    - parser_lang: ``None``
    - parser_defaults: ``None``,
    - convert_style: ``'default'``,
    - convert_from: ``None``,
    - convert_to: ``None``,
    - convert_defaults: ``None``,
    - adopt: ``'true'``
    
    If the keyword ``adopt`` is set to false then a |Document| node
    will be inserted."""
    trans = include.converter[-1]
    if input_file[0] != '/':
        input_file = pth.join(pth.dirname(trans.doc[-1].uri),
                              input_file)
    info = {
        'parser_style': 'default',
        'parser_lang': None,
        'parser_defaults': None,
        'convert_style': 'default',
        'convert_from': None,
        'convert_to': None,
        'convert_defaults': None,
        'adopt': True,
    }
    for key in keywords:
        info[key] = keywords[key]
    if info['parser_lang'] is None:
        path = pth.realpath(input_file)
        name = pth.basename(path)
        name = pth.splitext(name)
        info['parser_lang'] = name[1][1:]
    with open(input_file) as tmpf:
        text = tmpf.read()
    parser = LC.Parser(info['parser_lang'],
                       info['parser_style'],
                       info['parser_defaults'])
    parser.parse(text, input_file)
    if parser.log:
        trans.update_log(parser.log)
    crt = get_current_node()
    if info['convert_to'] is not None:
        if info['convert_from'] is None:
            info['convert_from'] = info['parser_lang']
        converter = Converter(info['convert_from'],
                              info['convert_to'],
                              info['convert_style'],
                              info['convert_defaults'])
        converter.convert(parser.doc)
        if converter.log:
            trans.update_log(converter.log)
        doc = converter.document
    else:
        doc = parser.doc
    if info['adopt']:
        crt.parent.extend_before(crt.index, doc)
    else:
        crt.parent.insert_before(crt.index, doc)
if not hasattr(include, 'converter'):
    include.converter = list()


def import_module(mod_path, mod_name=None):
    """Return a module from a path. If no name is provided then the
    name of the file loaded will be assigned to the name. When using
    relative paths, it will find the module relative to the file
    executing the python embedding. """
    doc = include.converter[-1].doc[-1]
    if not mod_path.endswith('.py'):
        mod_path += '.py'
    if mod_path[0] != '/':
        mod_path = pth.join(pth.dirname(doc.uri), mod_path)
    if mod_name is None:
        mod_name = pth.basename(mod_path)
    if mod_name.endswith('.py'):
        mod_name = mod_name[:-3]
    return load_source(mod_name, mod_path)


MSG = {
    'E100': 'errors in python processing instruction section `{0}`',
    'W101': '--> begin ?python section `{0}` messages',
    'W102': '--> end ?python section `{0}` messages',
    'E200': 'failed to find the requirement `{0}` for `{1}`',
    'E404': 'package `{0}` not found',
}
MSG_EXPLANATION = [
    """
    - This message is being shown because of E100.

    - The python processing instructions has mistakes. See the
      traceback generated to fix the errors.

    - If the traceback is not shown in the document it may be
      due to the option `error` being off.

""",
    """
    - Some directives are required to be declared on the same node
      or parent nodes in order for a directive to work.

    - E200 informs us when a requirement has failed and the directive
      cannot proceed unless the requirement is met.

    - Note that when this error is reported, the compile phase is
      stopped and the converting process comes to a halt. We
      may use the writing style `lexor:repr` to see the element
      that caused the error since this element will be the last one
      in the document.

""",
    """
    - A "lexor" package is a python script which declares one or
      several node converters and optionally a post_process
      function.

    - If the package is not found in the same directory as the
      document or some relative location to the document then it
      searches in each of the paths declared by the environment
      variable `LEXORINPUTS`.

    Reports error E404.

""",
]
