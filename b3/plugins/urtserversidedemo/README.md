UrT Server Side Demo Plugin for BigBrotherBot
=============================================

A [BigBrotherBot][B3] plugin to take advantage of the Urban Terror 4.2 server-side demo recording feature.
For every server-side demo started, you will find in the B3 log a _INFO_ line with demo filename, player name, player 
guid and player ip.

Commands reference
------------------

#### !startserverdemo \<player\>

Starts a server-side demo.

If _player_ is `all`, then all connected players will be recorded and future connecting players will also be recorded.
Else, starts recording a demo for the given player only.

#### !stopserverdemo \<player\>

Stops recording a server-side demo.

If _player_ is `all`, then all currently recording server-side demos are stopped and future connecting players won't get automatically recorded.
Else, stops all currently recording demos.

#### HaxBusterUrt plugin

This plugin can get notifications from the HaxBusterUrt plugin that a connecting player is suspected of cheating. By
setting a value for `demo_duration` in the `haxbusterurt` section of your config file, demos will automatically be taken 
for such players.  
Of course you need to have the HaxBusterUrt plugin installed and loaded for this to work, and furthermore, you need to
make sure that the HaxBusterUrt plugin is loaded **before** this plugin.

See the HaxBusterUrt plugin at : http://forum.bigbrotherbot.net/downloads/?sa=view;down=61

#### Follow plugin

This plugin can get notifications from the Follow plugin when a player is found in the follow list. By
setting a value for `demo_duration` in the `follow` section of your config file, demos will automatically be taken for
such players.  
Of course you need to have the Follow plugin installed and loaded for this to work, and furthermore, you need to
make sure that the HaxBusterUrt plugin is loaded **before** this plugin.

See the Follow plugin at : http://forum.bigbrotherbot.net/downloads/?sa=view;down=52

Changelog
---------

### 1.0
2012-05-23
* add commands __!startserverdemo__ and __!stopserverdemo__
* able to auto start demo of connecting players if `!startserverdemo all` was called

### 2.0
2012-10-08
* when trying to start a demo on a player which is not fully connected, will wait and retry when the player joins
* can detect the HaxBusterUrt plugin and auto-start demo for player suspected of cheating
* support both demo file extensions : dm_68 and urtdemo

### 2.1
2012-10-09
* can detect the Follow plugin and auto-start demo for player found in the follow list. See http://forum.bigbrotherbot.net/releases/follow-users-plugin/

### 2.2
205-03-24
* adapted plugin for built-in release
* expose demomanager visibility (public)
* make use of the new event handler system
* make use of the new onEnable, onDisable plugin class hooks