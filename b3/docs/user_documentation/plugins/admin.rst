.. _plugin-admin:

Admin
=====

The admin plugin is at the heart of BigBrotherBot. It brings to B3 the user groups and in-game commands.

It allows the game server owner to define his staff by assigning trusted players to the different administration groups.
Depending on their group membership, players will be given access to administrating commands which allow them to:

- display the server rules
- warn a user
- kick
- ban
- change map
- change the gamemode
- etc


General settings
----------------

All settings below are defined in the `settings` section of the admin plugin config file.

noreason_level
^^^^^^^^^^^^^^

The group/level from which admins are not required to specify a reason when giving penalties to players.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``superadmin``


hidecmd_level
^^^^^^^^^^^^^

The group/level required to be able to use hidden commands. On quake3 based games, a hidden command can be issued by
telling to command to oneself.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``senioradmin``


long_tempban_level
^^^^^^^^^^^^^^^^^^

Group/level required to be able to issue bans longer than the duration defined for the *long_tempban_max_duration*
setting.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``senioradmin``


long_tempban_max_duration
^^^^^^^^^^^^^^^^^^^^^^^^^

Maximum ban duration that can be inflicted by admins of group/level below the one defined at the *long_tempban_level*
setting.

expected values
  duration, see :ref:`duration-syntax`

default value
  ``3h``


command_prefix
^^^^^^^^^^^^^^

The prefix that should be put before b3 commands.

expected values
  a single character

default value
  ``!``


command_prefix_loud
^^^^^^^^^^^^^^^^^^^

Some commands can have their result broadcasted to all players instead of only to the player issuing the command. To
have such a behavior, use this command prefix instead of *command_prefix*.

.. note::
 that this behavior only work with commands that consider it.

expected values
  a single character

default value
  ``@``


command_prefix_big
^^^^^^^^^^^^^^^^^^

Some commands can have their result broadcasted to all players as a very noticeable way. To have such a behavior, use
this command prefix instead of *command_prefix*.

.. note::
    This behavior only work with commands that consider it.
    Also depending on the game, abuse of such display can be frustrating for users ; use it wisely.

expected values
  a single character

default value
  ``&``


admins_level
^^^^^^^^^^^^

The admin plugin considers as an admin any player who is member of a group of level higher or equal to the group/level
defined in the admin plugin config file at *admins_level*.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``mod``


ban_duration
^^^^^^^^^^^^

Temporary ban duration to apply to bans given by the :command:`!ban` and :command:`!banall` commands.

expected values
  duration, see :ref:`duration-syntax`

default value
  ``14d``


announce_registration
^^^^^^^^^^^^^^^^^^^^^

Define if a public message will be displayed to all in-game players when a user registered himself using the
:command:`!register` command. If enable, this can encourage others to register too.

expected values
  ``yes`` or ``no``

default value
  ``yes``



Commands
--------


admins
^^^^^^

The :command:`!admins` command tells which admins are currently on the game server.

.. rubric:: default required level

*mod*

.. rubric:: usage

The :command:`!admins` command takes no parameters.


.. rubric:: customization

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
^^^^^^^^^

Alias for command `regtest`_

.. rubric:: default required level

*admin*


aliases
^^^^^^^

The :command:`!aliases` command shows at most 10 aliases of a player.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!aliases [player]`

If ``player`` is provided, display at most 10 aliases for that player.

If ``player`` is not provided, display at most 10 of your aliases.

.. rubric:: alias

:command:`!alias`

.. rubric:: customization

The :command:`!aliases` command response can be customized in the admin plugin config file:

*messages:aliases*
    When the player has at least an alias, the message template used is *messages:aliases*. This template must contain
    2 `%s` placeholder which are respectively:
    - the player's name
    - the list of aliases

*messages:aliases_more_suffix*
    When the player has more than 10 aliases, this suffix will be added to the response.

*messages:no_aliases*
    When the player has no aliases, the message template used is *messages:no_aliases*. This template must contain
    one `%s` placeholder which will be replaced with the player's name.


b3
^^

The :command:`!b3` command shows the B3 version and uptime.

.. rubric:: default required level

*mod*

.. rubric:: usage

The :command:`!b3` command takes no parameters.


ban
^^^

The :command:`!ban` command temporarily bans a player for the duration set by `ban_duration`_.

.. rubric:: default required level

*fulladmin*

.. rubric:: usage

:command:`!ban <player> <reason>`
    ban a player specifying a reason. The reason can be any text of your choice or a reference to a reason shortcut as
    defined in the *warn_reasons* section of the admin config file.

:command:`!ban <player>`
    ban a player not specifying a reason. This is allowed only for admins of group level higher than `noreason_level`_.

.. rubric:: alias

:command:`!b`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *error_no_reason*, *ban_self*, *action_denied_masked*
and *ban_denied*.

The ban duration can be changed in the plugin config file at `ban_duration`_.


banall
^^^^^^

The `!banall` command behaves like the `ban`_ command except it will ban multiple players whom name contains a given
term.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!banall <term> [<reason>]`

