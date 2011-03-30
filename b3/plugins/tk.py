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
#    11/22/2009 - 1.2.4 - Courgette
#    * also send a msg to victim with instructions on how to forgive
#    * add tests
#    10/30/2009 - 1.2.3 - xlr8or
#    * Added a few ffa gametypes for bypassing tk handling
#    08/22/2009 - 1.2.2 - Courgette
#    * fix bug in cmd_forgiveall
#    08/22/2009 - 1.2.1 - Courgette
#    * fix bug in cmd_forgiveall
#    08/22/2009 - 1.2.0b - Courgette
#    * setting to choose if the bot should broadcast or send private messages (default send private)
#    10/20/2008 - 1.1.6b1 - mindriot
#    * indentation fix
#    10/20/2008 - 1.1.6b0 - mindriot
#    * in clientDamage, kill and damage mutlipliers were reversed - changed if killed: to [0] and else: to [1]
#    * added grudge_enable to control grudge command registration
#    8/29/2005 - 1.1.0 - ThorN
#    * Converted to use new event handlers
#    7/23/2005 - 1.0.2 - ThorN
#    * Changed temp ban duration to be based on ban_length times the number of victims

__version__ = '1.2.4'
__author__  = 'ThorN'

import b3, string, re, threading
import b3.events
import b3.plugin

class TkInfo:
    def __init__(self, plugin, cid):
        self._attackers = {}
        self._attacked  = {}
        self._warnings  = {}
        self._lastAttacker = None
        self._grudged = []
        self.plugin = plugin
        self.cid = cid
        self.lastWarnTime = 0
        
    def _get_attackers(self):
        return self._attackers

    def _get_attacked(self):
        return self._attacked

    def forgive(self, cid):
        try:
            points = self._attackers[cid] 
            del self._attackers[cid]
        except:
            return 0

        if self._lastAttacker == cid:
            self._lastAttacker = None

        if cid in self._grudged:
            grudged = []
            for g in self._grudged:
                if g != cid:
                    grudged.append(g)
            self._grudged = grudged

        return points

    def warn(self, cid, warning):
        self._warnings[cid] = warning

    def forgiven(self, cid):
        try:
            del self._attacked[cid]
        except:
            pass
        
        try:
            w = self._warnings[cid]
        except:
            w = None

        if w:                
            w.inactive = 1
            w.save(self.plugin.console)

            del w
            del self._warnings[cid]


    def damage(self, cid, points):
        self._attacked[cid] = True

    def damaged(self, cid, points):
        try:
            self._attackers[cid] += points
        except:
            self._attackers[cid] = points

        self._lastAttacker = cid

    def _get_lastAttacker(self):
        return self._lastAttacker

    lastAttacker = property(_get_lastAttacker)

    def grudge(self, cid):
        if not cid in self._grudged:
            self._grudged.append(cid)

    def isGrudged(self, cid):
        return cid in self._grudged

    def getAttackerPoints(self, cid):
        try:
            return self._attackers[cid]
        except:
            return 0

    def _get_points(self):
        points = 0

        if len(self._attacked):            
            for cid, bol in self._attacked.items():
                try:
                    client = self.plugin.console.clients.getByCID(cid)
                    points += self.plugin.getClientTkInfo(client).getAttackerPoints(self.cid)
                except:
                    pass

        return points

    attackers = property(_get_attackers)
    attacked = property(_get_attacked)
    points = property(_get_points)

