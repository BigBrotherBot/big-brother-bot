Banlist plugin for Big Brother Bot (www.bigbrotherbot.net)
==========================================================

Description
-----------

This plugin as been made to allow easy sharing of cheater banlist between clans.
It also as the advantage of not requiering any game server reboot after banlist updates.

You can enforce an unlimited number of banlists and whitelists which can be composed of either IP addresses
GUIDs or PBids.
It also can work with banlists from Rules of Combat www.rulesofcombat.com

Features :
----------

### IP banlists / whitelists :

 * specify as many banlist files as you want.
 * understands range ip ban. (ie: banlist file having IP addresses ending with '.0', '.0.0' or '.0.0.0')
 * option to enfore range IP ban as if all ip addresses where ending with ".0"
 
### GUID banlists / whitelists :

 * specify as many guid banlist files as you want.

### PBid banlists / whitelists :

 * specify as many PBid banlist files as you want.

### Rules of Combat banlists :

 * enforce Homefront banlists from www.rulesofcombat.com

### For all banlists :

 * an url can be specified to hourly update.
 * a specific message can be set to be displayed upon kick. (keywords understood: $id, $ip, $guid, $pbid, $name)


Installation
------------

 * copy banlist.py into b3/extplugins
 * copy plugin_banlist.xml in the same directory as your b3.xml
 * update your main b3 config file with :

    ```
    <plugin name="banlist" config="@conf/plugin_banlist.xml"/>
    ```

Support
-------

http://forum.bigbrotherbot.net/index.php?topic=389.0
