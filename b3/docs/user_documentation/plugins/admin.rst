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

Tells which admins are currently on the game server.

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

Show at most 10 aliases of a player.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!aliases` [:ref:`player <targeting-player-syntax>`]

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

Show the B3 version and uptime.

.. rubric:: default required level

*mod*

.. rubric:: usage

The :command:`!b3` command takes no parameters.



ban
^^^

Temporarily ban a player for the duration set by `ban_duration`_.

.. rubric:: default required level

*fulladmin*

.. rubric:: usage

:command:`!ban` <:ref:`player <targeting-player-syntax>`> <reason>
    ban a player specifying a reason. The reason can be any text of your choice or a reference to a reason shortcut as
    defined in the *warn_reasons* section of the admin config file.

:command:`!ban` <:ref:`player <targeting-player-syntax>`>
    ban a player not specifying a reason. This is allowed only for admins of group level higher than `noreason_level`_.

.. rubric:: alias

:command:`!b`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *error_no_reason*, *ban_self*, *action_denied_masked*
and *ban_denied*.

The ban duration can be changed in the plugin config file at `ban_duration`_.



banall
^^^^^^

Like the `ban`_ command except it will ban multiple players whom name contains a given term.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!banall` <term> [<reason>]

.. rubric:: alias

:command:`!ball`


baninfo
^^^^^^^

Tell if a given player has active bans.

.. rubric:: default required level

*admin*

.. rubric:: usage

:command:`!baninfo` <:ref:`player <targeting-player-syntax>`>

.. rubric:: alias

:command:`!bi`

.. rubric:: customization

The messages that can be displayed are: *baninfo*, *baninfo_no_bans*.



clientinfo
^^^^^^^^^^

Show the value of a given property for a player. The purpose of this command is more for debug purpose than anything
else but it can be useful to retrieve info such as the player IP address or guid.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!clientinfo` <:ref:`player <targeting-player-syntax>`> <field>
  where *field* can be one of:

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

Clear all active warnings and tk points (if the tk plugin is active) for a given player or for all in-game players.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!clear`

Clears active warnings and tk points for all in-game players

:command:`!clear` <:ref:`player <targeting-player-syntax>`>

Clears active warnings and tk points for the player identified by *<player>*

.. rubric:: alias

:command:`!kiss`

.. rubric:: customization

The messages that can be displayed are: *cleared_warnings* and *cleared_warnings_for_all*.



die
^^^

Shutdown B3

.. rubric:: default required level

*superadmin*



disable
^^^^^^^

Disable a plugin

.. rubric:: default required level

*superadmin*

.. rubric:: usage

:command:`!disable` <plugin name>


enable
^^^^^^

Enable a plugin that would have been disabled

.. rubric:: default required level

*superadmin*

.. rubric:: usage

:command:`!enable` <plugin name>


.. _find:

find
^^^^

Return the name and slot id of connected players matching a given pattern

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!find` <name>
    Find a player by its name or partial name

:command:`!find` <slot id>
    Find a player by its game slot id



help
^^^^

List available commands, or the short description of a given command

.. rubric:: default required level

*guest*

.. rubric:: usage

:command:`!help`

List the commands available to the player issuing the command


:command:`!help` <command>

Show a short description of the given command



kick
^^^^

Forcibly disconnects a player from the game server

.. rubric:: default required level

*admin*

.. rubric:: usage

:command:`!kick` <:ref:`player <targeting-player-syntax>`> <reason>
    kick a player specifying a reason. The reason can be any text of your choice or a reference to a reason shortcut as
    defined in the *warn_reasons* section of the admin config file.

:command:`!kick` <player>
    ban a player without specifying a reason. This is allowed only for admins of group level higher than `noreason_level`_.

.. rubric:: alias

:command:`!k`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *error_no_reason*, *kick_self*, *action_denied_masked*
and *kick_denied*.



kickall
^^^^^^^

Forcibly disconnects all players matching a pattern from the game server

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!kickall` <pattern> <reason>
    kick all players whose name matches the given pattern specifying a reason. The reason can be any text of your
    choice or a reference to a reason shortcut as defined in the *warn_reasons* section of the admin config file.

:command:`!kickall` <pattern>
    kick all players whose name matches the given pattern without specifying a reason.
    This is allowed only for admins of group level higher than `noreason_level`_.

.. rubric:: alias

:command:`!kall`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters* and *error_no_reason*.



