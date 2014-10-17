.. _lexor:

What is Lexor?
==============

Lexor provides a platform where we can specify how a document is
parsed, converted and written. It is an expandable Python package
which aims to provide functionality to deal with any text file.

Motivation
----------

Lexor started as a simple HTML file parser which later evolved into a
markdown parser. The first versions took inspiration on
`Python-Markdown`_. However, the need to modify and extend the
functionality led us to find `Pandoc`_.

Today, lexor aims to behave similary to Pandoc, in the sense that it
converts documents but it does so to meet the users preferences. For
instance, we may want to write an HTML file in a minified form, that
is, seeing as spaces and new lines do not matter in almost all HTML
tags we could write an HTML in a single line, provided that there are
no script or other special tags. Or perhaps we want to let Lexor write
it in a different style. Lexor attempts to emulate Pandoc in Python.
We should note that Pandoc is written in `Haskell`_ and although
Pandoc already has lots of document converters, Lexor brings potential
for Python users to create their own tools for processing files in a
simplified manner.

.. _`Python-Markdown`: https://pythonhosted.org/Markdown/
.. _`Pandoc`: http://johnmacfarlane.net/pandoc/
.. _`Haskell`: http://www.haskell.org/haskellwiki/Haskell
