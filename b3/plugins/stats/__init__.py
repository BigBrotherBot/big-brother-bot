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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import b3
import b3.events
import b3.plugin
import string

from b3.functions import getCmd
from ConfigParser import NoOptionError, NoSectionError

__author__ = 'ThorN, GrosBedo'
__version__ = '1.5.1'


class StatsPlugin(b3.plugin.Plugin):

    _adminPlugin = None

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def __init__(self, console, config=None):
        """
        Object constructor.
        :param console: The console instance
        :param config: The plugin configuration
        """
        b3.plugin.Plugin.__init__(self, console, config)
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
        """
        Load plugin configuration.
        """
        commands_options = []
        if self.config.has_section("commands"):
            try:
                commands_options = self.config.options("commands")
            except:
                pass

        def load_command_level(cmd_name):
            """
            Load a command level.
            :param cmd_name: The command name
            """
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
        except Exception, e:
            self.error(e)

        self.info('commands::mapstats level: %s', self.mapstatslevel)

        try:
            self.testscorelevel = load_command_level('testscore')
        except NoOptionError:
            pass
        except Exception, e:
            self.error(e)

        self.info('commands::testscore level: %s', self.testscorelevel)

        try:
            self.topstatslevel = load_command_level('topstats')
        except NoOptionError:
            pass
        except Exception, e:
            self.error(e)

        self.info('commands::topstats level: %s', self.topstatslevel)

        try:
            self.topxplevel = load_command_level('topxp')
        except NoOptionError:
            pass
        except Exception, e:
            self.error(e)

        self.info('commands::topxp level: %s', self.topxplevel)

        try:
            self.startPoints = self.config.getint('settings', 'startPoints')
            self.debug('loaded settings/startPoints: %s' % self.startPoints)
        except NoOptionError:
            self.warning('could not find settings/startPoints in config file, '
                         'using default: %s' % self.startPoints)
        except ValueError, e:
            self.error('could not load settings/startPoints config value: %s' % e)
            self.debug('using default value (%s) for settings/startPoints' % self.startPoints)

        try:
            self.resetscore = self.config.getboolean('settings', 'resetscore')
            self.debug('loaded settings/resetscore: %s' % self.resetscore)
        except NoOptionError:
            self.warning('could not find settings/resetscore in config file, '
                         'using default: %s' % self.resetscore)
        except ValueError, e:
            self.error('could not load settings/resetscore config value: %s' % e)
            self.debug('using default value (%s) for settings/resetscore' % self.resetscore)

        try:
            self.resetxp = self.config.getboolean('settings', 'resetxp')
            self.debug('loaded settings/resetscore: %s' % self.resetxp)
        except NoOptionError:
            self.warning('could not find settings/resetxp in config file, '
                         'using default: %s' % self.resetxp)
        except ValueError, e:
            self.error('could not load settings/resetxp config value: %s' % e)
            self.debug('using default value (%s) for settings/resetxp' % self.resetxp)

        try:
            self.show_awards = self.config.getboolean('settings', 'show_awards')
            self.debug('loaded settings/show_awards: %s' % self.show_awards)
        except NoOptionError:
            self.warning('could not find settings/show_awards in config file, '
                         'using default: %s' % self.show_awards)
        except ValueError, e:
            self.error('could not load settings/show_awards config value: %s' % e)
            self.debug('using default value (%s) for settings/show_awards' % self.show_awards)

        try:
            self.show_awards_xp = self.config.getboolean('settings', 'show_awards_xp')
            self.debug('loaded settings/show_awards: %s' % self.show_awards_xp)
        except NoOptionError:
            self.warning('could not find settings/show_awards_xp in config file, '
                         'using default: %s' % self.show_awards_xp)
        except ValueError, e:
            self.error('could not load settings/show_awards_xp config value: %s' % e)
            self.debug('using default value (%s) for settings/show_awards_xp' % self.show_awards_xp)

    def onStartup(self):
        """
        Initialize the plugin.
        """
        self._adminPlugin = self.console.getPlugin('admin')

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

        self.registerEvent('EVT_CLIENT_DAMAGE_TEAM', self.onDamageTeam)
        self.registerEvent('EVT_CLIENT_KILL_TEAM', self.onTeamKill)
        self.registerEvent('EVT_CLIENT_KILL', self.onKill)
        self.registerEvent('EVT_CLIENT_DAMAGE', self.onDamage)
        self.registerEvent('EVT_GAME_EXIT', self.onShowAwards)
        self.registerEvent('EVT_GAME_MAP_CHANGE', self.onShowAwards)
        self.registerEvent('EVT_GAME_ROUND_START', self.onRoundStart)

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onShowAwards(self, event):
        """
        Handle EVT_GAME_EXIT and EVT_GAME_MAP_CHANGE
        """
        if self.show_awards:
            self.cmd_topstats(None)
        if self.show_awards_xp:
            self.cmd_topxp(None)

    def onRoundStart(self, event):
        """
        Handle EVT_GAME_ROUND_START
        """
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
                except Exception, e:
                    self.error(e)

    def onDamage(self, event):
        """
        Handle EVT_CLIENT_DAMAGE
        """
        killer = event.client
        victim = event.target
        points = int(event.data[0])

        if points > 100:
            points = 100

        killer.var(self, 'shotsHit', 0).value  += 1
        killer.var(self, 'damageHit', 0).value += points
        victim.var(self, 'shotsGot', 0).value  += 1
        victim.var(self, 'damageGot', 0).value += points

    def onDamageTeam(self, event):
        """
        Handle EVT_CLIENT_DAMAGE_TEAM
        """
        killer = event.client
        points = int(event.data[0])

        if points > 100:
            points = 100

        killer.var(self, 'shotsTeamHit', 0).value  += 1
        killer.var(self, 'damageTeamHit', 0).value += points

    def onKill(self, event):
        """
        Handle EVT_CLIENT_KILL
        """
        killer = event.client
        victim = event.target
        points = int(event.data[0])

        if points > 100:
            points = 100

        killer.var(self, 'shotsHit', 0).value  += 1
        killer.var(self, 'damageHit', 0).value += points

        victim.var(self, 'shotsGot', 0).value  += 1
        victim.var(self, 'damageGot', 0).value += points

        killer.var(self, 'kills', 0).value  += 1
        victim.var(self, 'deaths', 0).value += 1

        val = self.score(killer, victim)
        killer.var(self, 'points', self.startPoints).value += val
        killer.var(self, 'pointsWon', 0).value += val

        victim.var(self, 'points', self.startPoints).value -= val
        victim.var(self, 'pointsLost', 0).value += val

        self.updateXP(killer)
        self.updateXP(victim)

    def onTeamKill(self, event):
        """
        Handle EVT_CLIENT_KILL_TEAM
        """
        killer = event.client
        victim = event.target
        points = int(event.data[0])

        if points > 100:
            points = 100

        killer.var(self, 'shotsTeamHit', 0).value  += 1
        killer.var(self, 'damageTeamHit', 0).value += points

        killer.var(self, 'teamKills', 0).value += 1

        val = self.score(killer, victim)
        killer.var(self, 'points', self.startPoints).value -= val
        killer.var(self, 'pointsLost', 0).value += val

        self.updateXP(killer)
        self.updateXP(victim)

    def updateXP(self, sclient):
        """
        Update client XP.
        """
        realpoints = sclient.var(self, 'pointsWon', 0).value - sclient.var(self, 'pointsLost', 0).value
        if sclient.var(self, 'deaths', 0).value != 0:
            experience = (sclient.var(self, 'kills', 0).value * realpoints) / sclient.var(self, 'deaths', 0).value
        else:
            experience = sclient.var(self, 'kills', 0).value * realpoints
        sclient.var(self, 'experience', 0).value = experience

    def score(self, killer, victim):
        """
        Return the amount of points the killer scored for killing the victim.
        """
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

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_mapstats(self, data, client, cmd=None):
        """
        [<name>] - list a players stats for the map
        """
        if data:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if not sclient:
                return
        else:
            sclient = client

        message = '^3Stats ^7[ %s ^7] K ^2%s ^7D ^3%s ^7TK ^1%s ^7Dmg ^5%s ^7Skill ^3%1.02f ^7XP ^6%s' % \
                  (sclient.exactName, sclient.var(self, 'kills', 0).value, sclient.var(self, 'deaths', 0).value,
                   sclient.var(self, 'teamKills', 0).value, sclient.var(self, 'damageHit', 0).value,
                   round(sclient.var(self, 'points', self.startPoints).value, 2),
                   round(sclient.var(self, 'oldexperience', 0).value + sclient.var(self, 'experience', 0).value, 2))

        cmd.sayLoudOrPM(client, message)

    def cmd_testscore(self, data, client, cmd=None):
        """
        <client> - how much skill points you will get if you kill the player
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
        """
        - list the top 5 map-stats players
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
        """
        - list the top 5 map-stats most experienced players
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