lastbans
^^^^^^^^

List the 5 last active bans.

.. rubric:: default required level

*admin*

.. rubric:: usage

:command:`!lastbans`

.. rubric:: alias

:command:`!lbans`



.. _leveltest:

leveltest
^^^^^^^^^

Tell in which B3 group a player is in.


.. rubric:: usage

:command:`!leveltest` [:ref:`player <targeting-player-syntax>`]

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

Return the name and database ID of a player matching a given pattern

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!lookup` <name>

Find a player in the B3 database by its name or partial name

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *no_players* and *lookup_found*.



makereg
^^^^^^^

Put a player in the *Regular* group.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!makereg` <:ref:`player <targeting-player-syntax>`>


.. rubric:: alias

:command:`mr`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *groups_already_in* and *groups_put*.



map
^^^

Change the map on the server

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!map` <map name>



maprotate
^^^^^^^^^

Load the next map on the game server

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!maprotate`


maps
^^^^

List the server map rotation list

.. rubric:: default required level

*regular*

.. rubric:: usage

:command:`!maps`


mask
^^^^

Mask yourself as being a member of a group of lower level

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!mask` <:ref:`group <groups>`>
    Mask yourself as being a member of the given group.

:command:`!mask` <:ref:`group <groups>`> <:ref:`player <targeting-player-syntax>`>
    Mask another player as being a member of the given group.

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters* and *group_unknown*.



nextmap
^^^^^^^

Tell which map will be loaded next on the game server

.. rubric:: default required level

*reg*

.. rubric:: usage

:command:`!nextmap`



notice
^^^^^^

Save to the B3 database a note about a player

.. rubric:: default required level

*admin*

.. rubric:: usage

:command:`!notice` <:ref:`player <targeting-player-syntax>`> <note>



pause
^^^^^

Make B3 ignore any game event for a given duration

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!pause` <:ref:`duration <duration-syntax>`>



permban
^^^^^^^

Permanently ban a player.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!permban` <:ref:`player <targeting-player-syntax>`> <reason>
    permanently ban a player specifying a reason. The reason can be any text of your choice or a reference to a reason
    shortcut as defined in the *warn_reasons* section of the admin config file.

:command:`!permban` <:ref:`player <targeting-player-syntax>`>
    permanently ban a player not specifying a reason. This is allowed only for admins of group level higher than
    `noreason_level`_.

.. rubric:: alias

:command:`!pb`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *error_no_reason*, *ban_self*, *action_denied_masked*
and *ban_denied*.


poke
^^^^

Notify a player that he needs to move.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!poke` <:ref:`player <targeting-player-syntax>`>

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*.




putgroup
^^^^^^^^

Add a player to a B3 group.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!putgroup` <:ref:`player <targeting-player-syntax>`> <:ref:`group <groups>`>

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *group_unknown*, *group_beyond_reach*, *groups_already_in*
and *groups_put*.



rebuild
^^^^^^^

Sync up connected players. This can be useful for games for which B3 can loose track of connected players.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!rebuild`


reconfig
^^^^^^^^

Re-load all config files.

This way you can change some settings and apply them without restarting B3.

.. warning::
    Some plugins may require a full restart of B3 to apply changes

.. rubric:: default required level

*superadmin*

.. rubric:: usage

:command:`!reconfig`


register
^^^^^^^^

Register yourself as a basic user.

.. rubric:: default required level

*guest*

.. rubric:: usage

:command:`!register`
    Put the player who typed the command into the *:ref:`user <groups>`* group

.. rubric:: customization

The messages that can be displayed are: *groups_already_in*, *regme_confirmation* and *regme_annouce*.


regtest
^^^^^^^

The :command:`!regtest` command tells in which B3 group you are in.


.. rubric:: usage

The :command:`!regtest` command takes no parameters.


.. rubric:: customization

The response message template can be customized in the admin plugin config file at *messages:leveltest*.



regulars
^^^^^^^^

List online players which are in the regular group.

.. rubric:: default required level

*user*

.. rubric:: usage

:command:`!regulars`

.. rubric:: alias

:command:`!regs`

.. rubric:: customization

The messages that can be displayed are: *regulars* and *no_regulars*.



restart
^^^^^^^

Restart B3.

.. warning:: For this command to work, B3 must have been started with the `--restart` command line parameter

.. rubric:: default required level

*superadmin*

.. rubric:: usage

:command:`!restart`



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


