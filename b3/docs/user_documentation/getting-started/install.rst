=============
Installing B3
=============

There are several types of installation available.
For Windows users the binary packages are recommended.
Developers and Unix users can use the Python standard tools.

Windows binaries
----------------
This package is a MS windows installer package that has an included
python interpreter for windows. You do not need to install Python.

Current packages of the stable version can downloaded in the `forum`_ or on `SourceForge`_.

Just run the installer and follow the instructions.

Some developers offer `daily builds`_ based on latest development code.

.. note::
    Daily builds are not officially supported. If you have problems, please try to use the stable version of B3.

    If you find a bug in such a build, please report the bug with as much details on how to reproduce it in
    the `forum`_.

.. _`forum`: http://forum.bigbrotherbot.net/downloads/?cat=10
.. _`SourceForge`: http://sourceforge.net/projects/bigbrotherbot/files/
.. _`daily builds`: http://files.cucurb.net/b3/daily/

Python .egg and source code package
-----------------------------------

If you have :mod:`distribute` installed, the easiest way of getting B3 is
to simply use :command:`easy_install`:

.. code-block:: bash

    $ easy_install b3

If you have downloaded a source tarball you can install it
by doing the following:

.. code-block:: bash

    $ python setup.py build
    # python setup.py install # as root

That's it.

The development version
-----------------------

It is also possible to install the development version of B3 from our
`Git <http://git-scm.com/>`_ source code repository. To do this you will
need to have Git installed on your system. Then just do:

.. code-block:: bash

    $ git clone https://github.com/BigBrotherBot/big-brother-bot.git
    $ cd big-brother-bot
    $ python setup.py install

