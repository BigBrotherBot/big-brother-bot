Chatlogger Plugin for Big Brother Bot (www.bigbrotherbot.net)
=============================================================

By Courgette


Description
-----------

This plugin logs to database and/or file all clients' messages (chat, team chat, private chat).
Forum : http://www.bigbrotherbot.com/forums/index.php?topic=423


Changelog
---------

### 1.5 - 26/03/2015 - Fenix
 - updated plugin for built in release
 - do not log callvote events: callvote plugin will deal with them
 - support sqlite and postgresql storage protocols
 - removed possibility to change database table names: allow table auto generation
 - make use of the new event handlers

### 1.4 - 18/08/2013 - Courgette
 - can now save SQUAD chat (for games that have squads)
 - UPGRADE NOTE: run the `upgrade_1.4.sql` script on your MySQL database
 
### 1.3.2 - 18/08/2013 - Courgette
 - plugin config file is now a .ini file

### 1.3.1 - 12/08/2012 - Courgette
 - gracefully fallback on default values when part of the config is missing

### 1.3 - 09/08/2012 - Courgette
 - now also log events EVT_CLIENT_RADIO, EVT_CLIENT_CALLVOTE and EVT_CLIENT_VOTE when available

### 1.2 - 03/03/2012 - OliverWieland
 - add new setting max_age_cmd

### 1.1.3 - 20/12/2011 - Courgette
 - fixes #2 : Error DELETE FROM cmdlog WHERE msg_time (thanks to Mariodu62)

### 1.1.2 - 12/09/2011 - Courgette
 - start without failure even if the plugin is loaded before the admin plugin
 - do not fail to handle SQLite database errors

### 1.1.1 - 01/09/2011 - Courgette
 - refactoring to reduce code duplication
 - better test coverage
 - update authors credit

### 1.1.0 - 01/09/2011 - BlackMamba
 - log commands to db

### 1.0.0 - 16/04/2011 - Courgette
 - can log to a file instead of logging to db (or both)
 - requires B3 1.6+

### 0.2.1 - 11/04/2011 - Courgette
 - update the sql script to use the utf8 charset

### 0.2.0 - 22/12/2008 - Courgette
 - allow to use a customized table name for storing the
   log to database. Usefull if multiple instances of the
   bot share the same database.
   Thanks to Eire.32 for bringing up the idea and testing.

### 0.1.2 - 7/11/2008 - xlr8or
 - added missing 'import b3.timezones'

### 0.1.1 - 13/09/2008
 - in config, the hour defined for the purge is now understood in the timezone defined in the main B3 config file (before, was understood as UTC time)
 - fix mistake in log text
 
### 0.1.0 - 14/08/2008
 - fix security issue with player names or messages containing double quote or antislash characters (Thx to Anubis for report and tests)
 - option to setup a daily purge of old messages to keep your database size reasonable
 
### 0.0.1 - 28/07/2008
 - manage say, teamsay and privatesay messages