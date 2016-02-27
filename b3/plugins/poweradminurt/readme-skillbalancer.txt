Autobalancer - Skill based

Why?
====
In TDM as the classic autobalancer moves players to balance the count of
players in each team, the skill level of the players is not taken into account.
This leads to unbalanced ("unfair") teams.

To solve this, we introduce a shuffler that creates teams based on skill;
skuffle (skill-shuffle).

How is "skill" measured?
========================
In the first iteration, the bot used the ratio of kills to deaths as a measure
of skill. Good players have higher k/d ratios. When a player joins since there
is no k/d ratio, we used k/d info from XLR stats, if available; if not a
default average value is provided. XLR info was used only in the first five
minutes so the players past performance does not bias how the bot looked at
present performance.   

However, when a player has a spree (either killing or dying rapidly), especially right after they just join causes spikes in the calculation.

In the latest iteration, the bot uses a weighted combination of kill ratio,
team contribution (TC = kills - deaths), and head shot ratio. (for CTF and Bomb
modes other relevant stats are used). This combination is time dampened to
smooth out spikes.

Team balance
============
After the skill is measured for all players, they bot shuffles the players into
red and blue teams till it finds the lowest difference in the sum of skills in
both teams.

Additionally, it tries to distribute snipers between both teams, because a
sniper nest in one team can dominate the game (esp. since SR-8 is a one hit
kill). A sniper is a player carrying a SR-8 or a PSG-1 with a kill ratio more
than 1.2. This way complete n00bs carrying SR8 are ignored.

Once the bot finds a good new set, the players are moved into new teams. The
admin who called !sk stays in the same team so it is not jarring.

A full shuffle is not always called for, so there is a balancer (!bal) that
tries to move not more than 30% of the players. In addition, "forced" players
are left in place (there was probably a good reason why they were forced :)

If !bal is unable to find a reasonably good team in the 30% it will force a
full shuffle, though this is very rare in practise.

The !bal command is intended to replace the !teams command. 

Autobalance
===========
A long pending request was to automatically balance by skill as the game
progresses. The bot needs a metric to decide when to run an autobalance
(thought the teams may be balanced in number the skill level may vary). We
found that players tend to call for !teams or complain when they are killed
very quickly and repeatedly. Also, when players are able to kill very rapidly
and repeatedly they get bored (shooting fish in a barrel).

Additionally, we observed that two l33t players in a team could drastically
shift the balance by keeping players on the other team busy, enabling the other
players in their team to get better scores.

So, it is sufficient to look at the top players kill ratio in each team to see
how the game is being perceived.

So, the bot has a sliding window of 2-4 minutes when it calculate the average
kill ratio for both teams and compares them. The difference shows how the game
is progressing, the higher the difference the more dominant one team is over
the other. The bot lists several levels of difference (from the code)

absdiff = 6*abs(avgdiff)
if 1 <= absdiff < 2:
  word = 'stronger'
if 2 <= absdiff < 3:
  word = 'dominating'
if 3 <= absdiff < 4:
  word = 'overpowering'
if 4 <= absdiff < 5:
  word = 'supreme'
if 5 <= absdiff < 6:
  word = 'Godlike!'
if 6 <= absdiff:
  word = 'probably cheating :P'

By monitoring this difference the bot can take appropriate action. To use this
the administrator uses the !ask [mode] command, where mode is one of:
"0-none",
"1-advise", 
"2-autobalance", 
"3-autoskuffle"

mode 1 is the same as calling !adv, which advises on action
mode 2 uses only the !bal command (which can in turn use !sk if needed)
mode 3 always shuffles

Our recommendation is to use mode 2.

The !ask command is intended to replace the classic count based autobalancer.

We look forward to comments and feedback on these features.

- tomyl & ZeroBIT

