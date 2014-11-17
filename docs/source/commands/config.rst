.. _config:

*************
lexor config
*************

Lexor depends on the user configuration files. The files can be
edited manually or by using the config command.

To see which configuration file lexor uses you may use the config
command along with the ``--display`` option::

    $ lexor config --display
    lexor configuration file: /Users/jmlopez-rod/.lexor.config

The command above only displayed the path to the configuration file
since the file must likely is empty or does not exist yet.

User Configuration File
-----------------------

Lexor will attempt to look for the file ``lexor.config`` in the
current working directory. If this fails then it will default to the
user configuration file ``.lexor.config``.

For instance, if our current working directory is ``~/Desktop`` and the
file ``~/Desktop/lexor.config`` does not exist then we may modify the
user configuration file as follows::

    $ pwd
    /Users/jmlopez-rod/Desktop
    $ lexor config sec.var val
    $ lexor config --display
    lexor configuration file: /Users/jmlopez-rod/.lexor.config
    [sec]
    var = val

If we only wish to view a single value::

    $ lexor config sec.var
    val

Lexor Configuration File
------------------------

We can use a different configuration by using the ``--cfg`` option::

    $ lexor --cfg ~/Documents config --display
    ERROR: /Users/jmlopez-rod/Documents/lexor.config does not exist.

Here we see an error because we attempted to use a configuration file
in a path which did not have the ``lexor.config`` file. We must first
create the file::

    $ touch ~/Documents/lexor.config
    $ lexor --cfg ~/Documents config --display
    lexor configuration file: /Users/jmlopez-rod/Documents/lexor.config

If our current directory contains a configuration file and we wish to
use our user configuration then we may use the ``--cfg-user`` option::

    $ cd ~/Documents
    $ lexor config --display
    lexor configuration file: ./lexor.config
    $ lexor --cfg-user config --display
    lexor configuration file: /Users/jmlopez-rod/.lexor.config
    [sec]
    var = val

Format
------

The configuration file consists of sections, variables and values

.. code-block:: ini

    [sec1]
    var1 = val1
    var2 = val2
    
    [sec1]
    var1 = val1
    var2 = val2


The sections may be names of commands or languages. For instance the
``edit`` command has two defaults that can modify::

    $ lexor defaults edit
    path = '.'
    editor = '$EDITOR'

To modify these defaults we may write the following in the
configuration file

.. code-block:: ini

    [edit]
    path = path/relative/to/configuration/file
    editor = emacs

You may specify more than one path by separating them with a colon
(``:``). By default "editor" is set to the environmental variable
``$EDITOR`` so that each user may specify its favorite editor (emacs,
vim, mate). If a command or style has a ``DEFAULTS`` variable then
you may overwrite those variables via the configuration file.
