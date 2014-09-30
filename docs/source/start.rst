.. _start:

***************
Getting Started
***************

As a simple example we will use the HTML language::

    lexor install html

Consider the file ``example.html``

.. code-block:: html

    <!DOCTYPE html>
    <html>
        <head>
            <title>Example</title>
    </head>
        <body>
                <h1>Example</h1>
                <p>
                    This is an example
                
                    </p>
            </body>
    </html>

Now we can rewrite this file into three different versions::

    lexor example.html html~plain,min,_~ -wn

The ``-w`` option writes the output to a file by appending the
specified style. The ``-n`` suppress the output in the terminal.

The following are the files written:

**example.default.html**:

.. code-block:: html

    <!DOCTYPE html>
    <html>
    <head>
    <title>Example</title>
    </head>
    <body>
    <h1>Example</h1>
    <p> This is an example </p>
    </body>
    </html>

**example.plain.html**:

.. code-block:: html

    <!DOCTYPE html>
    <html>
        <head>
            <title>Example</title>
    </head>
        <body>
                <h1>Example</h1>
                <p>
                    This is an example
                
                    </p>
            </body>


**example.min.html**:

.. code-block:: html

    <!DOCTYPE html><html><head><title>Example</title></head><body><h1>Example</h1><p> This is an example </p></body></html>

For more information on how to transform files see the lexor command
``to``.
