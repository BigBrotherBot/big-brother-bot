Power Admin Medal of Honor plugin for Big Brother Bot (www.bigbrotherbot.net)
=============================================================================

Description
-----------
This plugin brings Medal of Honor specific features to Bigbrotherbot.

Commands
--------

!pb_sv_command <punkbuster command> - Execute a punkbuster command
!runnextround - Switch to next round, without ending current
!restartround - Restart current round
!kill <player> - Kill a player without scoring effects
!teams - Make the teams balanced
!teambalance <on/off> - Set teambalancer on/off
!changeteam [<player>] - change a player to the other team
!swap <playerA> <playerB> - swap teams for player A and B (if in different teams)
!scramble - schedule teams scramble at next round
!scramblemode <random|score> - how to scramble ? randomly, by scores
!autoscramble <off|round|map> - auto scramble at each round/map change
!match <on/off> - Set server match mode on/off
!spect <player> - Send a player to spectator mode
!reserveslot <player>
!unreserveslot <player>
!setnextmap <map name>

Changelog
---------

* v0.3 - 2010/10/24 - make it compatible with v1.4.0
* v0.2 - 2010/10/24 - beta release for testing and feedbacks
* v0.4 - 2010/10/24 - Courgette (thanks to GrossKopf, foxinabox & Darkskys for tests and feedbacks)
    * fix misspelling
    * fix teambalancing mechanism
    * add 2 settings for the teambalancer in config file
    * fix !changeteam command crash
    * !pb_sv_command : when PB respond with an error, displays the PB response instead of "There was an error processing your command"
    * !runnextround : when MoH respond with an error message display that message instead of "There was an error processing your command"
    * !restartround : when MoH respond with an error message display that message instead of "There was an error processing your command"
* v0.5 - 2010/10/24 - Courgette
    * minor fix
    * major fix to the admin.movePlayer MoH command. This affected all team balancing features
* v0.6 - 2010/10/25 - Courgette
    * fix !runnextround
    * fix !restartround
    * matchmod will now restart round when count down is finished
* v0.7 - 2010/10/28 - Courgette
    * prevent autobalancing right after a player disconnected
    * attempt to be more fair in the choice of the player to move over to avoid the same player being switch consecutively
    * add command !swap to swap a player with another one
* v0.8 - 2010/10/25 - Courgette
    * when balancing, broadcast who get balanced
* v0.9 - 2010/11/01 - Courgette
    * add !scramble command to plan team scrambing on next round start
* v0.10 - 2010/11/04 - Courgette
    * add !scramblemode, !autoscramble
    * can scramble based on player scores
* v0.11 - 2010/11/04 - Courgette
    * fix auto scramble at map change
    * fix scrambling strategy 'by scores'
* v0.12 - 2010/11/06 - Courgette
    * fix !scramble which would scramble each following round (whatever !autoscramble)
    * fix !autoscramble map
* v0.13 - 2010/11/09 - Courgette
    * add maxlevel for the teambalancer
* v1.0 - 2010/11/14 - Courgette
    * add !spect command
    * add !reserveslot and !unreserveslot commands
    * add !setnextmap command  
* v1.1 - 2011/06/04 - Courgette
    * fix teambalancer which would swap the first instead of the last guy who changed teams
* v1.2 - 2015/05/19 - Fenix
    * make poweradminmoh a built-in plugin
* v1.3 - 2015/07/31 - Thomas LEVEIL
    * convert config file to ini format, `matchmode` config section added