.. _guide-warning:
.. index:: warning system

==============
Warning System
==============

.. _warning-basics:

Basics
------

The warning system allows to design an easy to use set of rules.
Warnings are issued for breaking of the rules. B3 will automatically enforce
harsh penalties if a limit of maximum warnings was exceeded.

Warnings are awarded automatically based on rules and manually by authorized players.
The censorship plugin for example cautioned player automatically when they use
an inappropriate language in chat.
In another case, a moderator can warn a player for unfair play - example camp.

Automatic Warnings
------------------

Automatic warnings are carried out by the plugins.
In general, the message, the warning time and the punishment can be configured.

.. note::
    The configuration may vary and is documented in the manual of the plugin.

Manual Warnings
---------------

Manual warnings can be given by authorized players like moderators and
are handled by the :ref:`admin plugin <plugin-admin>`.

A player may be warned with the following command:

::

   !warn PlayerName camp

The player would receive the following warning:
  *WARNING (1): PlayerName stop camping or you will be kicked!*

.. tip::
    The warning system can make use of pre-configured rules and their abbreviations.

Useful Commands:
    - :command:`!clear` *<player>* - Clears active warnings and tk points for the player identified by *<player>*

The :ref:`admin plugin <plugin-admin>` comes with a variety of configured warnings.
The configuration is made in the file :file:`admin_plugin.xml`.


.. todo::
    show configuration example
    explain more useful commands

