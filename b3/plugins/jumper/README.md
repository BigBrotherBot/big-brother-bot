Jumper Plugin for BigBrotherBot
===============================

Description
-----------

A [BigBrotherBot][B3] plugin provides an advanced statistics system for Urban Terror 4.2 Jump servers.
The plugin is capable of storing permanently all the timings performed during jump runs, offering also the
possibility to list player and map records.

Demo auto-recording
-------------------

In order for the demo autorecording feature to work properly, b3 needs to have privileges of **removing** demo files
from your UrT 4.2.x server directory, so make sure to give the `b3` user correct writing permissions. More over to let
the plugin autorecord serverside demos, you would need to enable the `urtserversidedemo` plugin in B3 main configuration
file.

Commands reference
------------------

* **!delrecord [&lt;client&gt;] [&lt;mapname&gt;]** - `delete the best run(s) of a client on a specific map`
* **!map &lt;mapname&gt;** - `change the server to a new map`
* **!maps** - `display all the available maps on the server`
* **!maprecord [&lt;mapname&gt;]** - `display map best jump run(s)`
* **!mapinfo [&lt;mapname&gt;]** - `display map specific informations`
* **!record [&lt;client&gt;] [&lt;mapname&gt;]** - `display the best run(s) of a client on a specific map`
* **!setway &lt;way-id&gt; &lt;name&gt;** - `set a name for the specified way id`
* **!setnextmap &lt;mapname&gt;** - `set the next map`
* **!topruns [&lt;mapname&gt;]** - `display map top run(s)`

Credits
-------

Since version 2.1 this plugin provides a new command, **!jmpmapinfo**, which retrieves maps information (such as
author, release date, level, etc.) and display them in-game. This has been made possible thanks to the
[Urt Jumpers](http://www.urtjumpers.com/) community which provides such data.