"""
The core of lexor is divided among the modules in this package.

:|node|:
    Provides the most basic structure to create the document object
    model (DOM).

:|elements|:
    Here we define the basic structures to handle the information
    provided in files. Make sure to familiarize yourself with all the
    objects in this module to be able to write extensions for the
    |Parser|, |Converter| and |Writer|.

:|parser|:
    The parser module provides the |Parser| and the abstract class
    |NodeParser| which helps us write derived objects for future
    languages to parse.

:|converter|:
    The converter module provides the |Converter| and the abstract
    class |NodeConverter| which helps us copy a |Document| we
    want to convert to another language.

:|writer|:
    The writer module provides the |Writer| and the abstract class
    |NodeWriter| which once subclassed help us tell the |Writer|
    how to write a |Node| to a file object.


.. |node| replace:: :mod:`~lexor.core.node`
.. |Node| replace:: :mod:`~lexor.core.node.Node`
.. |elements| replace:: :mod:`~lexor.core.elements`
.. |Document| replace:: :mod:`~lexor.core.elements.Document`
.. |parser| replace:: :mod:`~lexor.core.parser`
.. |Parser| replace:: :mod:`~lexor.core.parser.Parser`
.. |NodeParser| replace:: :mod:`~lexor.core.parser.NodeParser`
.. |converter| replace:: :mod:`~lexor.core.converter`
.. |Converter| replace:: :mod:`~lexor.core.converter.Converter`
.. |NodeConverter| replace:: :mod:`~lexor.core.converter.NodeConverter`
.. |writer| replace:: :mod:`~lexor.core.writer`
.. |Writer| replace:: :mod:`~lexor.core.writer.Writer`
.. |NodeWriter| replace:: :mod:`~lexor.core.writer.NodeWriter`

"""

from lexor.core.node import Node
from lexor.core.elements import (
    CharacterData,
    Text,
    ProcessingInstruction,
    Comment,
    CData,
    Entity,
    DocumentType,
    Element,
    RawText,
    Void,
    Document,
    DocumentFragment,
)
from lexor.core.parser import (
    NodeParser,
    Parser,
)
from lexor.core.writer import (
    NodeWriter,
    Writer,
    replace,
)
from lexor.core.converter import (
    BaseLog,
    NodeConverter,
    Converter,
    get_converter_namespace,
)
from lexor.core.selector import Selector
