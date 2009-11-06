#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

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
#    9/5/2005 - 1.2.0 - ThorN
#    Added !topstats command
#    8/29/2005 - 1.1.0 - ThorN
#    Converted to use new event handlers

__author__  = 'ThorN'
__version__ = '1.2.3'



import b3
import b3.events
import b3.plugin

#--------------------------------------------------------------------------------------------------
class StatsPlugin(b3.plugin.Plugin):
    _adminPlugin = None
    _minLevel = 0
    _startPoints = 100

    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_KILL)
        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE)
        #self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
        self.registerEvent(b3.events.EVT_GAME_EXIT)

    def onLoadConfig(self):
        self._minLevel = self.config.getint('settings', 'min_level')

        self._adminPlugin = self.console.getPlugin('admin')

        if self._adminPlugin:
            self._adminPlugin.registerCommand(self, 'mapstats', self._minLevel, self.cmd_mapstats, 'mstats')
            self._adminPlugin.registerCommand(self, 'testscore', self._minLevel, self.cmd_testscore, 'ts')
            self._adminPlugin.registerCommand(self, 'topstats', 9, self.cmd_topstats, 'tstats')

    def onEvent(self, event):
        if event.type == b3.events.EVT_GAME_EXIT:
            self.debug('Map End: clearing stats')
            for cid,c in self.console.clients.items():
                if c.maxLevel >= self._minLevel:
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

                        # points will stay till past the map
                        #c.setvar(self, 'pointsLost', 0)
                        #c.setvar(self, 'pointsWon', 0)
                        #c.setvar(self, 'points', self._startPoints)
                    except:
                        pass
        elif event.client:
            if event.type == b3.events.EVT_CLIENT_DAMAGE or event.type == b3.events.EVT_CLIENT_DAMAGE_TEAM:
                self.clientDamage(event.client, event.target, int(event.data[0]))
            elif event.type == b3.events.EVT_CLIENT_KILL or event.type == b3.events.EVT_CLIENT_KILL_TEAM:
                self.clientKill(event.client, event.target, int(event.data[0]))


    def clientDamage(self, killer, victim, points):
        if points > 100:
            points = 100

        if killer.team == victim.team:
            killer.var(self, 'shotsTeamHit', 0).value  += 1
            killer.var(self, 'damageTeamHit', 0).value += points
        else:
            killer.var(self, 'shotsHit', 0).value  += 1
            killer.var(self, 'damageHit', 0).value += points

            victim.var(self, 'shotsGot', 0).value  += 1
            victim.var(self, 'damageGot', 0).value += points

    def clientKill(self, killer, victim, points):
        if points > 100:
            points = 100

        if killer.team == victim.team:
            killer.var(self, 'shotsTeamHit', 0).value  += 1
            killer.var(self, 'damageTeamHit', 0).value += points

            killer.var(self, 'teamKills', 0).value += 1

            score = self.score(killer, victim)
            killer.var(self, 'points', self._startPoints).value -= score
            killer.var(self, 'pointsLost', 0).value += score
        else:
            killer.var(self, 'shotsHit', 0).value  += 1
            killer.var(self, 'damageHit', 0).value += points

            victim.var(self, 'shotsGot', 0).value  += 1
            victim.var(self, 'damageGot', 0).value += points

            killer.var(self, 'kills', 0).value  += 1
            victim.var(self, 'deaths', 0).value += 1
            
            score = self.score(killer, victim)
            killer.var(self, 'points', self._startPoints).value += score
            killer.var(self, 'pointsWon', 0).value += score

            victim.var(self, 'points', self._startPoints).value -= score
            victim.var(self, 'pointsLost', 0).value += score

    def cmd_mapstats(self, data, client, cmd=None):
        """\
        [<name>] - list a players stats for the map
        """
        if data:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if not sclient: return            
        else:
            sclient = client

        message = '^3Stats ^7[ %s ^7] K ^2%s ^7D ^3%s ^7TK ^1%s ^7Dmg ^5%s ^7Skill ^3%1.02f' % (sclient.exactName, sclient.var(self, 'kills', 0).value, sclient.var(self, 'deaths', 0).value, sclient.var(self, 'teamKills', 0).value, sclient.var(self, 'damageHit', 0).value, round(sclient.var(self, 'points', self._startPoints).value, 2))
        cmd.sayLoudOrPM(client, message)

    def cmd_testscore(self, data, client, cmd=None):
        """\
        <name> - how much skill points you will get if you kill the player
        """

        if not data:
            client.message('^7You must supply a player name to test')
            return

        sclient = self._adminPlugin.findClientPrompt(data, client)
        if not sclient: return    
        elif sclient == client:
            client.message('^7You don\'t get points for killing yourself')
            return

        cmd.sayLoudOrPM(client, '^3Stats: ^7%s^7 will get ^3%s ^7skill points for killing %s^7' % (client.exactName, self.score(client, sclient), sclient.exactName))

    def cmd_topstats(self, data, client, cmd=None):
        """\
        List the top 5 map[stats players
        """

        scores = []
        for c in self.console.clients.getList():
            if c.isvar(self, 'points'):
                scores.append((c.exactName, round(c.var(self, 'points', self._startPoints).value, 2)))
        
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

                results.append('^3#%s^7 %s ^7(^3%s^7)' % (i, name, score))
                
                    
            cmd.sayLoudOrPM(client, '^3Top Stats:^7 %s' % ', '.join(results))
        else:
            client.message('^3Stats: ^7No top players')

    def score(self, killer, victim):
        k = int(killer.var(self, 'points', self._startPoints).value)
        v = int(victim.var(self, 'points', self._startPoints).value)

        if k < 1:
            k = 1.00
        if v < 1:
            v = 1.00

        """
        if k > v:
            high = k
            low  = v
        else:
            high = v
            low  = k
        
        vshift = float(high) / float(low)
        self.console.verbose('stats vshift %s' % vshift)

        #per = (vshift * 100) / 10
        per = (vshift * 10.0) / 100.0

        self.console.verbose('stats per %s' % per)

        if per > 100:
            per = 100.0
        elif per < 1:
            per = 1.0
        """

        vshift = (float(v) / float(k)) / 2
        self.console.verbose('stats vshift %s' % vshift)
        
        points = (15.00 * vshift) + 5

        if points < 1:
            points = 1.00
        elif points > 100:
            points = 100.00

        return round(points, 2)
        
"""
#--------------------------------------------------------------------------------------------------
class ClientStats(DelayedSQLObject):
    _table = 'stats'
    timeAdd = IntCol(default=0)
    kills = IntCol(default=0)
    teamKills = IntCol(default=0)
    deaths = IntCol(default=0)
    score  = IntCol(default=0)
    shotsGot  = IntCol(default=0)
    shotsHit  = IntCol(default=0)
    damageGot  = IntCol(default=0)
    damageHit  = IntCol(default=0)
    captures = IntCol(default=0)
    pickups = IntCol(default=0)
    rank = IntCol(default=0)
    gameName = StringCol(default='',length=3)
    gameType = StringCol(default='',length=3)
    pointsWon = IntCol(default=0)
    pointsLost = IntCol(default=0)
    playTime = IntCol(default=0)

    lastEventTime = 0

#    client = ForeignKey('Clients.Client')

    def __init__(self):
        ClientStats.__init__(self)
        self.createTable(ifNotExists=True)
        
    def experiance(self):
        return ( self.kills + self.deaths ) / ( (self.pointsWon + self.pointsLost) / self.playTime )

    def save(self):
        self.playTime += ( (time.time() - time.timezone) - self.lastEventTime ) / 60
        #DelayedSQLObject.save(self)
"""
