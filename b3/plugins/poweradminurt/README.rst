Power Admin Urban Terror for Big Brother Bot
============================================

http://www.bigbrotherbot.net


Description

-----------
This plugin brings Urban Terror 4.1 / 4.2 / 4.3 specific features to Bigbrotherbot.


Commands
--------

!paadvise (!advise)
  report team skill balance, and give advice if teams are unfair

!paunskuffle (!unsk)
  create unbalanced teams. Used to test !paskuffle and !pabalance.

!paskuffle (!sk)
  shuffle players to balanced teams by numbers and skill

  Lock players are also moved. Use `!force all free` to unlock them.

!pabalance (!bal)
  move as few players as needed to create teams balanced by numbers AND skill.

  Lock players are not moved. Use `!force all free` to unlock them.

!paautoskuffle (!ask) [new mode]
  display current auto skuffle mode

  If *new mode* is provided, switch to that new auto skuffle mode.

  Skuffle modes are :

  +-----+--------------+
  |  0  | none         |
  +-----+--------------+
  |  1  | advise       |
  +-----+--------------+
  |  2  | auto balance |
  +-----+--------------+
  |  3  | auto skuffle |
  +-----+--------------+

!paswap (!swap) <player1> [player2]
  swap two teams for 2 players. If *player2* is not specified, the admin using the command is swapped with player1

  Doesn't work with spectators (exception for calling admin).

!pateams (!teams)
  balance teams evenly (read *teambalancer* below)

!pavote <on/off/reset>
  switch voting (cvar *g_allowvote*)

  When choosing *reset* set the voting mode as it was before B3 started

!paversion (!paver)
  display the version of PowerAdminUrt

!paexec <configfile.cfg>
  execute a server given server config file

!pacyclemap (!cyclemap)
  tell the game server to load the next map

!pamaprestart (!maprestart)
  tell the game server to restart the current map

!pamapreload (!mapreload)
  tell the game server to reload the current map

!paset <cvar> <value>
  set a server cvar to a certain value

!paget <cvar name>
  display a server cvar value

!pabigtext (!bigtext) <message>
  print a bold message on the center of players' screen

!pamute (!mute) <player> [<seconds>]
  mute a player

  if *seconds* is provided, mute the player for this amount of time.

  if *seconds* is 0, unmute the player

!papause (!pause)
  tell the game server to pause the current game

!paslap (!slap) <name/id> [<amount>]
  (multi) slap a player

!panuke (!nuke) <player> [<ammount>]
  (multi) Nuke a player

!paveto
  veto currently running Vote.

!paforce (!force) <player> <red/blue/spec/free> [lock]
  force a client to red/blue/spec or release the player from a forced team (free).

  You can use the first letter of a team instead of the full team name.

  Adding *'lock'* will lock the player where it is forced to.

  Using *'all free'* wil release all locks.

  **Usage examples**

  Moving Bill to the red team :
    - `!force bill red`
    - `!force bill r`

  Forcing Bill to stay in the red team :
    `!force bill r lock`

  Allowing Bill to go whereever he wants :
    `!force bill free`

!paswapteams (!swapteams)
  tell the game server to swap teams

!pashuffleteams (!shuffleteams)
  tell the game server to shuffle teams

!pamoon (!moon) <on/off>
  activate Moon mode... low gravity

  Set the values for normal/low gravity in the plugin config file under section *moonmode*

!papublic (!public) <on/off>
  set the server to public or private mode

  In private mode players need a password to enter the server.

  When putting the server in private mode, a password will be picked depending on the settings from section *publicmode*.

!pamatch (!match) <on/off>
  tell the game server to switch of match mode (cvar *g_matchmode*)

  When switching to match mode B3 plugins set in the config section *matchmode/plugins_disable* will be disabled.

  Then will be re-enabled when you will use `!match off`. Also the team balancer, name checker, spec checker, heashot
  counter will be disabled.

!pagear (!gear) <all/none/reset/[+-](nade|snipe|spas|pistol|auto|negev)> *for UrT 4.1*
  set allowed/disallowed weapon groups

  *all* allow all weapons

  *none* will only allow the knife

  *reset* will put back the settings as they were before B3 started

  Use *+* before a weapon group to allow it

  Use *-* before a weapon group to disallow it

  If you want to disable only one weapon/item instead of weapon group, have a look at the plugins weaponcontrolurt  and weaponcontrolurt42. They allow to disallow smoke grenades while allowing HE for instance, or can disallow the kelvar vest.


