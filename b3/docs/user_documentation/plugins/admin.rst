.. index:: Plugins; Admin, Admin plugin
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


:index:`noreason_level`
^^^^^^^^^^^^^^^^^^^^^^^

The group/level from which admins are not required to specify a reason when giving penalties to players.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``superadmin``


:index:`hidecmd_level`
^^^^^^^^^^^^^^^^^^^^^^

The group/level required to be able to use hidden commands. On quake3 based games, a hidden command can be issued by
telling to command to oneself.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``senioradmin``


:index:`long_tempban_level`
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Group/level required to be able to issue bans longer than the duration defined for the *long_tempban_max_duration*
setting.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``senioradmin``


:index:`long_tempban_max_duration`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Maximum ban duration that can be inflicted by admins of group/level below the one defined at the *long_tempban_level*
setting.

expected values
  duration, see :ref:`duration-syntax`

default value
  ``3h``


:index:`command_prefix`
^^^^^^^^^^^^^^^^^^^^^^^

The prefix that should be put before b3 commands.

expected values
  a single character

default value
  ``!``


:index:`command_prefix_loud`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some commands can have their result broadcasted to all players instead of only to the player issuing the command. To
have such a behavior, use this command prefix instead of *command_prefix*.

.. note::
 that this behavior only work with commands that consider it.

expected values
  a single character

default value
  ``@``


:index:`command_prefix_big`
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some commands can have their result broadcasted to all players as a very noticeable way. To have such a behavior, use
this command prefix instead of *command_prefix*.

.. note::
    This behavior only work with commands that consider it.
    Also depending on the game, abuse of such display can be frustrating for users ; use it wisely.

expected values
  a single character

default value
  ``&``


:index:`admins_level`
^^^^^^^^^^^^^^^^^^^^^

The admin plugin considers as an admin any player who is member of a group of level higher or equal to the group/level
defined in the admin plugin config file at *admins_level*.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``mod``


:index:`ban_duration`
^^^^^^^^^^^^^^^^^^^^^

Temporary ban duration to apply to bans given by the :command:`!ban` and :command:`!banall` commands.

expected values
  duration, see :ref:`duration-syntax`

default value
  ``14d``


:index:`announce_registration`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Define if a public message will be displayed to all in-game players when a user registered himself using the
:command:`!register` command. If enable, this can encourage others to register too.

expected values
  ``yes`` or ``no``

default value
  ``yes``


.. _spamages:
.. index:: spamages

Spamages settings
-----------------

The `spamages` section of the admin plugin config file defines ids for messages you want to be easily displayed to
players with the `spam`_ command.

If the message id is of the form 'rule#' where # is a number between 1 and 20, it will be used for the `rules`_ command.

.. rubric:: Related commands:

`spam`_, `spams`_ and `rules`_.


Commands
--------

.. index:: single: !admins

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



.. index:: single: !admintest

admintest
^^^^^^^^^

Alias for command `regtest`_

.. rubric:: default required level

*admin*



.. index:: single: !aliases

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



.. index:: single: !b3

b3
^^

Show the B3 version and uptime.

.. rubric:: default required level

*mod*

.. rubric:: usage

The :command:`!b3` command takes no parameters.



.. index:: single: !ban
.. index:: single: !b

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



.. index:: single: !banall
.. index:: single: !ball

banall
^^^^^^