.. rubric:: alias

:command:`!ball`


baninfo
^^^^^^^

The `!baninfo` command tells if a given player has active bans.

.. rubric:: default required level

*admin*

.. rubric:: usage

:command:`!baninfo <player>`

.. rubric:: alias

:command:`!bi`

.. rubric:: customization

The messages that can be displayed are: *baninfo*, *baninfo_no_bans*.


clientinfo
^^^^^^^^^^

The `!clientinfo` command shows the value of a given property for a player. The purpose of this command is more for
debug purpose than anything else but it can be useful to retrieve info such as the player IP address or guid.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!clientinfo <player> <field>` where *field* can be one of:
    - guid
    - pbid
    - name
    - exactName
    - ip
    - greeting
    - autoLogin
    - groupBits
    - connected
    - lastVisit
    - timeAdd
    - timeEdit
    - data
    - bans
    - warnings
    - groups
    - aliases
    - ip_addresses
    - maskLevel
    - maskGroup
    - maskedGroup
    - maskedLevel
    - maxLevel
    - maxGroup
    - numWarnings
    - lastWarning
    - firstWarning
    - numBans
    - lastBan

.. note:: Not all those fields will return human readable data.


clear
^^^^^

The `!clear` command clears all active warnings and tk points (if the tk plugin is active) for a given player or for all
in-game players.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!clear`

Clears active warnings and tk points for all in-game players

:command:`!clear <player>`

Clears active warnings and tk points for the player identified by *<player>*

.. rubric:: alias

:command:`!kiss`

.. rubric:: customization

The messages that can be displayed are: *cleared_warnings* and *cleared_warnings_for_all*.



die
^^^

TODO


disable
^^^^^^^

TODO


enable
^^^^^^

TODO

.. _find:

find
^^^^

TODO


help
^^^^

TODO


kick
^^^^

TODO


kickall
^^^^^^^

TODO


lastbans
^^^^^^^^

TODO

.. _leveltest:

leveltest
^^^^^^^^^

The :command:`!leveltest` command tells in which B3 group a player is in.


.. rubric:: usage

:command:`!leveltest [player]`

If ``player`` is an on-line player name, display in which B3 group this player is in.

If ``player`` is not provided, display in which B3 group you are in.


.. rubric:: customization

The :command:`!leveltest` command responds with two types of messages depending on if the user has a group or not. Those
messages can be customized in the admin plugin config file:

*messages:leveltest*
    When the player is in a B3 group, the message template used is *messages:leveltest*. This template must contain
    5 `%s` placeholder which are respectively:
    - the player's name
    - the player's B3 database identifier
    - the player's B3 group name
    - the player's B3 group level
    - the date at which the player joined that B3 group

*messages:leveltest_nogroups*
    When the player is in no B3 group, the message template used is *messages:leveltest_nogroups*. This template must
    contain 2 `%s` placeholder which are respectively:
    - the player's name
    - the player's B3 database identifier


.. _lookup:

lookup
^^^^^^

TODO


makereg
^^^^^^^

TODO


map
^^^

TODO


maprotate
^^^^^^^^^

TODO


maps
^^^^

TODO


mask
^^^^

TODO


nextmap
^^^^^^^

TODO


notice
^^^^^^

TODO


pause
^^^^^

TODO


pbss
^^^^

TODO


permban
^^^^^^^

TODO


poke
^^^^

TODO


putgroup
^^^^^^^^

TODO


rebuild
^^^^^^^

TODO


reconfig
^^^^^^^^

TODO


register
^^^^^^^^

TODO



regtest
^^^^^^^

The :command:`!regtest` command tells in which B3 group you are in.


.. rubric:: usage

The :command:`!regtest` command takes no parameters.


.. rubric:: customization

The response message template can be customized in the admin plugin config file at *messages:leveltest*.



regulars
^^^^^^^^

TODO


restart
^^^^^^^

TODO


rules
^^^^^

TODO


runas
^^^^^

TODO


say
^^^

TODO


scream
^^^^^^

TODO


seen
^^^^

TODO


spam
^^^^

TODO


spams
^^^^^

TODO


spank
^^^^^

TODO


spankall
^^^^^^^^

TODO


status
^^^^^^

TODO


tempban
^^^^^^^

TODO


time
^^^^

TODO


unban
^^^^^

TODO


ungroup
^^^^^^^

TODO


unmask
^^^^^^

TODO


unreg
^^^^^

TODO


warn
^^^^

TODO


warnclear
^^^^^^^^^

TODO


warninfo
^^^^^^^^

TODO


warnremove
^^^^^^^^^^

TODO


warns
^^^^^

TODO


warntest
^^^^^^^^

TODO