!pagear (!gear) <all/none/reset/[+-]weapon/item/group> *for UrT 4.2*
  set allowed/disallowed weapons or items

  *all* allow all weapons

  *none* will only allow the knife

  *reset* will put back the settings as they were before B3 started

  Use *+* before a weapon/item to allow it

  Use *-* before a weapon/item to disallow it

  Accepted *weapon* and *item* names are what you would expect. I.E. *spas* for the SPAS, *de* for Desert Eagle .50, etc.

  Accepted *group* names are stricly one of:

  - *all_nades*: for all HE and Smoke grenades
  - *all_snipers*: for SR8 and PSG1
  - *all_pistols*: for Beretta 92FS, .50 Desert Eagle, Glock and Colt1911
  - *all_auto*: for MPK5, LR300ML, Colt M4, MAC11, UMP45, G36, AK.103 and Negev LMG

  For instance, you can make your server a SR8 only with the following command::

    !gear none +sr8

  If you want to only allow any sniper rifles::

    !gear none +all_snipers

  or maybe you just want to forbid smoke grenades::

    !gear all -smoke


!paffa (!ffa)
  switch to gametype *Free For All*

!patdm (!tdm)
  switch to gametype *Team Death Match*

!pats (!ts)
  switch to gametype *Team Survivor*

!paftl (!ftl)
  switch to gametype *Follow The Leader*

!pacah (!cah)
  switch to gametype *Capture And Hold*

!pactf (!ctf)
  switch to gametype *Capture The Flag*

!pabomb (!bomb)
  switch to gametype *Bomb Mode*

!paident (!id) <name/id>
  print a player's B3-id, Guid and IP to screen

!pawaverespawns (!waverespawns) <on/off>
  tell the game server to respawn players by wave (cvar *g_waverespawns*)

!pasetnextmap (!setnextmap) <next map name>
  tell the game server what will be the next map (cvar *g_nextmap*)

  You can use a partial map name, B3 will do its best to guess the correct name

!parespawngod (!respawngod) <seconds>
  set the respawn protection in seconds (cvar *g_respawnProtection*)

!parespawndelay (!respawndelay) <seconds>
  set the respawn delay in seconds (cvar *g_respawnDelay*)

!pacaplimit (!caplimit) <number of captures>
  set the amount of flagcaps before map is over (cvar *capturelimit*)

!patimelimit (!timelimit) <minutes>
  set the minutes before map is over (cvar *timelimit*)

!pafraglimit (!fraglimit) <number of frags>
  set the amount of points to be scored before map is over (cvar *fraglimit*)

!pabluewave (!bluewave) <seconds>
  set the blue wave respawn time (cvar *g_bluewave*)

!paredwave (!redwave) <seconds>
  set the red wave respawn time (cvar *g_redwave*)

!pasetwave (!setwave) <seconds>
  set the wave respawn time for both teams (cvars *g_bluewave* and *g_redwave*)

!pahotpotato (!hotpotato) <minutes>
  set the flag explode time (cvar *g_hotpotato*)

!pasetgravity (!setgravity) <value>
  set the gravity value. default = 800 (less means less gravity) (cvar *g_gravity*)
  Also see command *!pamoon*



Commands specific to Urban Terror 4.2
-------------------------------------

!pakill (!kill) <name/id>
  kill a player

!palms (!lms)
  change game type to *Last Man Standing*

!pajump (!jump)
  change game type to *Jump Mode*

!pafreeze (!freeze)
  change game type to *Freeze Tag*
  
!pagoto (!goto) <on/off>
  activate/deactivate the *goto* (Jump mode feature)
  
!paskins (!skins) <on/off>
  activate/deactivate the use of client skins
  
!pafunstuff (!funstuff) <on/off>
  activate/deactivate the use of funstuff

!pastamina (!stamina) <default/regain/infinite>
  set the stamina behavior (Jump mode feature)

!pacaptain (!captain) <player>
  set the given client as the captain for its team (only in match mode)

!pasub (!sub) <player>
  set the given client as a substitute for its team (only in match mode)
  

Other features
--------------

Autobalancer
~~~~~~~~~~~~

When active the autobalancer makes sure the teams will always be balanced. When a player joins a team that is already
outnumbering the other team B3 will immediately correct the player to the right team. The balancer also checks on
(configurable) intervals if balancing is needed. In that case it will balance the player with the least teamtime, so
the player that joined the team last will be force to the other team.


Namechecker
~~~~~~~~~~~

When active it checks for unwanted playernames. This is a simple function and warns players using duplicate names, the
name 'all' or 'New UrT Player' depending on the config. Three warnings without a responding rename action will result
in a kick.


Vote Delayer
~~~~~~~~~~~~

You can disable voting during the first minutes of a round. Set the number of minutes in the config and voting will be
disabled for that amount of time.


Spec Checker
~~~~~~~~~~~~

Controls how long a player may stay in spec before being warned. All parameters are configurable.

**Important!**

In order to make Spec checker work it is crucial you edit *b3/conf/plugin_admin.xml*

Open the file with your favorite text editor and look for the next line:
  `<set name="spectator">5m, ^7spectator too long on full server</set>`
