#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
#
#    2014/05/02 - 1.4.1 - Fenix
#    * Make use of the new getCmd function from functions module
#    2013/10/30 - 1.4 Courgette
#    * fix bug when using the !testscore command against a team mate
#    * display topstat and topxp awards on EVT_GAME_MAP_CHANGE event additionally to the EVT_GAME_EXIT event.
#    04/14/2011 - 1.3.7 Courgette
#    * fix bug with !topstats and  !topxp
#    04/13/2011 - 1.3.6 Courgette
#    * import missing string module
#    10/30/2010 - 1.3.5 GrosBedo
#    * added show_awards and show_awards_xp
#    10/20/2010 - 1.3.4 GrosBedo
#    * clientKill and clientDamage separated from clientKillTeam and clientDamageTeam
#    10/20/2010 - 1.3.3 GrosBedo
#    * No more teamKills if team is unknown (eg: parser can't detect the team)
#    8/15/2010 - 1.3.2 GrosBedo
#    * Fixed disabling reset xp option
#    8/14/2010 - 1.3.1 Courgette
#    * move commands in the commands section of config
#    * allow to define aliases in config
#    * add automated tests
#    8/14/2010 - 1.3.0 GrosBedo
#    * Stats are now cleared at the beginning of next round (so they are still available at scoreboard)
#    * Moved the parameters to the xml config file (and added more)
#    * Added XP score and !topxp
#    * Setting to enable/disable score reset at round start
#    9/5/2005 - 1.2.0 - ThorN
#    * Added !topstats command
#    8/29/2005 - 1.1.0 - ThorN
#    * Converted to use new event handlers

from ConfigParser import NoOptionError, NoSectionError
import string
import b3
import b3.events
import b3.plugin

from b3.functions import getCmd

__author__ = 'ThorN, GrosBedo'
__version__ = '1.4.1'


