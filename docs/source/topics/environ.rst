.. _environ:

**********************
Enviromental Variables
**********************

There are several environmental variables that lexor may use. Here
you will find the names of these variables as well as a references to
functions or commands that makes use of them.

``LEXOR_CONFIG_PATH``
=====================

This variable should be a single path specifying the location of the
file ``lexor.config``. It is used by
:func:`lexor.command.config.read_config`.

This is variable may be useful when working in a project for extended
periods of time. By specifying this variable we do not have to use
the option ``--cfg`` every time we wish to use the projects
configuration.

One suggestion to use this variable in a project is to have a ``bashrc`` file
inside the project in which you export this variable

.. code-block:: bash

    export BASH_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    export LEXOR_CONFIG_PATH=$BASH_ROOT/path/to/lexor.config

Then ``source`` the bashrc file.

.. code-block:: bash

    cd path/to/project
    source bashrc
    echo $LEXOR_CONFIG_PATH