Change it to:
  `<set name="spectator">1h, ^7spectator too long on full server</set>`


Bot Support
~~~~~~~~~~~

This will crash your server. I've put it in here as a challenge for you programmers out there to fix us a stable version.


Headshot counter
~~~~~~~~~~~~~~~~

Broadcasts headshots made by players.


RotationManager
~~~~~~~~~~~~~~~

Switches between different mapcycles, based on the playercount.


Changelog
---------

09/06/2008 - Courgette
  - add commands pagear (to change allowed weapons)
  - add commands paffa, patdm, pats, paftl, pacah, pactf, pabomb (to change g_gametype)
  - now namecheck is disabled during match mode
  - _smaxplayers is now set taking care of private slots (this is for speccheck)
09/07/2008 - Courgette
  - add command !paident <player> : show date / ip / guid of player. Useful when moderators make demo of cheaters
17/08/2008 - xlr8or
  - added counter for max number of allowed client namechanges per map before being kicked
1.4.0b8 - 20/10/2008 - xlr8or
  - fixed a bug where balancing failed and disabled itself on rcon socket failure.
1.4.0b9 - 10/21/2008 - mindriot
  - added team_change_force_balance_enable to control force balance on client team change
1.4.0b10 - 10/22/2008 - mindriot
  -added autobalance_gametypes to specify which gametypes to autobalance
1.4.0b11 -  10/22/2008 - mindriot
  - if client does not have teamtime, provide new one
1.4.0b12 -  10/23/2008 - mindriot
  - onTeamChange is disabled during matchmode
1.4.0b13 -  10/28/2008 - mindriot
  - fixed teambalance to set newteam if dominance switches due to clients voluntarily switching teams during balance
1.4.0b14 -  10/28/2008 - mindriot
  - teambalance verbose typo
1.4.0b15 -  12/07/2008 - xlr8or
  - teamswitch-stats-harvest exploit penalty -> non legit switches become suicides
1.4.0b16 -  2/9/2009 - xlr8or
  - added locking mechanism to paforce. !paforce <player> <red/blue/s/free> <lock>
1.4.0b17 -  2/9/2009 - xlr8or
  - Fixed a default value onLoad for maximum teamdiff setting
03/15/09 by FSK405|Fear
  - added more rcon cmds:
  - !waverespawns <on/off> Turn waverespawns on/off
  - !bluewave <seconds> Set the blue team wave respawn delay
  - !redwave <seconds> Set the red team wave respawn delay
  - !setnextmap <mapname> Set the nextmap
  - !respawngod <seconds> Set the respawn protection
  - !respawndelay <seconds> Set the respawn delay
  - !caplimit <caps>
  - !timelimit <mins>
  - !fraglimit <frags>
  - !hotpotato <mins>
1.4.0b18 -  4/4/2009 - xlr8or
  - Fixed locked force to stick and not continue with balancing
  - Helmet and Kevlar messages only when connections < 20
1.4.0 -  28/6/2009 - xlr8or
  - Time to leave beta
  - Teambalance raises warning instead of error
1.4.1 -  10/8/2009 - naixn
  - Improved forceteam locking mechanism and messaging
1.4.2 -  10/8/2009 - xlr8or
  - Added TeamLock release command '!paforce all free' and release on gameExit
1.4.3 - 09/07/2009 - SGT
  - add use of dictionary for private password (papublic)
1.5.0 -  27/10/2009 - Courgette
  - /!\ REQUIRES B3 v1.2.1 /!\
  - add !pamap which works with partial map names
  - update !pasetnextmap to work with partial map names
1.5.1 -  27/10/2009 - Courgette
  - debug !pamap and !pasetnextmap
  - debug dictionnary use for !papublic
  - !papublic can now use randnum even if dictionnary is not used
1.5.2 -  31/01/2010 - xlr8or
  - added ignore Set and Check functions for easier implementation in commands
  - added ignoreSet(30) to swapteams and shuffleteams to temp disable auto checking functions
  - Note: this will be overridden by the ignoreSet(60) when the new round starts after swapping/shuffling!
  - Send rcon result to client on !paexec
1.5.3 -  13/03/2010 - xlr8or
  - fixed headshotcounter reset. now able to set it to 'no', 'round', or 'map'
1.5.4 -  19/03/2010 - xlr8or
  - fixed endless loop in ignoreCheck()
1.5.5 -  30/06/2010 - xlr8or
  - no longer set bot_enable var to 0 on startup when botsupport is disabled.
1.5.6 -  20/09/2010 - Courgette
  - debug !paslap and !panuke
  - add tests
1.5.7 -  20/09/2010 - BlackMamba
  - fix !pamute - http://www.bigbrotherbot.net/forums/xlr-releases/poweradminurt-1-4-0-for-urban-terror!/msg15296/#msg15296
