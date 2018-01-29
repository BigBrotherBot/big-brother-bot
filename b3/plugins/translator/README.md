Translator Plugin for BigBrotherBot
===================================

Description
-----------

A BigBrotherBot plugin which is capable o translating in-game chat messages into a specified language.

Installation
------------

* install langdetect python module (from pypi) to support exclude_language setting.

In-game user guide
------------------

* **!translate [&lt;source&gt;]*[&lt;target&gt;] &lt;message&gt;** `translate a message`
* **!translast [&lt;target&gt;]** `translate the last available sentence from the chat`
* **!transauto &lt;on|off&gt;** `turn on/off the automatic translation` - STRONGLY DISADVISED (unless you would like your server to get banned from Google...)
* **!translang** `display the list of available language codes`

It is advised to increase min_time_between to reduce the likelihood of a google temporary ban.
