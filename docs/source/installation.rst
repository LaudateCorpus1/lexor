.. _installation:

****************
Installing Lexor
****************

Pip or Manual Installation
==========================

The easiest way to install lexor is to use ``pip``. If you wish
to perform a global installation and you have admin rights then do

.. code-block:: sh

    sudo pip install lexor

or to install in some directory under your user account

.. code-block:: sh

    pip install --user lexor

Or if you prefer to do do a manual installation then you may do the
following from the command line (where x.y is the version number):

.. code-block:: sh

    wget https://pypi.python.org/packages/source/l/lexor/lexor-x.y.tar.gz
    tar xvzf lexor-x.y.tar.gz
    cd lexor-x.y/
    sudo python setup.py install

The last command can be replaced by ``python setup.py install
--user``. See `PyPI <https://pypi.python.org/pypi/lexor/>`_ for
all available versions.


Lexor Languages
===============

The basic lexor installation does not provide any parsers, converters
or writers. You must install them manually using the ``install``
lexor command.

.. code-block:: sh

    lexor install <language>

To see the available languages see
`http://jmlopez-rod.github.io/lexor-lang/
<http://jmlopez-rod.github.io/lexor-lang/>`_.
