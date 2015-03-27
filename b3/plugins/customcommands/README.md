b3-plugin-custom-commands
=========================

A [BigBrotherBot][B3] plugin to take easily create new simple commands.
It is a port of the Manu Admin Mod Custom Commands feature to B3.


Configuration
-------------

The config file is composed of eight sections named after each of the B3 group names that allow you to define custom commands that will be
available to player to those particular B3 groups. Those sections are :

- guest commands
- user commands
- regular commands
- mod commands
- admin commands
- fulladmin commands
- senioradmin commands
- superadmin commands

To define a new command, pick the right section depending on who will be able to use it and create a new entry named
after your command. Then define the *rcon command template* to execute for it as a value. 

See the *Placeholders reference* below for more info on what placeholders can be used within your rcon command templates.

```ini
[guest commands]
# define in this section commands that will be available to all players
cookie = tell <ARG:FIND_PLAYER:PID> ^1<PLAYER:NAME> ^7 gave you a ^2COOKIE^7
sry = tell <LAST_VICTIM:PID> sorry mate :|
ns = tell <LAST_KILLER:PID> nice shot !
```

Additionnaly there is section `help` which can be used to provide a short description of each of the defined command.
This short description will be used to create the message that the !help command will return.

```ini
[help]
# define in this section a short description for each of your command.
# This description will be shown when a players uses the !help command
cookie = give a cookie to a player
sry = say you are sorry to your last victim
ns = say 'Nice shot' to your killer
```

Placeholders reference
----------------------

Placeholders are special tokens that you can use in your *rcon command templates*. Those placeholders will be replaced
just before sending your command to the gameserver.

Some placeholders are special and also define a parameter which can be added after your command.

### parameter placeholders

#### `<ARG:FIND_PLAYER:PID>`
  Makes your custom command accept a mandatory parameter which represents a player. The placeholder will be replaced with that player's slot id.

#### `<ARG:FIND_PLAYER:GUID>`
  Makes your custom command accept a mandatory parameter which represents a player. The placeholder will be replaced with that player's GUID.

#### `<ARG:FIND_PLAYER:PBID>`
  Makes your custom command accept a mandatory parameter which represents a player. The placeholder will be replaced with that player's Punkbuster id.

#### `<ARG:FIND_PLAYER:NAME>`
  Makes your custom command accept a mandatory parameter which represents a player. The placeholder will be replaced with that player's cleaned up name.

#### `<ARG:FIND_PLAYER:EXACTNAME>`
  Makes your custom command accept a mandatory parameter which represents a player. The placeholder will be replaced with that player's exact name.

#### `<ARG:FIND_PLAYER:B3ID>`
  Makes your custom command accept a mandatory parameter which represents a player. The placeholder will be replaced with that player B3 id.

#### `<ARG:FIND_MAP>`
  Makes your custom command accept a mandatory parameter which represents a map. The placeholder will be replaced with the map name.

#### `<ARG>`
  Makes your custom command accept a mandatory parameter parameter. The placeholder will be replaced with that parameter.

#### `<ARG:OPT:{TEXT}>`
  Makes your custom command accept an optional parameter. The placeholder will be replaced with that parameter or if not provided by the content of {TEXT}.

  Example :
  ```ini
  hi = say Hi <ARG:OPT:everyone>!
  ```

  `!hi` would produce `say Hi everyone!`

  while `!hi all` would produce `say Hi all!`


### other placeholders

#### `<LAST_KILLER:PID>`
  The placeholder will be replaced with the slot id of the player who killed the player calling the command last.

#### `<LAST_KILLER:GUID>`
  The placeholder will be replaced with the GUID of the player who killed the player calling the command last.

#### `<LAST_KILLER:PBID>`
  The placeholder will be replaced with the Punkbuster id of the player who killed the player calling the command last.

#### `<LAST_KILLER:NAME>`
  The placeholder will be replaced with the cleaned up name of the player who killed the player calling the command last.

#### `<LAST_KILLER:EXACTNAME>`
  The placeholder will be replaced with the name of the player who killed the player calling the command last.

#### `<LAST_KILLER:B3ID>`
  The placeholder will be replaced with the B3 id of the player who killed the player calling the command last.

----
#### `<LAST_VICTIM:PID>`
  The placeholder will be replaced with the slot id of the player who got last killed by the player calling the command.

#### `<LAST_VICTIM:GUID>`
  The placeholder will be replaced with the GUID of the player who got last killed by the player calling the command.

#### `<LAST_VICTIM:PBID>`
  The placeholder will be replaced with the Punkbuster id of the player who got last killed by the player calling the command.

#### `<LAST_VICTIM:NAME>`
  The placeholder will be replaced with the cleaned up name of the player who got last killed by the player calling the command.

#### `<LAST_VICTIM:EXACTNAME>`
  The placeholder will be replaced with the name of the player who got last killed by the player calling the command.

#### `<LAST_VICTIM:B3ID>`
  The placeholder will be replaced with the name of the B3 id who got last killed by the player calling the command.

----
#### `<PLAYER:PID>`
  The placeholder will be replaced with the slot id of the player calling the command.

#### `<PLAYER:GUID>`
  The placeholder will be replaced with the GUID of the player calling the command.

#### `<PLAYER:PBID>`
  The placeholder will be replaced with the Punkbuster id of the player calling the command.

#### `<PLAYER:NAME>`
  The placeholder will be replaced with the cleaned up name of the player calling the command.

#### `<PLAYER:EXACTNAME>`
  The placeholder will be replaced with the name of the player calling the command.

#### `<PLAYER:B3ID>`
  The placeholder will be replaced with the B3 id of the player calling the command.

----
#### `<PLAYER:ADMINGROUP_SHORT>`
  The placeholder will be replaced with the identifier of the admin group which the player calling the command belongs to.

#### `<PLAYER:ADMINGROUP_LONG>`
  Gets replaced with the name of the admin group which the player calling the command belongs to.

#### `<PLAYER:ADMINGROUP_LEVEL>`
  Gets replaced with the level of the admin group which the player calling the command belongs to.


Changelog
---------

### 1.0
2013-03-10
* first release

### 1.1
2014-04-17
* fix: do not execute command using FIND_PLAYER if multiple player names match

### 1.2
2015-03-27
* made customcommands a built-in plugin