#--------------------------------------------------------------------------------------------------
class TkPlugin(b3.plugin.Plugin):
    _levels = {}
    _adminPlugin = None
    _maxLevel = 0
    _maxPoints = 0
    _grudge_enable = True
    _private_messages = None
    _ffa = ['dm', 'ffa', 'syc-ffa']

    
    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
        self.registerEvent(b3.events.EVT_GAME_EXIT)

        self._adminPlugin = self.console.getPlugin('admin')
        if self._adminPlugin:
            self._adminPlugin.registerCommand(self, 'forgive', 0, self.cmd_forgive, 'f')
            #self._adminPlugin.registerCommand('forgivenow', 0, self.cmd_forgivenow) # this command will forgive the person about to be kicked
            self._adminPlugin.registerCommand(self, 'forgivelist', 0, self.cmd_forgivelist, 'fl')
            self._adminPlugin.registerCommand(self, 'forgiveall', 0, self.cmd_forgiveall, 'fa')
            self._adminPlugin.registerCommand(self, 'forgiveinfo', 20, self.cmd_forgiveinfo, 'fi')
            self._adminPlugin.registerCommand(self, 'forgiveclear', 60, self.cmd_forgiveclear, 'fc')
            self._adminPlugin.registerCommand(self, 'forgiveprev', 0, self.cmd_forgivelast, 'fp')

            #    10/20/2008 - 1.1.6b0 - mindriot
            #    * added grudge_enable to control grudge command registration
            try:
                grudge_enable = self.config.getboolean('settings', 'grudge_enable')
                grudge_level = self.config.getint('settings','grudge_level')
            except:
                grudge_enable = self._grudge_enable
                grudge_level = 0
                self.debug('Using default value (%s) for grudge_enable', self._grudge_enable)
            if grudge_enable:
                self._adminPlugin.registerCommand(self, 'grudge', grudge_level, self.cmd_grudge, 'grudge')


    def onLoadConfig(self):
        self._issue_warning = self.config.get('settings', 'issue_warning') 
        self._round_grace =  self.config.getint('settings', 'round_grace')

        try:
            levels = string.split(self.config.get('settings', 'levels'), ',')

            for lev in levels:
                self._levels[int(lev)] = (self.config.getfloat('level_%s' % lev, 'kill_multiplier'), self.config.getfloat('level_%s' % lev, 'damage_multiplier'), self.config.getint('level_%s' % lev, 'ban_length'))

            self._maxLevel = int(lev)

            self.debug('tk max level is %s', self._maxLevel)

            self._maxPoints = self.config.getint('settings', 'max_points')
        except Exception, msg:
            self.error('There is an error with your TK Plugin config %s' % msg)
            return False
            
        try:
            self._private_messages = self.config.getboolean('settings','private_messages')
        except:
            self._private_messages = True
        self.debug('Send messages privately ? %s' % self._private_messages)
        

    def onEvent(self, event):
        if self.console.game.gameType in self._ffa: 
            # game type is deathmatch, ignore
            return
        elif event.type == b3.events.EVT_CLIENT_DAMAGE_TEAM:
            if event.client.maxLevel <= self._maxLevel:
                self.clientDamage(event.client, event.target, int(event.data[0]))

        elif event.type == b3.events.EVT_CLIENT_KILL_TEAM:
            if event.client.maxLevel <= self._maxLevel:
                self.clientDamage(event.client, event.target, int(event.data[0]), True)

        elif event.type == b3.events.EVT_CLIENT_DISCONNECT:
            self.forgiveAll(event.data)
            return

        elif event.type == b3.events.EVT_GAME_EXIT:
            self.debug('Map End: cutting all tk points in half')
            for cid,c in self.console.clients.items():
                try:
                    tkinfo = self.getClientTkInfo(c)
                    for acid,points in tkinfo.attackers.items():
                        points = int(round(points / 2))

                        if points == 0:
                            self.forgive(acid, c, True)
                        else:
                            try: tkinfo._attackers[acid] = points
                            except: pass
                except:
                    pass

            return
        else:
            return

        tkinfo = self.getClientTkInfo(event.client)
        points = tkinfo.points
        if points >= self._maxPoints:
            if points >= self._maxPoints + (self._maxPoints / 2):
                self.forgiveAll(event.client.cid)
                event.client.tempban(self.getMessage('ban'), 'tk', self.getMultipliers(event.client)[2])
            elif event.client.var(self, 'checkBan').value:
                pass
            else:            
                msg = ''
                if len(tkinfo.attacked) > 0:
                    myvictims = []
                    for cid, bol in tkinfo.attacked.items():
                        victim = self.console.clients.getByCID(cid)
                        if not victim:
                            continue
                        
                        v = self.getClientTkInfo(victim)
                        myvictims.append('%s ^7(^1%s^7)' % (victim.name, v.getAttackerPoints(event.client.cid)))
                        
                    if len(myvictims):
                        msg += ', ^1Attacked^7: %s' % ', '.join(myvictims)

                self.console.say(self.getMessage('forgive_warning', { 'name' : event.client.exactName, 'points' : points, 'cid' : event.client.cid }) + msg)
                event.client.setvar(self, 'checkBan', True)

                t = threading.Timer(30, self.checkTKBan, (event.client,))
                t.start()

    def checkTKBan(self, client):
        client.setvar(self, 'checkBan', False)
        tkinfo = self.getClientTkInfo(client)
        if tkinfo.points >= self._maxPoints:
            self.forgiveAll(client.cid)

            mult = len(tkinfo.attacked)
            if mult < 1:
                mult = 1

            duration = self.getMultipliers(client)[2] * mult
            for cid,a in tkinfo.attacked.items():
                self.forgive(cid, client, True)

            client.tempban(self.getMessage('ban'), 'tk', duration)

    def getMultipliers(self, client):
        level = ()
        for lev,mult in self._levels.iteritems():
            if lev <= client.maxLevel:
                level = mult

        if not level:
            return (0,0,0)

        #self.debug('getMultipliers = %s', level)
        #self.debug('round time %s' % self.console.game.roundTime())
        if self._round_grace and self.console.game.roundTime() < self._round_grace:
            # triple tk damage for first 15 seconds of round
            level = (level[0] * 1.5, level[1] * 3, level[2])

        return level

    def clientDamage(self, attacker, victim, points, killed=False):
        if points > 100:
            points = 100

        a = self.getClientTkInfo(attacker)
        v = self.getClientTkInfo(victim)

        #    10/20/2008 - 1.1.6b0 - mindriot
        #    * in clientDamage, kill and damage mutlipliers were reversed - changed if killed: to [0] and else: to [1]
        if killed:        
            points = int(round(points * self.getMultipliers(attacker)[0]))
        else:
            points = int(round(points * self.getMultipliers(attacker)[1]))

        a.damage(v.cid, points)
        v.damaged(a.cid, points)

        if self._round_grace and self._issue_warning and self.console.game.roundTime() < self._round_grace and a.lastWarnTime + 60 < self.console.time():
            a.lastWarnTime = self.console.time()
            self._adminPlugin.warnClient(attacker, self._issue_warning, None, False)
        elif points > 100 and attacker.maxLevel < 2 and a.lastWarnTime + 180 < self.console.time():
            a.lastWarnTime = self.console.time()
            warning = self._adminPlugin.warnClient(attacker, '^3Do not attack teammates, ^1Attacked: ^7%s ^7[^3%s^7]' % (victim.exactName, points), None, False)
            a.warn(v.cid, warning)
            victim.message('^7type ^3!fp ^7 to forgive ^3%s' % (attacker.exactName))

    def getClientTkInfo(self, client):
        if not client.isvar(self, 'tkinfo'):
            client.setvar(self, 'tkinfo', TkInfo(self, client.cid))

        if not client.isvar(self, 'checkBan'):
            client.setvar(self, 'checkBan', False)

        return client.var(self, 'tkinfo').value

    def forgive(self, acid, victim, silent=False):
        v = self.getClientTkInfo(victim)
        points = v.forgive(acid)

        attacker = self.console.clients.getByCID(acid)
        if attacker:
            a = self.getClientTkInfo(attacker)
            a.forgiven(victim.cid)

            if not silent:
                if self._private_messages:
                    victim.message(self.getMessage('forgive', { 'vname' : victim.exactName, 'aname' : attacker.name, 'points' : points }))
                    attacker.message(self.getMessage('forgive', { 'vname' : victim.exactName, 'aname' : attacker.name, 'points' : points }))
                else:
                    self.console.say(self.getMessage('forgive', { 'vname' : victim.exactName, 'aname' : attacker.name, 'points' : points }))
        elif not silent:
            if self._private_messages:
                victim.message(self.getMessage('forgive', { 'vname' : victim.exactName, 'aname' : acid, 'points' : points }))
            else:
                self.console.say(self.getMessage('forgive', { 'vname' : victim.exactName, 'aname' : acid, 'points' : points }))

        return points

    def grudge(self, acid, victim, silent=False):
        attacker = self.console.clients.getByCID(acid)
        if attacker:
            try:
                v = self.getClientTkInfo(victim)
                points = v.getAttackerPoints(attacker.cid)
                v.grudge(attacker.cid)

                if not silent:
                    if self._private_messages:
                        victim.message(self.getMessage('grudged', { 'vname' : victim.exactName, 'aname' : attacker.name, 'points' : points }))
                        attacker.message(self.getMessage('grudged', { 'vname' : victim.exactName, 'aname' : attacker.name, 'points' : points }))
                    else:
                        self.console.say(self.getMessage('grudged', { 'vname' : victim.exactName, 'aname' : attacker.name, 'points' : points }))
                return points
            except:
                pass
        return False

    def forgiveAll(self, acid):
        attacker = self.console.clients.getByCID(acid)
        if attacker:
            a = self.getClientTkInfo(attacker)
            a._attacked = {}

        # forgive all his points
        points = 0
        for cid,c in self.console.clients.items():
            try:
                v = self.getClientTkInfo(c)
                points += v.forgive(acid)
                a.forgiven(v.cid)
            except:
                pass

        return points

    def cmd_grudge(self, data, client, cmd=None):
        """\
        <name> - grudge a player for team damaging, a grudge player will not be auto-forgiven
        """
        v = self.getClientTkInfo(client)
        if not len(v.attackers):
            client.message(self.getMessage('no_forgive'))
            return

        if not data:
            if len(v.attackers) == 1:
                for cid, points in v.attackers.items():
                    self.grudge(cid, client)
            else:
                self.cmd_forgivelist(data, client)
        elif data == 'last':
            self.grudge(v.lastAttacker, client)
        elif re.match(r'^[0-9]+$', data):
            self.grudge(data, client)
        else:
            data = data.lower()
            for cid, points in v.attackers.items():
                c = self.console.clients.getByCID(cid)
                if c and c.name.lower().find(data) != -1:
                    self.grudge(c.cid, client)

    def cmd_forgive(self, data, client, cmd=None):
        """\
        <name> - forgive a player for team damaging
        """
        v = self.getClientTkInfo(client)
        if not len(v.attackers):
            client.message(self.getMessage('no_forgive'))
            return

        if not data:
            if len(v.attackers) == 1:
                for cid, points in v.attackers.items():
                    self.forgive(cid, client)
            else:
                self.cmd_forgivelist(data, client)
        elif data == 'last':
            self.forgive(v.lastAttacker, client)
        elif re.match(r'^[0-9]+$', data):
            self.forgive(data, client)
        else:
            data = data.lower()
            for cid, points in v.attackers.items():
                c = self.console.clients.getByCID(cid)
                if c and c.name.lower().find(data) != -1:
                    self.forgive(c.cid, client)

    def cmd_forgivelast(self, data, client, cmd=None):
        """\
        - forgive the last person to tk you
        """
        v = self.getClientTkInfo(client)
        if len(v.attackers) == 1:
            for cid, attacker in v.attackers.items():
                if v.isGrudged(cid):
                    client.message(self.getMessage('no_forgive'))
                else:
                    self.forgive(cid, client)
        elif v.lastAttacker and not v.isGrudged(v.lastAttacker):
            self.forgive(v.lastAttacker, client)
        else:
            client.message(self.getMessage('no_forgive'))            

    def cmd_forgiveall(self, data, client, cmd=None):
        """\
        - forgive all attackers' tk points
        """
        v = self.getClientTkInfo(client)
        if len(v.attackers) > 0:
            forgave = []
            for cid,points in v.attackers.items():
                if v.isGrudged(cid):
                    continue

                attacker = self.console.clients.getByCID(cid)
                points = self.forgive(cid, client, True)
                if attacker and points:
                    forgave.append('%s^7 [^3%s^7]' % (attacker.name, points))
                    if self._private_messages:
                        attacker.message(self.getMessage('forgive_many', { 'vname' : client.exactName, 'attackers' : attacker.exactName }))
                

            if len(forgave):
                if self._private_messages:
                    client.message(self.getMessage('forgive_many', { 'vname' : client.exactName, 'attackers' : string.join(forgave, ', ') }))
                else:
                    self.console.say(self.getMessage('forgive_many', { 'vname' : client.exactName, 'attackers' : string.join(forgave, ', ') }))
            else:
                client.message(self.getMessage('no_forgive'))
        else:
            client.message(self.getMessage('no_forgive'))

    def cmd_forgivelist(self, data, client, cmd=None):
        """\
        - list all the players who have shot you
        """
        # do some stuff here to list forgivable players
        v = self.getClientTkInfo(client)
        if len(v.attackers) > 0:
            myattackers = []
            for cid, points in v.attackers.items():
                attacker = self.console.clients.getByCID(cid)
                if not attacker:
                    v.forgive(cid)
                    continue

                if v.isGrudged(cid):
                    myattackers.append('^7[^2%s^7] ^1%s ^7(^1%s^7)' % (attacker.cid, attacker.name, points))
                else:
                    myattackers.append('^7[^2%s^7] %s ^7[^3%s^7]' % (attacker.cid, attacker.name, points))

            if len(myattackers):
                client.message(self.getMessage('players', ', '.join(myattackers)))
            else:
                client.message(self.getMessage('no_forgive'))
        else:
            client.message(self.getMessage('no_forgive'))

    def cmd_forgiveinfo(self, data, client, cmd=None):
        """\
        <name> - display a user's tk points
        """
        m = re.match('^([a-z0-9]+)$', data)
        if not m:
            client.message('^7Invalid parameters')
            return

        sclient = self._adminPlugin.findClientPrompt(data, client)

        if sclient:
            tkinfo = self.getClientTkInfo(sclient)
            msg = ''
            if len(tkinfo.attacked) > 0:
                myvictims = []
                for cid, bol in tkinfo.attacked.items():
                    victim = self.console.clients.getByCID(cid)
                    if not victim:
                        continue
                    
                    v = self.getClientTkInfo(victim)
                    myvictims.append('%s ^7(^1%s^7)' % (victim.name, v.getAttackerPoints(sclient.cid)))
                    
                if len(myvictims):
                    msg += ', ^1Attacked^7: %s' % ', '.join(myvictims)

            if len(tkinfo.attackers) > 0:
                myattackers = []
                for cid, points in tkinfo.attackers.items():
                    attacker = self.console.clients.getByCID(cid)
                    if not attacker:
                        continue
                    
                    if tkinfo.isGrudged(attacker.cid):
                        myattackers.append('^1%s ^7[^3%s^7]' % (attacker.name, points))
                    else:
                        myattackers.append('%s ^7[^3%s^7]' % (attacker.name, points))
                    
                if len(myattackers):
                    msg += ', ^3Attacked By^7: %s' % ', '.join(myattackers)

            cmd.sayLoudOrPM(client, self.getMessage('forgive_info', { 'name' : sclient.exactName, 'points' : tkinfo.points }) + msg)

    def cmd_forgiveclear(self, data, client, cmd=None):
        """\
        <name> - clear a user's tk points
        """
        m = re.match('^([a-z0-9]+)$', data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        sclient = self._adminPlugin.findClientPrompt(data, client)

        if sclient:
            points = self.forgiveAll(sclient.cid)
            if self._private_messages:
                client.message(self.getMessage('forgive_clear', { 'name' : sclient.exactName, 'points' : points }))
                sclient.message(self.getMessage('forgive_clear', { 'name' : sclient.exactName, 'points' : points }))
            else:
                self.console.say(self.getMessage('forgive_clear', { 'name' : sclient.exactName, 'points' : points }))

            return True



if __name__ == '__main__':
    import time
    from b3.fake import fakeConsole
    from b3.fake import joe
    from b3.fake import simon
    from b3.fake import moderator
    
    p = TkPlugin(fakeConsole, "@b3/conf/plugin_tk.xml")
    p.onStartup() # register events, etc
    
    joe.team = b3.TEAM_BLUE
    simon.team = b3.TEAM_BLUE
    
    time.sleep(5)
    joe.kills(simon)
    time.sleep(6)
    simon.kills(joe)
    time.sleep(2)
    joe.says('!f 2')
    time.sleep(2)
    joe.damages(simon)
    moderator.says('!forgiveinfo joe')
    time.sleep(2)
    joe.damages(simon)
    joe.damages(simon)
    moderator.says('!forgiveinfo joe')
    time.sleep(2)
    joe.kills(simon)
    time.sleep(2)
    
