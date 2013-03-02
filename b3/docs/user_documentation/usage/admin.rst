The Admin plugin
================

The admin plugin is at the heart of BigBrotherBot. It brings to B3 the user groups and in-game commands.

It allows the gameserver owner to define his staff by assigning trusted players to the different administration groups.
Depending on their group membership, players will be given access to administrating commands which allow them to:

- display the server rules
- warn a user
- kick
- ban
- change map
- change the gamemode
- etc

.. _groups:

Groups and levels
-----------------

B3's permissions are based on groups and levels. Players are assigned to groups and each group has a level. Commands can
be run by users that have the minimum level needed to use the command.

B3 has 8 user groups, each serving a different purpose. Several commands are available to assign players to group :

- register
- makereg
- unreg
- putgroup
- ungroup

guest / level 0
~~~~~~~~~~~~~~~

This is a default group for any player joining your gameserver who is not member of any other group.

user / level 1
~~~~~~~~~~~~~~

Players of group *Users* are self appointed regulars. New players can use the :command:`!register` command to gain user
status.
User's have only a few commands but gain extra privileges that would be ignored for the one-time visit players.

reg / level 2
~~~~~~~~~~~~~

*Regulars* are not admins or moderators, but your loyal server population. You would only give
regular status to members of your community who follow the rules and play on your server often. *Regulars* not only get
a status symbol, but access to a few more commands than the average user. By default, only *Senior Admins* and up can
appoint regulars with the :command:`!makereg` command.

mod / level 20
~~~~~~~~~~~~~~

The *Moderators* group is meant for regular players who earned the trust of the gameserver admins. They know and agree
with the gameserver rules and are given a few commands to help the admin staff educate other players in regards with the
gameserver rules. They are the first step to becoming an admin, an admin training ground if you will. They can only
:command:`!warn` users or remind them of the rules. They can notify higher level admins when harsher punishment is
needed.

admin / level 40
~~~~~~~~~~~~~~~~

*Admins* are the first level of administrators. Their harshest punishment is a :command:`!kick`, yet they are probably
the most numerous of the admins.

fulladmin / level 60
~~~~~~~~~~~~~~~~~~~~

*Full Admins* have less authority than *Senior Admins* but still have access to harsher punishment commands such as
:command:`!ban`.

senioradmin / level 80
~~~~~~~~~~~~~~~~~~~~~~

*Senior Admins* are usually the highest admins that play and admin on the server often. They have access to most
commands except for the commands used in server/bot setup. Choose your *Senior Admins* wisely for they have the full
regiment of commands to enforce your server policy.

superadmin / level 100
~~~~~~~~~~~~~~~~~~~~~~

The *Super Admin* is the highest level of authority. A *Super Admin* has access to all commands and is generally only
assigned to the server operators.


General settings
----------------

All settings below are defined in the `settings` section of the admin plugin config file.

noreason_level
~~~~~~~~~~~~~~

The group/level from which admins are not required to specify a reason when giving penalties to players.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``superadmin``


hidecmd_level
~~~~~~~~~~~~~

The group/level required to be able to use hidden commands. On quake3 based games, a hidden command can be issued by
telling to command to oneself.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``senioradmin``


long_tempban_level
~~~~~~~~~~~~~~~~~~

Group/level required to be able to issue bans longer than the duration defined for the *long_tempban_max_duration*
setting.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``senioradmin``


long_tempban_max_duration
~~~~~~~~~~~~~~~~~~~~~~~~~

Maximum ban duration that can be inflicted by admins of group/level below the one defined at the *long_tempban_level*
setting.

expected values
  duration, see :ref:`duration-syntax`

default value
  ``3h``


command_prefix
~~~~~~~~~~~~~~

The prefix that should be put before b3 commands.

expected values
  a single character

default value
  ``!``


command_prefix_loud
~~~~~~~~~~~~~~~~~~~

Some commands can have their result broadcasted to all players instead of only to the player issuing the command. To
have such a behavior, use this command prefix instead of *command_prefix*.

Note that this behavior only work with commands that consider it.

