.. _guide-groups:
.. index:: groups, levels

=====================
User Roles and Groups
=====================

Basics
------

B3's permissions are based on groups and levels.
Users are assigned to groups and each group has a level. Commands can be ran by
users that have the minimum level needed to use the command.

Most commands for user and group management provided by the :ref:`admin plugin <plugin-admin>`.

.. _groups:

B3 Groups
---------

B3 has several default user groups, each serving a different purpose.

=====  ===========  ===========
Level  Group        description
=====  ===========  ===========
100    superadmin   The **Super Admin** is the highest level of authority. |br|\ A Super Admin has access to all commands and is generally only assigned to the server owner.
80     senioradmin  **Senior Admins** are the highest admins. |br|\ They have access to most commands except for the commands used in server/bot setup.
60     fulladmin    **Full admins** have less authority than Senior Admins but still have access to harsher punishment commands such as !ban.
40     admin        **Admins** are the first level of administrators. Their harshest punishment is a !kick, yet they are probably the most numerous of the admins.
20     mod          **Moderators** are the first step to becoming an admin, an admin training ground if you will. They can only !warn users or remind them of the rules. They can notify higher level admins when harsher punishment is needed.
2      reg          **Regulars** are not admins or moderators, but your loyal server population. |br|\ You would only give regular status to members of your community.
1      user         A **user** is like a self appointed regular. |br|\ New players can use the !register command to gain user status. User's have only a few commands but gain extra privelages that would be ignored for the one-time visit players.
=====  ===========  ===========

.. |br| raw:: html

   <br />

.. warning::

   Plugins rely on these default groups. Do not remove these groups.

user Management
---------------

Users can be moved in groups by privileged users (eg admins)
with the :command:`!putgroup` command.
The prerequisite is that the user is registered.

Useful Commands:
    - :command:`!register` - register yourself as a basic user
    - :command:`!makereg` <:ref:`player <targeting-player-syntax>`> - Used by admins to add a user to the regular group
    - :command:`!unreg` <:ref:`player <targeting-player-syntax>`> - Used by admins to remove a user from the regular group
    - :command:`!putgroup` <:ref:`player <targeting-player-syntax>`> <:ref:`group <groups>`> - Used by admins to add a user to a group
    - :command:`!ungroup` <:ref:`player <targeting-player-syntax>`> <:ref:`group <groups>`> - Used by admins to remove a client to a group

The following example would move PlayerA into the moderators group.

::

   !putgroup playerA mod

Users can only be a member of one group.

group Permissions
-----------------

Group permissions regulate which command may be executed.
Each plugin (core plugins or 3rd party plugins) comes with a config file
where you can set levels belonging to the commands.

The following example would allow users with level 1 to use the !time command.::

    <set name="time">1</set>

If you don't want level 1 users to be able to use the command,
but you want regulars (level 2) and up to be able to use it, change it to::

    <set name="time">2</set>

You can set a range for the usage of the commands.::

    <set name="time">20-40</set>

This will give the right to use the !time command only to moderators up to admins,
but no below or above privileges can possibly use this command.

.. note::
   Changes to the configuration file require a restart or reread the configuration files.
