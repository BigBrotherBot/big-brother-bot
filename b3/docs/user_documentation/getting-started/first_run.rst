.. _getting-started:

First run
=========

This document describes the preparations and the first start of B3.
You'll need the following:

- Database
- Access to your game server

.. index:: database, mysql

Database Setup
--------------

B3 currently only supports MySQL and SQLite databases.
We recommend the use of MySQL. For small installations SQLite may be sufficient.
If you want to use SQLite, then once is nothing more to do.

1. Create a new MySQL database for B3 (see :ref:`mysql-tools`)

2. Import the table structure
    On the database you just created,
    import the :file:`b3.sql` file located in b3/docs/ to create the tables and insert
    the initial values in your database.

    Use your favorite database management tool again or the following command.

    .. code-block:: bash

        mysql -u root -p<mysql password> b3 b3.sql


Configuration
-------------

B3 main config file is called b3.xml by default.
If you run the bot straight away, it will detect you did not properly setup the
main config file and will walk through a config wizard where each setting is
prompted with a short description.

Alternatively, you can use our `online configuration generator`_.

Detailed configuration options can be found in the manual.
For game-specific configuration and alternative scenarios visit to our `forums`_.

.. _`online configuration generator`: http://config.bigbrotherbot.net/
.. _`forums`: http://forum.bigbrotherbot.net/configurations/

Running B3
----------

You can run B3 from the command line when you've installed it as a source install or python egg.

.. code-block:: bash

    python ./b3_run.py

Windows users who use the binary package, will find a shortcut.

With command line parameters can influence the behavior of B3.
An overview of all parameters can be found in the manual.

Become Super Admin
------------------

After successfully installing and configuring your B3 bot you'll start B3 for
the first time. B3 will check if there are any SuperAdmins in your database.
If not, B3 will enable the !iamgod command for the first player typing it in game.

So, it is wise to go in game immediately after starting B3 and
typing :command:`!iamgod` in chat, it will register you as the SuperAdmin and
disable the :command:`!iamgod` command.