1.5.8 -  20/09/2011 - SGT
  - minor fix for b3 1.7 compatibility
  - fix method onKillTeam
1.5.9 - 25/09/2011 -  xlr8or
  - Code reformat by convention
1.6 -  25/07/2012 - Courgette
  - prepare separation of poweradmin plugin for UrT4.1 and UrT4.2
  - change default config file from xml to ini format
  - change the way to load from the config the list of plugins to disable in matchmode. See section 'matchmode' in config file
  - gracefully fallback on default value if cannot read publicmode/usedic from config file
  - UrT4.2: implement command !kill <player>
1.6.1 -  25/08/2012 - Courgette
  - fix checkunknown feature
  - name checker: provide exact reason for warning in log
  - fix plugin version since UrT 4.1/4.2 split
1.6.2 -  13/09/2012 - Courgette
  - UrT42: fix feedback message on missing parameter for the !pakill command
1.6.3 -  05/10/2012 - Courgette
  - UrT42: fix the headshot counter by introducing hit location constants
1.7 -  06/10/2012 - Courgette
  - UrT42: add the radio spam protection feature
1.8 -  21/10/2012 - Courgette
  - UrT42: change: update to new rcon mute command behavior introduced in UrT 4.2.004
1.9 -  27/10/2012 - Courgette
  - change: remove command pamap now that the B3 admin plugin map command can provide suggestions and does fuzzy matching
  - change: command !setnextmap now gets map suggestions from the B3 parser
1.10 -  28/10/2012 - Courgette
  - merge from xlr8or/master
1.11 -  09/11/2012 - Courgette
  - new: add command !jump to change the server to the jump gametype
1.12 -  07/04/2013 - Courgette
  - the spec check won't be ignored at game/round start for 30s anymore
1.13 -  07/07/2013 - Fenix
  - added command !pagoto
  - added command !paskins
  - added command !pafunstuff
  - added command !pastamina
  - updated hitlocation codes to match the last UrT release (4.2.013)
1.14 -  14/07/2013 - Courgette
  - hitlocation codes are provided by the B3 parser if available
1.14.1 - 17/09/2013 - Fenix
  - !pasetnextmap command displays at most 5 map suggestions
1.15 -  09/10/2013 - Courgette
  - !paident command now shows the auth name from the Frozen Sand account (UrT 4.2 only)
1.16 - 10/11/2013 - Fenix
  - refactored plugin syntax to match PEP8 coding style guide
  - more verbose logging on plugin configuration
  - catch all raised exception instead of discarding them
  - correctly use config getFloat method when needed
  - log message consistency (used same pattern for plugin configuration log messages)
  - declare missing attributes
  - flagged some attributes with correct scope (protected)
  - correctly declare lists as lists instead of dictionaries
  - renamed variables using python reserved symbols
  - fixed forceteam %s spectate: spectate is not interpreted by the gamecode
  - added missing command descriptions
  - fixed some in-game message spelling
  - replaced color code ^9 with ^1 -> red in both 4.1 and 4.2
  - make use of self.console.setCvar when possible
1.16.1 - 2014/01/26 - Courgette
  - fix !paset when used with no cvar value
1.17 - 2014/01/27 - Fenix
  - updated !pagear command for iourt42 game: it now works with weapon letters instead of bitmask
1.18 - 2014/01/28 - Courgette
  - !pagear command for iourt42 game accept weapon groups as parameter (all_snipers, all_nades, all_pistols, all_auto)
1.19 - 2014/02/09 - Fenix
  - code cleanup
1.20 - 2014/02/09 - Courgette
  - !pagear accepts multiple parameters
1.21 - 2014/05/11 - Fenix
  - fixed unresolved reference for EVT_CLIENT_RADIO
  - removed some warnings in iourt41.py module
1.22 - 2014/09/19 - Fenix
  - added !pafreeze command: change gametype to Freeze Tag
1.23 - 2014/12/04 - Fenix
  - added command !pacaptain: set the captain status on the given client
  - added command !pasub: set the substitute status on the given client
  - overridden command !paswap in iourt42 module: game server now provides a swap rcon command
  - updated printGear method (iourt42 module) to use the new getWrap implementation
1.24 - 2015/05/13 - Fenix
  - fixed invalid plugin class reference 'requiresParsers' which was crashing B3 on startup
1.25 - 2015/06/23 - Fenix
  - split event handler hooks into multiple functions
  - delay teambalancing to round end in round based gametypes
  - delay skillbalancing to round end in round based gametypes
1.26 - 2015/07/12 - Fenix
  - make use of Plugin.getSetting to load configuration file values
  - minor optimizations

Credit
------

Original author : xlr8or
Contributors : Courgette, mindriot, FSK405|Fear, naixn, BlackMamba, SGT, Fenix
