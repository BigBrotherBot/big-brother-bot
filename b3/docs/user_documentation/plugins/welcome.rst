.. index:: Plugins; Welcome, Welcome plugin
.. _plugin-welcome:

Welcome
=======

The welcome plugin will welcome players that join the game server.

You can define different messages that will be sent privately to players depending on if it is the first time
the player joins the server of if he is a registered player.

Also you can define announcement messages that are broadcasted to all players when a player joins for the first time
or if he is a registered player.

Finally you can allow players to define their own custom announcement message that will be displayed to all on joining
the server. This custom greeting is to be set with the :command:`!greeting` command.

.. note::
  The plugin won't welcome anyone in the 5 first minutes after B3 started.


Configuration
-------------


Commands
^^^^^^^^


:index:`greeting`
"""""""""""""""""

Group/level required to be able to use the :command:`!greeting` command.

expected values
  any group keyword or any group level, see :ref:`groups`

default value
  ``mod``



Settings
^^^^^^^^


:index:`welcome_first`
""""""""""""""""""""""

Define if private message welcoming first time players will be sent.

expected values
  ``yes`` or ``no``

default value
  ``yes``


:index:`welcome_newb`
"""""""""""""""""""""

Define if private message welcoming newbie players will be sent.

expected values
  ``yes`` or ``no``

default value
  ``yes``


:index:`welcome_user`
"""""""""""""""""""""

Define if private message welcoming registered players will be sent.

expected values
  ``yes`` or ``no``

default value
  ``yes``


:index:`announce_first`
"""""""""""""""""""""""

Define if a message welcoming first time players will be broadcasted.

expected values
  ``yes`` or ``no``

default value
  ``yes``


:index:`announce_user`
""""""""""""""""""""""

Define if a message welcoming registered players will be broadcasted.

expected values
  ``yes`` or ``no``

default value
  ``yes``


:index:`show_user_greeting`
"""""""""""""""""""""""""""

Define if players custom greeting message will be broadcasted.

expected values
  ``yes`` or ``no``

default value
  ``yes``



:index:`newb_connections`
"""""""""""""""""""""""""

Define the maximum number of connections above which a non registered player won't be considered a newbie anymore.

expected values
  integer greater than 0

default value
  ``15``



:index:`delay`
""""""""""""""

Define the delay in second after which the welcome message will be sent when a player connects.

expected values
  integer greater than 0

default value
  ``30``



:index:`min_gap`
""""""""""""""""

Define the duration in seconds the bot must wait before welcoming a player again.

i.e.: if you set min_gap to 3600 seconds (one hour) then the bot will not welcome a player more than once per hour.

expected values
  integer greater than 0

default value
  ``3600``


messages
^^^^^^^^

:index:`first`
""""""""""""""

Define the message to sent privately to joining first time players.

The text can contain `placeholders`_ that will be replaced just before sending the message.


expected values
  text

default value
  ``^7Welcome $name^7, this must be your first visit, you are player ^3#$id. Type !help for help``


:index:`newb`
"""""""""""""

Define the message to sent privately to joining newbie players.
Newbie players are players with less than `newb_connections`_ connections.

The text can contain `placeholders`_ that will be replaced just before sending the message.

expected values
  text

default value
  ``^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit. Type !register in chat to register. Type !help for help``



:index:`user`
"""""""""""""

Define the message to sent privately to joining registered players.

The text can contain `placeholders`_ that will be replaced just before sending the message.

expected values
  text

default value
  ``^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit^7, you're a ^2$group^7, played $connections times``



:index:`announce_first`
"""""""""""""""""""""""

Define the message to broadcast when a first time player joins.

The text can contain `placeholders`_ that will be replaced just before sending the message.

expected values
  text

default value
  ``^7Everyone welcome $name^7, player number ^3#$id^7, to the server``



:index:`announce_user`
""""""""""""""""""""""

Define the message to broadcast when a registered player joins.

The text can contain `placeholders`_ that will be replaced just before sending the message.

expected values
  text

default value
  ``^7Everyone welcome back $name^7, player number ^3#$id^7, to the server, played $connections times``



:index:`greeting`
"""""""""""""""""

Define the message to broadcast when a player having defined a custom greeting message with the :command:`!greeting` joins.

The text can contain the following placeholders that will be replaced just before sending the message:

+--------------+--------------------------------------------------------------------------+
| placeholder  | replacement                                                              |
+==============+==========================================================================+
| $name        | the name of the joining player                                           |
+--------------+--------------------------------------------------------------------------+
| $maxLevel    | the level of the joining player                                          |
+--------------+--------------------------------------------------------------------------+
| $group       | the group of the joining player                                          |
+--------------+--------------------------------------------------------------------------+
| $connections | the number of connections the joining player already made on that server |
+--------------+--------------------------------------------------------------------------+

expected values
  text with a special placeholder ``$greeting`` which will get replaced with the player custom greeting message.

default value
  ``^7$name^7 joined: $greeting``



:index:`greeting_empty`
"""""""""""""""""""""""

Feedback message for the :command:`!greeting` command.

expected values
  text

default value
  ``^7You have no greeting set``



:index:`greeting_yours`
"""""""""""""""""""""""

Feedback message for the :command:`!greeting` command.

expected values
  text with a ``%s`` placeholder which will get replaced by the current user custom greeting message.

default value
  ``^7Your greeting is %s``


:index:`greeting_bad`
"""""""""""""""""""""

Feedback message for the :command:`!greeting` command.

expected values
  text with a ``%s`` placeholder which will get replaced with details on what went wrong.

default value
  ``^7Greeting is not formatted properly: %s``



:index:`greeting_changed`
"""""""""""""""""""""""""

Feedback message for the :command:`!greeting` command.

expected values
  text with a ``%s`` placeholder which will get replaced by the new user custom greeting message.

default value
  ``^7Greeting changed to: %s``



:index:`greeting_cleared`
"""""""""""""""""""""""""

Feedback message for the :command:`!greeting` command.

expected values
  text

default value
  ``^7Greeting cleared``



Placeholders
------------

The text can contain the following placeholders that will be replaced just before sending the message:

+--------------+--------------------------------------------------------------------------+
| placeholder  | replacement                                                              |
+==============+==========================================================================+
| $name        | the name of the joining player                                           |
+--------------+--------------------------------------------------------------------------+
| $id          | the B3 id number of the joining player                                   |
+--------------+--------------------------------------------------------------------------+
| $group       | the group of the joining player                                          |
+--------------+--------------------------------------------------------------------------+
| $level       | the group level of the joining player                                    |
+--------------+--------------------------------------------------------------------------+
| $lastVisit   | the date / time of the last connection of the joining player             |
+--------------+--------------------------------------------------------------------------+
| $connections | the number of connections the joining player already made on that server |
+--------------+--------------------------------------------------------------------------+



Commands
--------


.. index:: single: !greeting

greeting
^^^^^^^^


The `!greeting` command allows players to set / clear their custom greeting message.

.. rubric:: default required level

*mod*

.. rubric:: usage

:command:`!greeting`

Shows the current player's custom greeting message.

:command:`!greeting <message>`

Sets *<player>* as the new player's custom greeting message.

:command:`!greeting none`

Clears the player's custom greeting message.