class StatsPlugin(b3.plugin.Plugin):
    _adminPlugin = None

    def __init__(self, console, config=None):
        b3.plugin.Plugin.__init__(self, console, config)
        self.mapstatslevel = None
        self.testscorelevel = None
        self.topstatslevel = None
        self.topxplevel = None
        self.startPoints = None
        self.resetscore = None
        self.resetxp = None
        self.show_awards = None
        self.show_awards_xp = None

    def load_default_config(self):
        self.mapstatslevel = 0
        self.testscorelevel = 0
        self.topstatslevel = 2
        self.topxplevel = 2
        self.startPoints = 100
        self.resetscore = False
        self.resetxp = False
        self.show_awards = False
        self.show_awards_xp = False

    def onLoadConfig(self):
        self.load_default_config()

        try:
            commands_options = self.config.options("commands")
        except NoSectionError:
            commands_options = []

        def load_command_level(cmd_name):
            matching_options = [x for x in commands_options if x.startswith('%s-' % cmd_name)]
            if len(matching_options):
                option_name = matching_options[0]
            else:
                option_name = cmd_name
            return self.config.getint('commands', option_name)

        try:
            self.mapstatslevel = load_command_level('mapstats')
        except NoOptionError:
            pass
        except Exception, err:
            self.error(err)
        self.info('commands::mapstats level: %s', self.mapstatslevel)

        try:
            self.testscorelevel = load_command_level('testscore')
        except NoOptionError:
            pass
        except Exception, err:
            self.error(err)
        self.info('commands::testscore level: %s', self.testscorelevel)

        try:
            self.topstatslevel = load_command_level('topstats')
        except NoOptionError:
            pass
        except Exception, err:
            self.error(err)
        self.info('commands::topstats level: %s', self.topstatslevel)

        try:
            self.topxplevel = load_command_level('topxp')
        except NoOptionError:
            pass
        except Exception, err:
            self.error(err)
        self.info('commands::topxp level: %s', self.topxplevel)


        try:
            self.startPoints = self.config.getint('settings', 'startPoints')
        except NoOptionError:
            pass
        except Exception, err:
            self.error(err)
        self.info('settings::startPoints: %s', self.startPoints)

        try:
            self.resetscore = self.config.getboolean('settings', 'resetscore')
        except NoOptionError:
            pass
        except Exception, err:
            self.error(err)
        self.info('settings::resetscore: %s', self.resetscore)

        try:
            self.resetxp = self.config.getboolean('settings', 'resetxp')
        except NoOptionError:
            pass
        except Exception, err:
            self.error(err)
        self.info('settings::resetxp: %s', self.resetxp)

        try:
            self.show_awards = self.config.getboolean('settings', 'show_awards')
        except NoOptionError:
            pass
        except Exception, err:
            self.error(err)
        self.info('settings::show_awards: %s', self.show_awards)

        try:
            self.show_awards_xp = self.config.getboolean('settings', 'show_awards_xp')
        except NoOptionError:
            pass
        except Exception, err:
            self.error(err)
        self.info('settings::show_awards_xp: %s', self.show_awards_xp)

    def onStartup(self):
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            self.critical('Cannot find the admin plugin. Disabling Stats plugin')
            self.disable()
            return

        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp
                func = getCmd(self, cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_KILL)
        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE)
        self.registerEvent(b3.events.EVT_GAME_EXIT)  # used to show awards at the end of round
        self.registerEvent(b3.events.EVT_GAME_MAP_CHANGE)  # used to show awards at the end of round
        self.registerEvent(b3.events.EVT_GAME_ROUND_START) # better to reinit stats at round start than round end, so that players can still query their stats at the end

    def onEvent(self, event):
        if event.type in (b3.events.EVT_GAME_EXIT, b3.events.EVT_GAME_MAP_CHANGE):
            if self.show_awards:
                self.cmd_topstats(None)
            if self.show_awards_xp:
                self.cmd_topxp(None)
        elif event.type == b3.events.EVT_GAME_ROUND_START:
            self.debug('Map Start: clearing stats')
            for cid, c in self.console.clients.items():
                if c.maxLevel >= self.mapstatslevel:
                    try:
                        c.setvar(self, 'shotsTeamHit', 0)
                        c.setvar(self, 'damageTeamHit', 0)
                        c.setvar(self, 'shotsHit', 0)
                        c.setvar(self, 'damageHit', 0)
                        c.setvar(self, 'shotsGot', 0)
                        c.setvar(self, 'damageGot', 0)
                        c.setvar(self, 'teamKills', 0)
                        c.setvar(self, 'kills', 0)
                        c.setvar(self, 'deaths', 0)

                        if self.resetscore:
                            # skill points are reset at the beginning of each map
                            c.setvar(self, 'pointsLost', 0)
                            c.setvar(self, 'pointsWon', 0)
                            c.setvar(self, 'points', self.startPoints)
                        if self.resetxp:
                            c.setvar(self, 'experience', 0)
                        else:
                            c.var(self, 'oldexperience', 0).value += c.var(self, 'experience', 0).value
                            c.setvar(self, 'experience', 0)
                    except Exception, err:
                        self.error(err)
        elif event.client:
            if event.type == b3.events.EVT_CLIENT_DAMAGE:
                self.clientDamage(event.client, event.target, int(event.data[0]))
            elif event.type == b3.events.EVT_CLIENT_DAMAGE_TEAM:
                self.clientDamageTeam(event.client, event.target, int(event.data[0]))
            elif event.type == b3.events.EVT_CLIENT_KILL:
                self.clientKill(event.client, event.target, int(event.data[0]))
            elif event.type == b3.events.EVT_CLIENT_KILL_TEAM:
                self.clientKillTeam(event.client, event.target, int(event.data[0]))

    def clientDamage(self, killer, victim, points):
        if points > 100:
            points = 100

        killer.var(self, 'shotsHit', 0).value  += 1
        killer.var(self, 'damageHit', 0).value += points

        victim.var(self, 'shotsGot', 0).value  += 1
        victim.var(self, 'damageGot', 0).value += points
        return

    def clientDamageTeam(self, killer, victim, points):
        if points > 100:
            points = 100

        killer.var(self, 'shotsTeamHit', 0).value  += 1
        killer.var(self, 'damageTeamHit', 0).value += points
        return

    def clientKill(self, killer, victim, points):
        if points > 100:
            points = 100

        killer.var(self, 'shotsHit', 0).value  += 1
        killer.var(self, 'damageHit', 0).value += points

        victim.var(self, 'shotsGot', 0).value  += 1
        victim.var(self, 'damageGot', 0).value += points

        killer.var(self, 'kills', 0).value  += 1
        victim.var(self, 'deaths', 0).value += 1

        score = self.score(killer, victim)
        killer.var(self, 'points', self.startPoints).value += score
        killer.var(self, 'pointsWon', 0).value += score

        victim.var(self, 'points', self.startPoints).value -= score
        victim.var(self, 'pointsLost', 0).value += score

        self.updateXP(killer)
        self.updateXP(victim)
        
    def clientKillTeam(self, killer, victim, points):
        if points > 100:
            points = 100

        killer.var(self, 'shotsTeamHit', 0).value  += 1
        killer.var(self, 'damageTeamHit', 0).value += points

        killer.var(self, 'teamKills', 0).value += 1

        score = self.score(killer, victim)
        killer.var(self, 'points', self.startPoints).value -= score
        killer.var(self, 'pointsLost', 0).value += score

        self.updateXP(killer)
        self.updateXP(victim)

    def updateXP(self, sclient):
        realpoints = sclient.var(self, 'pointsWon', 0).value - sclient.var(self, 'pointsLost', 0).value
        if sclient.var(self, 'deaths', 0).value != 0:
            experience = (sclient.var(self, 'kills', 0).value * realpoints) / sclient.var(self, 'deaths', 0).value
        else:
            experience = sclient.var(self, 'kills', 0).value * realpoints
        sclient.var(self, 'experience', 0).value = experience

    def cmd_mapstats(self, data, client, cmd=None):
        """\
        [<name>] - list a players stats for the map
        """
        if data:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if not sclient:
                return
        else:
            sclient = client

        message = '^3Stats ^7[ %s ^7] K ^2%s ^7D ^3%s ^7TK ^1%s ^7Dmg ^5%s ^7Skill ^3%1.02f ^7XP ^6%s' % (sclient.exactName, sclient.var(self, 'kills', 0).value, sclient.var(self, 'deaths', 0).value, sclient.var(self, 'teamKills', 0).value, sclient.var(self, 'damageHit', 0).value, round(sclient.var(self, 'points', self.startPoints).value, 2), round(sclient.var(self, 'oldexperience', 0).value + sclient.var(self, 'experience', 0).value, 2))
        cmd.sayLoudOrPM(client, message)

    def cmd_testscore(self, data, client, cmd=None):
        """\
        <name> - how much skill points you will get if you kill the player
        """

        if not data:
            client.message('^7You must supply a player name to test')
            return

        sclient = self._adminPlugin.findClientPrompt(data, client)
        if not sclient:
            return
        elif sclient == client:
            client.message('^7You don\'t get points for killing yourself')
        elif sclient.team in (b3.TEAM_BLUE, b3.TEAM_RED) and sclient.team == client.team:
            client.message('^7You don\'t get points for killing a team mate')
        else:
            cmd.sayLoudOrPM(client, '^3Stats: ^7%s^7 will get ^3%s ^7skill points for killing %s^7' %
                                    (client.exactName, self.score(client, sclient), sclient.exactName))

    def cmd_topstats(self, data, client=None, cmd=None):
        """\
        List the top 5 map-stats players
        """
        self.debug('Haha')
        scores = []
        for c in self.console.clients.getList():
            if c.isvar(self, 'points'):
                scores.append((c.exactName, round(c.var(self, 'points', self.startPoints).value, 2)))
        
        if len(scores):
            tmplist = [(x[1], x) for x in scores]
            tmplist.sort()
            scores = [x for (key, x) in tmplist]
            scores.reverse()

            i = 0
            results = []
            for name, score in scores:
                i += 1

                if i >= 6:
                    break

                results.append('^3#%s^7 %s ^7[^3%s^7]' % (i, name, score))
                
            if client:        
                client.message('^3Top Stats:^7 %s' % string.join(results,', '))
            else:
                self.console.say('^3Top Stats:^7 %s' % string.join(results,', '))
        else:
            client.message('^3Stats: ^7No top players')

    def cmd_topxp(self, data, client=None, cmd=None):
        """\
        List the top 5 map-stats most experienced players
        """

        scores = []
        for c in self.console.clients.getList():
            if c.isvar(self, 'experience'):
                scores.append((c.exactName, round(c.var(self, 'experience', self.startPoints).value, 2)))

        if len(scores):
            tmplist = [(x[1], x) for x in scores]
            tmplist.sort()
            scores = [x for (key, x) in tmplist]
            scores.reverse()

            i = 0
            results = []
            for name, score in scores:
                i += 1

                if i >= 6:
                    break

                results.append('^3#%s^7 %s ^7[^3%s^7]' % (i, name, score))

            if client:
                client.message('^3Top Experienced Players:^7 %s' % string.join(results, ', '))
            else:
                self.console.say('^3Top Experienced Players:^7 %s' % string.join(results, ', '))
        else:
            client.message('^3Stats: ^7No top experienced players')

    def score(self, killer, victim):
        k = int(killer.var(self, 'points', self.startPoints).value)
        v = int(victim.var(self, 'points', self.startPoints).value)

        if k < 1:
            k = 1.00
        if v < 1:
            v = 1.00

        vshift = (float(v) / float(k)) / 2

        points = (15.00 * vshift) + 5

        if points < 1:
            points = 1.00
        elif points > 100:
            points = 100.00

        return round(points, 2)
