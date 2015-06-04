# AFK Plugin [![BigBrotherBot](http://i.imgur.com/7sljo4G.png)][B3]

A [BigBrotherBot][B3] plugin taking care of AFK players on your game server.

This plugin monitors your game server for inactive players. If a player is suspected to be away from keyboard (AFK)
B3 will ask him if he is. If no answer if given and no activity is detected in a timely manner, the player is kicked.


How does the plugin detect AFK?
-------------------------------

Let say `consecutive_deaths_threshold` is `2` and `inactivity_threshold` is `30s` in the plugin config file

- If a player is afk and gets killed a 1st time, nothing happens
- If that player gets killed a second time while having shown no activity in between, he will be checked for inactivity
- Upon being checked, if his last activity is older than 30s, then B3 asks the player if he is AFK
- If no response or activity is detected in the next 20s, then the player is kicked

     
### Urban Terror 4.2

If you are using the modified UrT 4.2 game engine, then you can improve the afk detection by also adding the 
[urtposition B3 plugin](https://github.com/danielepantaleone/b3-plugin-urtposition).

With this modified server and B3 plugin, players will be checked when the game server reports them as standing still
and player movements will be recognised as player activity.


Configuration
-------------

Take a look at the `@conf/plugin_afk.ini` file. All settings are documented in this file.


Changelog
---------

### 1.10 (Fenix) - 2015/04/08
- made the plugin built-in
- correctly check if an event is registered by B3
- make sure to load the AFK plugin after the urtposition one (if available)

### 1.9 - 2015/04/08
- improve support for UrT 4.2 modified servers (with B3 urtposition plugin) 

### 1.8 - 2015/04/01
- `consecutive_deaths_threshold` can be set to `0` to be disabled
- if anyone says the word 'afk' in chat, then all players are checked for inactivity

### 1.7 - 2015/03/31
- add `suspicion_announcement` and `last_chance_delay` to config file

### 1.6 - 2015/03/28
- improve activity detection for Frostbite games 

### 1.5 - 2015/03/26
- players are checked for inactivity after a certain number of consecutive deaths (instead of every x sec)

### 1.4 - 2015/03/25
- do not announce kick made by the afk plugin, B3 already does that when kicking
- improve logs
 
### 1.3 - 2015/03/25
- fix inactivity recognition that would produce false positives in some cases
- cancel all checks on map change or round start to give time to players to load the map

### 1.2 - 2015/03/25
- do not check bots
- add immunity level so admins won't get kicked
- better handling of players disconnection
 
### 1.1 - 2015/03/19
- do not kick last remaining player on the server even if AFK

### 1.0 - 2015/03/19
- initial release


Support
-------

If you have found a bug or have a suggestion for this plugin, please report it on the [B3 forums][Support].


[B3]: http://www.bigbrotherbot.net/ "BigBrotherBot (B3)"
[Support]: http://forum.bigbrotherbot.net/ "Support topic on the B3 forums"