Like the `ban`_ command except it will ban multiple players whom name contains a given term.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!banall` <term> [<reason>]

.. rubric:: alias

:command:`!ball`



.. index:: single: !baninfo
.. index:: single: !bi

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



.. index:: single: !clientinfo

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



.. index:: single: !clear
.. index:: single: !kiss

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



.. index:: single: !die

die
^^^

Shutdown B3

.. rubric:: default required level

*superadmin*



.. index:: single: !disable

disable
^^^^^^^

Disable a plugin

.. rubric:: default required level

*superadmin*

.. rubric:: usage

:command:`!disable` <plugin name>



.. index:: single: !enable

enable
^^^^^^

Enable a plugin that would have been disabled

.. rubric:: default required level

*superadmin*

.. rubric:: usage

:command:`!enable` <plugin name>



.. _find:
.. index:: single: !find

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



.. index:: single: !help
.. index:: single: !h

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


.. index:: single: !kick
.. index:: single: !k

kick
^^^^

Forcibly disconnects a player from the game server

.. rubric:: default required level

*admin*

.. rubric:: usage

:command:`!kick` <:ref:`player <targeting-player-syntax>`> <reason>
    kick a player specifying a reason. The reason can be any text of your choice or a reference to a reason shortcut as
    defined in the *warn_reasons* section of the admin config file.

:command:`!kick` <:ref:`player <targeting-player-syntax>`>
    kick a player without specifying any reason. This is allowed only for admins of group level higher than `noreason_level`_.

.. rubric:: alias

:command:`!k`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *error_no_reason*, *kick_self*, *action_denied_masked*
and *kick_denied*.



.. index:: single: !kiall
.. index:: single: !kall

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
    kick all players whose name matches the given pattern without specifying any reason.
    This is allowed only for admins of group level higher than `noreason_level`_.

.. rubric:: alias

:command:`!kall`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters* and *error_no_reason*.



.. index:: single: !lastbans
.. index:: single: !lbans

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
.. index:: single: !leveltest
.. index:: single: !lt

leveltest
^^^^^^^^^

Tell in which B3 group a player is in.


.. rubric:: usage

:command:`!leveltest` [:ref:`player <targeting-player-syntax>`]

If ``player`` is an on-line player name, display in which B3 group this player is in.

If ``player`` is not provided, display in which B3 group you are in.

.. rubric:: alias

:command:`!lt`

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
.. index:: single: !lookup

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



.. index:: single: !makereg
.. index:: single: !mr

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


.. index:: single: !map

map
^^^

Change the map on the server

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!map` <map name>



.. index:: single: !maprotate

maprotate
^^^^^^^^^

Load the next map on the game server

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!maprotate`



.. index:: single: !maps

maps
^^^^

List the server map rotation list

.. rubric:: default required level

*regular*

.. rubric:: usage

:command:`!maps`



.. index:: single: !mask

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



.. index:: single: !nextmap

nextmap
^^^^^^^

Tell which map will be loaded next on the game server

.. rubric:: default required level

*reg*

.. rubric:: usage

:command:`!nextmap`



.. index:: single: !notice

notice
^^^^^^

Save to the B3 database a note about a player

.. rubric:: default required level

*admin*

.. rubric:: usage

:command:`!notice` <:ref:`player <targeting-player-syntax>`> <note>



.. index:: single: !pause

pause
^^^^^

Make B3 ignore any game event for a given duration

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!pause` <:ref:`duration <duration-syntax>`>



.. index:: single: !permban
.. index:: single: !pb

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



.. index:: single: !poke

poke
^^^^

Notify a player that he needs to move.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!poke` <:ref:`player <targeting-player-syntax>`>

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*.



.. index:: single: !putgroup

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



.. index:: single: !rebuild

rebuild
^^^^^^^

Sync up connected players. This can be useful for games for which B3 can loose track of connected players.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!rebuild`



.. index:: single: !reconfig

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



.. index:: single: !register

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



.. index:: single: !regtest

regtest
^^^^^^^

The :command:`!regtest` command tells in which B3 group you are in.


.. rubric:: usage

The :command:`!regtest` command takes no parameters.


.. rubric:: customization

The response message template can be customized in the admin plugin config file at *messages:leveltest*.



.. index:: single: !regulars
.. index:: single: !regs

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



.. index:: single: !restart

restart
^^^^^^^

Restart B3.

.. warning:: For this command to work, B3 must have been started with the `--restart` command line parameter

.. rubric:: default required level

*superadmin*

.. rubric:: usage

:command:`!restart`



.. index:: single: !rules
.. index:: single: !r

rules
^^^^^

Display the server rules.

.. rubric:: default required level

*guest*

.. rubric:: usage

:command:`!rules`

.. rubric:: alias

:command:`!r`

.. rubric:: customization

The server rules are defined in the admin plugin config file under the section :ref:`spamages <spamages>`.

