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

__author__ = 'ThorN'
__version__ = '1.3.2'



import b3
import b3.events
import b3.plugin

#--------------------------------------------------------------------------------------------------
class StatsPlugin(b3.plugin.Plugin):
    _adminPlugin = None

    def onLoadConfig(self):
        try:
            self.mapstatslevel = self.config.getint('commands', 'mapstats')
        except:
            self.mapstatslevel = 0
            self.debug('Using default value (%i) for commands::mapstats', self.mapstatslevel)

        try:
            self.testscorelevel = self.config.getint('commands', 'testscore')
        except:
            self.testscorelevel = 0
            self.debug('Using default value (%i) for commands::testscore', self.testscorelevel)

        try:
            self.topstatslevel = self.config.getint('commands', 'topstats')
        except:
            self.topstatslevel = 2
            self.debug('Using default value (%i) for commands::topstats', self.topstatslevel)

        try:
            self.topxplevel = self.config.getint('commands', 'topxp')
        except:
            self.topxplevel = 2
            self.debug('Using default value (%i) for commands::topxp', self.topxplevel)

        try:
            self.startPoints = self.config.getint('settings', 'startPoints')
        except:
            self.startPoints = 100
            self.debug('Using default value (%i) for settings::startPoints', self.startPoints)

        try:
            self.resetscore = self.config.getboolean('settings', 'resetscore')
        except:
            self.resetscore = False
            self.debug('Using default value (%s) for settings::resetscore', self.resetscore)

        try:
            self.resetxp = self.config.getboolean('settings', 'resetxp')
        except:
            self.resetxp = False
            self.debug('Using default value (%s) for settings::resetxp', self.resetxp)


    def onStartup(self):
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            self.critical('Cannot find the admin plugin. Disabling Stats plugin')
            self.disable()
            return False

        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp
                func = self.getCmd(cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)


        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_KILL)
        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE)
        #self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)

    def onEvent(self, event):
        if event.type == b3.events.EVT_GAME_ROUND_START:
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
                    except:
                        pass
        elif event.client:
            if event.type == b3.events.EVT_CLIENT_DAMAGE or event.type == b3.events.EVT_CLIENT_DAMAGE_TEAM:
                self.clientDamage(event.client, event.target, int(event.data[0]))
            elif event.type == b3.events.EVT_CLIENT_KILL or event.type == b3.events.EVT_CLIENT_KILL_TEAM:
                self.clientKill(event.client, event.target, int(event.data[0]))


    def getCmd(self, cmd):
        """ return the method for a given command  """
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
        return None


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
            killer.var(self, 'points', self.startPoints).value -= score
            killer.var(self, 'pointsLost', 0).value += score
        else:
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
            if not sclient: return            
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
        if not sclient: return    
        elif sclient == client:
            client.message('^7You don\'t get points for killing yourself')
            return

        cmd.sayLoudOrPM(client, '^3Stats: ^7%s^7 will get ^3%s ^7skill points for killing %s^7' % (client.exactName, self.score(client, sclient), sclient.exactName))

    def cmd_topstats(self, data, client, cmd=None):
        """\
        List the top 5 map-stats players
        """

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

                results.append('^3#%s^7 %s ^7(^3%s^7)' % (i, name, score))
                
                    
            cmd.sayLoudOrPM(client, '^3Top Stats:^7 %s' % ', '.join(results))
        else:
            client.message('^3Stats: ^7No top players')

    def cmd_topxp(self, data, client, cmd=None):
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

                results.append('^3#%s^7 %s ^7(^3%s^7)' % (i, name, score))


            cmd.sayLoudOrPM(client, '^3Top Experienced Players:^7 %s' % ', '.join(results))
        else:
            client.message('^3Stats: ^7No top experienced players')

    def score(self, killer, victim):
        k = int(killer.var(self, 'points', self.startPoints).value)
        v = int(victim.var(self, 'points', self.startPoints).value)

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


if __name__ == '__main__':
    """
    Automated tests below
    """
    from b3.fake import fakeConsole
    from b3.fake import superadmin, joe 
    import time
    
    from b3.config import XmlConfigParser
    
    conf = XmlConfigParser()
    conf.setXml("""
<configuration plugin="stats">
  <settings name="commands">
    <set name="mapstats-mystatalias">0</set>
    <set name="testscore-tscr">0</set>
    <set name="topstats-tops">2</set>
    <set name="topxp-txp">2</set>
  </settings>
  <settings name="settings">
    <set name="startPoints">100</set>
    <set name="resetscore">no</set>
    <set name="resetxp">no</set>
  </settings>
</configuration>
    """)

    
    p = StatsPlugin(fakeConsole, conf)
    p.onStartup()
    p.onLoadConfig()
    
    time.sleep(1)
    joe.connects(cid=3)
    joe.says("!mapstats")
    joe.says("!mystatalias")
    joe.says("!testscore")
    joe.says("!tscr")
    joe.says("!topstats")
    joe.says("!tops")
    joe.says("!topxp")
    joe.says("!txp")
    
    
    superadmin.connects(cid=2)
    joe.kills(superadmin)
    joe.kills(superadmin)
    joe.kills(superadmin)
    superadmin.kills(joe)
    
    superadmin.says("!mapstats")
    superadmin.says("!mystatalias")
    superadmin.says("!testscore")
    superadmin.says("!tscr")
    superadmin.says("!topstats")
    superadmin.says("!tops")
    superadmin.says("!topxp")
    superadmin.says("!txp")
    
    
