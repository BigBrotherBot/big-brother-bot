Makeroom plugin for BigBrotherBot [![BigBrotherBot](http://i.imgur.com/7sljo4G.png)][B3]
=================================

Description
-----------

This plugin provides a command that will kick the player who last joined server from the lowest group.
This command is useful on popular servers which need to make room for member players.


Commands
--------

`!makeroom` : kick the last non-member player who entered the game
`!makeroomauto <on|off>` : will makeroom every time the server gets full


Installation
------------

 * copy `makeroom.py` into `b3/extplugins`
 * copy `plugin_makeroom.ini` in the same directory as your `b3.xml` file
 * update your main b3 config file with :

```xml
<plugin name="makeroom" config="@conf/plugin_makeroom.ini"/>
```

Changelog
---------

### 1.7 - 2014-08-17
 - add new config file option `retain_free_duration` to retain a freed slot for a while. Any non-member joining the
   server will be kicked unless a member joined or the duration expires

### 1.6 - 2014-08-17
 - config file option `non_member_level` accepts B3 group keywords additionally to B3 group levels
   
### 1.5 - 2011-11-20
 - fix config option "non_member_level" not being read
 - only one kick action can take place at once. If there is a delay set, then wait for the first request
   to complete before accepting a new one
  
### 1.4.1  - 2011-07-11
 - just more debug messages

### 1.4.0 - 2011-07-11
 - fix automated mode where any last connected player would be the one kicked
   whatever his level
  
### 1.3.1 - 2011-07-09
 - fix issue in automation mode where the last player to connect
   would not be kicked if his level is equals to the non_member_level 
  
### 1.3 - 2011-06-20
 - add an automation feature to keep some free slot

### 1.2 - 2011-06-08
 - add info message and delay between info message and actual kick

### 1.1.1 - 2011-05-29
 - fix saving the kick into database

### 1.1 - 2011-05-12
 - messages can be customized in the plugin config file


[B3]: http://www.bigbrotherbot.net/ "BigBrotherBot (B3)"