Default rules are: ::

    rule1: ^3Rule #1: No racism of any kind
    rule2: ^3Rule #2: No clan stacking, members must split evenly between the teams
    rule3: ^3Rule #3: No arguing with admins (listen and learn or leave)
    rule4: ^3Rule #4: No abusive language or behavior towards admins or other players
    rule5: ^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names
    rule6: ^3Rule #6: No recruiting for your clan, your server, or anything else
    rule7: ^3Rule #7: No advertising or spamming of websites or servers
    rule8: ^3Rule #8: No profanity or offensive language (in any language)
    rule9: ^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning
    rule10: ^3Rule #10: Offense players must play for the objective and support their team

If you want to add another rule, name it `rule11` and so on up to number 20.



.. index:: single: !runas

runas
^^^^^

Run a command as a different user

.. rubric:: default required level

*superadmin*

.. rubric:: usage

:command:`!runas` <name> <command>

.. rubric:: alias

:command:`!su`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*.



.. index:: single: !say

say
^^^

Broadcast a message to all players.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!say` <text>

.. rubric:: alias

:command:`!su`

.. rubric:: customization

The text template can be customized with setting *say* from the *messages* section of the config file.

That text template must have two place holders `%s`. The first one will be replaced by the name of the player issuing
the command, while the second will be replaced with the text to broadcast.



.. index:: single: !scream

scream
^^^^^^

Broadcast a message 5 times in a row to all players.

If your game support Quake3 color codes, then each message occurrence will be in a different color.

.. rubric:: default required level

*admin*

.. rubric:: usage

:command:`!scream` <text>



.. index:: single: !seen

seen
^^^^

Report the last time a player was seen on the game server.

.. rubric:: default required level

*reg*

.. rubric:: usage

:command:`!seen` <:ref:`player <targeting-player-syntax>`>

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *no_players* and *seen*.

The *seen* template must contain two `%s` placeholders which will be respectively replaced by the name of the player
and the date and time he was last seen at.


.. index:: single: !spam
.. index:: single: !s

spam
^^^^

Spam a predefined message.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!spam` <:ref:`message id <spamages>`>
    will spam the message defined in the *spamages* section of the config file under the given message id to all players.

:command:`!spam` <:ref:`player <targeting-player-syntax>`> <:ref:`message id <spamages>`>
    will spam the message defined in the *spamages* section of the config file under the given message id to the specified player in a private message.

.. rubric:: alias

:command:`!s`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*.

Also see the `spamages`_ section of the config file.



.. index:: single: !spams

spams
^^^^^

List spam message ids.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!spams`



.. index:: single: !spank
.. index:: single: !sp

spank
^^^^^

Spank a player (kick).

.. rubric:: default required level

*fulladmin*

.. rubric:: usage

:command:`!spank` <:ref:`player <targeting-player-syntax>`> <reason>
    spank a player specifying a reason. The reason can be any text of your choice or a reference to a reason shortcut as
    defined in the *warn_reasons* section of the admin config file.

:command:`!spank` <:ref:`player <targeting-player-syntax>`>
    spank a player without specifying any reason. This is allowed only for admins of group level higher than `noreason_level`_.

.. rubric:: alias

:command:`!sp`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *error_no_reason*, *kick_self*, *action_denied_masked*,
 *kick_denied*, *spanked_reason* and *spanked*.



.. index:: single: !spankall
.. index:: single: !sall

spankall
^^^^^^^^

Spank all players matching a pattern from the game server.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!spankall` <pattern> <reason>
    spank all players whose name matches the given pattern specifying a reason. The reason can be any text of your
    choice or a reference to a reason shortcut as defined in the *warn_reasons* section of the admin config file.

:command:`!spankall` <pattern>
    spank all players whose name matches the given pattern without specifying any reason.
    This is allowed only for admins of group level higher than `noreason_level`_.

.. rubric:: alias

:command:`!kall`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters* and *error_no_reason*, *spanked_reason* and *spanked*.



.. index:: single: !status

status
^^^^^^

