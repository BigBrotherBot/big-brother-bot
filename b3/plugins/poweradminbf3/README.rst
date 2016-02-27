Power Admin Battlefield 3 for Big Brother Bot
=============================================

Description
-----------

This plugin brings Battlefield 3 specific features to Bigbrotherbot.


Commands
--------

!roundnext
  Switch to next round, without ending current

!roundrestart
  Restart current round

!kill <player> [reason]
  Kill a player without scoring effects

!changeteam <player>
  move <player> to the other team

!swap <player A> [<player B>]
  swap player A's team/squad with player B's team/squad

!setnextmap <map> [, <gamemode> [, <rounds>]]
  select the next map to load after current round. If the map is not in the current map rotation list, then it is added.
  When no gamemode or no rounds is specified, then uses the current values.
  Parameters MUST be separated by a comma ','.

  Usage example :
   - `!setnextmap firestorm, conquest, 2`
   - `!setnextmap bazaar, rush, 1`

!punkbuster <punkbuster command>
  run a punkbuster command

!loadconfig <config file>
  load a config file to change server vars, map list, game modes

!listconfig
  list available config files

!scramble
  (un)request scrambler to scramble teams at next round

!scramblemode <random/score>
  set the scrambling strategy

!autoscramble <off/round/map>
  set the auto-scrambling mode

!unlockmode <all|common|stats|none>
  set the weapons unlocks

!vehicles <on|off>
  (en|dis)able vehicles spawn

!autobalance <off|on>
  (de)activate the autobalancer

!autoassign <off|on>
  (de)activate the autoassigner which puts connecting player into the right team

!endround <winning team id>
  end current round and set winning team

!idle <off|on|min>
  set the idle kicker off/on or to the number of minute you wish

!serverreboot
  restart the BF3 gameserver

!yell <msg>
  yell a message to all players

!yellplayer <player name> <msg>
  yell a message to a given player

!yellteam <msg>
  yell a message to your teammates

!yellsquad <msg>
  yell a message to your squadmates

!nuke <all|us|ru>
  kill all players or players from a given team

!viplist [filter]
  display VIP names
  If `filter` is provided then only display names matching that filter.
  Will display first connected VIPs and then at most the 1st 15 VIP names from the list.

!vips
  display the currently connected VIPs

!vipadd <player>
  add `player` to the VIP list
  If the player you want to add is connected, then you don't have to enter its full name as a parameter.

!vipremove <player>
  remove `player` from the VIP list
  If the player you want to add is connected, then you don't have to enter its full name as a parameter.
  Note that you won't be able to remove admins of higher level that you are.

!vipclear
  clear the VIP list

!vipsave
  write the VIP list to the disk

!vipload
  load the VIP list from the disk

!gunmaster <index>
  set weapon preset for the next Gunmaster round


Other features
--------------

CONFIG MANAGER
~~~~~~~~~~~~~~

Configmanager can automatically load server config scripts at each map change based on current 
gamemode and/or map. It will first look if a b3_<gametype>_<mapname>.cfg exists 
(example: b3_teamdeathmatch0_mp001.cfg) and execute it. If it doesn't exist, it checks for 
b3_<gametype>.cfg (example: b3_rushlarge0.cfg). 

If none of them exist, it will look for b3_main.cfg. This file makes it possible to reset certain 
vars, so always create a b3_main.cfg if you want to enable and use this feature.


Example Scenario
~~~~~~~~~~~~~~~~

You are running a server with mixed gametypes of Conquest and Rush and you want to play Rush maps
without vehicles. What you need to do is to create a file called "b3_rushlarge0.cfg" inside your
configmanager folder with required settings. "vars.vehicleSpawnAllowed false" in this case. Also
make sure you add "vars.vehicleSpawnAllowed True" in your b3_main.cfg so that when a conquest map
comes in rotation vehicles are enabled again.

Please take note that config manager plugin supports only instantaneous server vars.