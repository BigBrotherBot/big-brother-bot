Miscellaneous
=============


.. _duration-syntax:
.. index:: duration syntax

Duration syntax
---------------

Many plugin settings need to express durations. For this purpose, B3 provides a convenient syntax using a suffix for
expressing different duration units :

s
  second *i.e.:* ``45s``

m
  minute *i.e.:* ``5m``

h
  hour *i.e.:* ``1h``

d
  day *i.e.:* ``7d``

w
  week *i.e.:* ``4w``

For example, let's say you want to ban player Joe for 1 week with reason '*insult other players*', you would use the
command :

:command:`!ban joe 1w insult other players`



.. _targeting-player-syntax:
.. index:: player identification

Player identification in commands
---------------------------------

Commands that accept player designations can use several types of input.


Partial Name
^^^^^^^^^^^^

  The simplest player identifier is the players name. You can use any part of the player name. Only enough characters
  to match the players name uniquely is needed. If more than one player on the server has a similar name, you will be
  prompted with all players matching that name and their client id.

  Example:
    :command:`!warn sam cuss` for giving a warning to a connected player named 'Samuel'

  .. note::
     You can use the :ref:`find` command to show which connected players match a given name.

  .. note::
     If the player's name contains blank characters as in ``M I K E``, then you can use its name without the blanks:
     :command:`!kick mike`

     Another solution is to wrap single quotes (``'``) around the name: :command:`!kick 'm i k e'`



Client ID
^^^^^^^^^

  The client ID is the number assigned to the player by the game server. The client ID only works for the current
  gaming session. For a list of players' client IDs, use the !list command. If a players name is too hard to type
  or there are more than one players with similar names, you can use the client id to single them out.

  Example:
    :command:`!kick 3 tk` to kick a player connected on game slot number 3



Database ID
^^^^^^^^^^^

  The Database ID is the players unique identification within the B3 database. It is prepended with an ”@” and is often
  referred to as the “at ID”. This ID is displayed with the :ref:`leveltest` command and the :ref:`lookup` command. You can use
  this ID to perform actions against a player even when that player is not connected.

  Example:
    :command:`!makereg @1235`

.. note::
  You can use the :ref:`lookup` command to find offline users in the database and get their database ID.



.. _mysql-tools:
.. index:: mysql tools

MySQL tools
-----------

The following tools facilitate the use and administration of a MySQL database.
Probably you have already installed one of these tools.

        - `Adminer`_
        - `phpMyAdmin`_
        - `MySQL Workbench`_


.. _`Adminer`: http://www.adminer.org/
.. _`phpMyAdmin`: http://www.adminer.org/de/
.. _`MySQL Workbench`: http://dev.mysql.com/downloads/tools/workbench/
