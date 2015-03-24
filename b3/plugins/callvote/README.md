Callvote Plugin for BigBrotherBot
=================================

Description
-----------

A [BigBrotherBot][B3] plugin which provides advanced features related to the Urban Terror 4.2 callvotes.
With this plugin is possible to specify which B3 group has access to specific callvotes.
Moreover there is the possibility to specify a *special maps list* so that only a certain group of users can
issue callvote for map/nextmap if the level is in the *special maps list*.
Since there is a bit of delay between a /callvote command being issued on the server and the b3 generating the
corresponding event, is not possible to handle everything.
As an example think about this situation:

    Bob  - Team Red
    Tom  - Team Spectator
    Lisa - Team Spectator
 
If Bob issue a **/callvote** command, the callvote will end as soon as the countdown starts since he's the only
active player. Because of this we will perform checks on a callvote being issued on the server just if there is
more than 1 player being able to vote.

In-game user guide
------------------

* **!lastvote** - `display the last callvote issued on the server`
* **!veto** - `cancel the current callvote`