expected values
  a single character

default value
  ``@``


command_prefix_big
~~~~~~~~~~~~~~~~~~

Some commands can have their result broadcasted to all players as a very noticeable way. To have such a behavior, use
this command prefix instead of *command_prefix*.

Note that this behavior only work with commands that consider it.

Also note that depending on the game, abuse of such display can be frustrating for users ; use it wisely.

expected values
  a single character

default value
  ``&``


admins_level
~~~~~~~~~~~~

The admin plugin considers as an admin any player who is member of a group of level higher or equal to the group/level
defined in the admin plugin config file at *admins_level*.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``mod``


ban_duration
~~~~~~~~~~~~

Temporary ban duration to apply to bans given by the :command:`!ban` and :command:`!banall` commands.

expected values
  duration, see :ref:`duration-syntax`

default value
  ``14d``


announce_registration
~~~~~~~~~~~~~~~~~~~~~

Define if a public message will be displayed to all in-game players when a user registered himself using the
:command:`!register` command. If enable, this can encourage others to register too.

expected values
  ``yes`` or ``no``

default value
  ``yes``


Commands
--------


admins
~~~~~~

The :command:`!admins` command tells which admins are currently on the game server.


usage

  The :command:`!admins` command takes no parameters.


customization

  Admins are players who are member of a group of level equal or higher than the group/level set in the admin plugin
  config file at *admins_level*.

  The :command:`!admins` command responds with two types of messages depending on if there are any admins online. Those
  messages can be customized in the admin plugin config file:

  *messages:admins*
    When there is one admin online or more, the message template used is *messages:admins*. This template must contain
    a `%s` placeholder which will be replaced with the actual list of online admin names and levels.

  *messages:no_admins*
    When there is no admin online, the message used is *messages:no_admins*. In the special case where message
    *messages:no_admins* would be present but empty, then no answer is given back to the player when using the
    :command:`!admins` command.


admintest
~~~~~~~~~

TODO


aliases
~~~~~~~

TODO


b3
~~

TODO


ban
~~~

TODO


banall
~~~~~~

TODO


baninfo
~~~~~~~

TODO



clientinfo
~~~~~~~~~~

TODO


clear
~~~~~

TODO


die
~~~

TODO


disable
~~~~~~~

TODO


enable
~~~~~~

TODO


find
~~~~

TODO


help
~~~~

TODO


kick
~~~~

TODO


kickall
~~~~~~~

TODO


lastbans
~~~~~~~~

TODO


leveltest
~~~~~~~~~

TODO


lookup
~~~~~~

TODO


makereg
~~~~~~~

TODO


map
~~~

TODO


maprotate
~~~~~~~~~

TODO


maps
~~~~

TODO


mask
~~~~

TODO


nextmap
~~~~~~~

TODO


notice
~~~~~~

TODO


pause
~~~~~

TODO


pbss
~~~~

TODO


permban
~~~~~~~

TODO


poke
~~~~

TODO


putgroup
~~~~~~~~

TODO


rebuild
~~~~~~~

TODO


reconfig
~~~~~~~~

TODO


register
~~~~~~~~

TODO


regtest
~~~~~~~

TODO


regulars
~~~~~~~~

TODO


restart
~~~~~~~

TODO


rules
~~~~~

TODO


runas
~~~~~

TODO


say
~~~

TODO


scream
~~~~~~

TODO


seen
~~~~

TODO


spam
~~~~

TODO


spams
~~~~~

TODO


spank
~~~~~

TODO


spankall
~~~~~~~~

TODO


status
~~~~~~

TODO


tempban
~~~~~~~

TODO


time
~~~~

TODO


unban
~~~~~

TODO


ungroup
~~~~~~~

TODO


unmask
~~~~~~

TODO


unreg
~~~~~

TODO


warn
~~~~

TODO


warnclear
~~~~~~~~~

TODO


warninfo
~~~~~~~~

TODO


warnremove
~~~~~~~~~~

TODO


warns
~~~~~

TODO


warntest
~~~~~~~~

TODO


