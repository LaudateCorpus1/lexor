"""
The core of lexor is divided among the modules in this package.

:`node <lexor.core.node>`_:
    Provides the most basic structure to create the document object
    model (DOM).

:`elements <lexor.core.elements>`_:
    Here we define the basic structures to handle the information
    provided in files. Make sure to familiarize yourself with all the
    objects in this module to be able to write extensions for the
    ``Parser``, ``Converter`` and ``Writer``.

:parser:
    The parser module provides the ``Parser`` and the abstract class
    ``NodeParser`` which helps us write derived objects for future
    languages to parse.

:converter:
    The converter module provides the ``Converter`` and the abstract
    class ``NodeConverter`` which helps us copy a ``Document`` we
    want to convert to another language.

:writer:
    The writer module provides the ``Writer`` and the abstract class
    ``NodeWriter`` which once subclassed help us tell the ``Writer``
    how to write a ``Node`` to a file object.

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