Report status of B3 database.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!status`



.. index:: single: !tempban
.. index:: single: !tb

tempban
^^^^^^^

Temporarily ban a player for the duration a given duration.

.. rubric:: default required level

*admin*

.. rubric:: usage

:command:`!tempban` <:ref:`player <targeting-player-syntax>`> <:ref:`duration <duration-syntax>`> <reason>
    tempban a player for the given duration specifying a reason. The reason can be any text of your choice or a
    reference to a reason shortcut as defined in the *warn_reasons* section of the admin config file.

:command:`!tempban` <:ref:`player <targeting-player-syntax>`> <:ref:`duration <duration-syntax>`>
    tempban a player for a given duration not specifying a reason. This is allowed only for admins of group level
    higher than `noreason_level`_.

.. rubric:: alias

:command:`!tb`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *error_no_reason*, *temp_ban_self*,
*action_denied_masked* and *temp_ban_denied*.

A maximum tempban duration is enforced for admin of level lower than `long_tempban_level`_. See setting `long_tempban_max_duration`_.



.. index:: single: !time

time
^^^^

Display the current time.

.. rubric:: default required level

*user*

.. rubric:: usage

:command:`!time`
    Display the server time.

:command:`!time` <timezone/offset>
    Display the time for a given timezone or offset.

.. rubric:: customization

The messages that can be displayed are: *time*.



.. index:: single: !unban

unban
^^^^^

Unban a player.

.. rubric:: default required level

*fulladmin*

.. rubric:: usage

:command:`!tempban` <:ref:`player <targeting-player-syntax>`>

    .. tip::
        As the player you which to unban cannot be connected on the game server you will have to get the B3 database ID
        for that player. To do so, use the `lookup`_ command.

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*.



.. index:: single: !ungroup

ungroup
^^^^^^^

Remove a player from a B3 group.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!ungroup` <:ref:`player <targeting-player-syntax>`> <:ref:`group <groups>`>

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *group_unknown*.



.. index:: single: !unmask

unmask
^^^^^^

Un-hide level.

Revert what the `mask`_ command does.

.. rubric:: default required level

*superadmin*

.. rubric:: usage

:command:`!unmask`
    unmask yourself.

:command:`!unmask` <:ref:`player <targeting-player-syntax>`>
    unmask a given player.



.. index:: single: !unreg

unreg
^^^^^

Remove a player from the *regular* group.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!unmask` <:ref:`player <targeting-player-syntax>`>

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*.



.. index:: single: !warn
.. index:: single: !w

warn
^^^^

Give a warning to a player.

If then the player reaches a high number of active warnings, he is temporarily banned.
See :ref:`Warning system <guide-warning>`.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!warn` <:ref:`player <targeting-player-syntax>`> <reason>
    warn a player specifying a reason. The reason can be any text of your choice or a reference to a reason shortcut as
    defined in the *warn_reasons* section of the admin config file.

:command:`!warn` <:ref:`player <targeting-player-syntax>`>
    warn a player without specifying any reason.

.. rubric:: alias

:command:`!w`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*, *warn_self*, *warn_denied* and *warn_too_fast*.



.. index:: single: !warnclear
.. index:: single: !wc

warnclear
^^^^^^^^^

Clear all of a users' warnings.

.. rubric:: default required level

*senioradmin*

.. rubric:: usage

:command:`!warnclear` <:ref:`player <targeting-player-syntax>`>

.. rubric:: alias

:command:`!wc`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*.



.. index:: single: !warninfo
.. index:: single: !wi

warninfo
^^^^^^^^

Display how many active warnings a user has.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!warninfo` <:ref:`player <targeting-player-syntax>`>

.. rubric:: alias

:command:`!wi`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*.



.. index:: single: !warnremove
.. index:: single: !wr

warnremove
^^^^^^^^^^

Remove the last warning of a user.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!warnremove` <:ref:`player <targeting-player-syntax>`>

.. rubric:: alias

:command:`!wr`

.. rubric:: customization

The messages that can be displayed are: *invalid_parameters*.



.. index:: single: !warns

warns
^^^^^

List the available warning ids.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!warns`

.. rubric:: customization

See the *warn_reasons* section of the admin plugin config file.



.. index:: single: !warntest
.. index:: single: !wt

warntest
^^^^^^^^

Test a warning

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!warntest` <warning id>
    See the *warn_reasons* section of the admin plugin config file or the `warns`_ command for the list of warning ids.

.. rubric:: alias

:command:`!wt`





