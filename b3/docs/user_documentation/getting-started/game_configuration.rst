.. _game-configuration:
.. index:: game server configuration, g_logsync, g_loghits

Game server configuration
=========================

This document describes the configuration of your game server that might be required in order for B3 to work properly.

If your game is not listed below, then you have nothing specific to do.



Quake III Arena, Call of Duty games, etc
----------------------------------------

Make sure your game server config sets the `g_logsync` cvar correctly.
::

   set g_logsync 2


Urban Terror 4.1 and 4.2
------------------------

Make sure your game server config sets the `g_logsync` cvar correctly.
::

   set g_logsync 2

You might want to log every bullet hit to the game log file in order for B3 to work with plugins such as XLRstats.
Then set the cvar `g_loghits` as bellow.

::

  set g_logsync "2"    // 0=no log, 1=buffered, 2=continuous, 3=append
  set g_loghits "1"    // log hits which allows b3 to recognize headshots and xlrstats to provide hit location statistics

.. note::
  If you are running a patched UrT server that allows up to 64 players, set sv_minrate to 25000 to have stable pings and have B3 work smoothly


Smokin' Guns
------------

::

  set g_logsync "1"
  set g_debugDamage "1" // log hits


Soldier of Fortune 2
--------------------

This game actually switches the settings…
::

  set g_logSync "0"  // 0 = continuous logging, 1 = buffered logging
  set g_logHits "1"  // set to 1 to log hits



Counter-Strike: Global Offensive CS:GO
--------------------------------------

In order to have a consistent name for the game log file, you need to start the game server with `-condebug` as a
command line parameter. The game server log file can then be found in the `csgo` folder under the name `console.log`.

You must have SourceMod installed on the game server. See http://www.sourcemod.net/

Make sure to avoid conflict with in-game commands between B3 and SourceMod by choosing different command prefixes.
See `PublicChatTrigger` and `SilentChatTrigger` in :file:`addons/sourcemod/configs/core.cfg`


SourceMod recommended plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

B3 Say
~~~~~~

If you have the SourceMod `plugin B3 Say`_ installed then the messages sent by B3 will better displayed on screen.

SuperLogs:CS:S
~~~~~~~~~~~~~~

If you have the `SourceMod plugin SuperLogs:CS:S`_ installed then kill stats will be more accurate.


.. _`plugin B3 Say`: http://forum.bigbrotherbot.net/counter-strike-global-offensive/sourcemod-plugins-for-b3/
.. _`SourceMod plugin SuperLogs:CS:S`: http://forums.alliedmods.net/showthread.php?p=897271