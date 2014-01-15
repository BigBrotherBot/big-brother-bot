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
#    15/01/2014 - 1.3.2 - Fenix
#    * add 'lms' to ffa gametype: skip teamkill detection for Last Man Standing on Urban Terror 4.2
#    23/10/2013 - 1.3.1 - courgette
#    * the plugin falls back on default values even with an empty config file
#    * fix bug with _round_end_games
#    22/10/2013 - 1.3.0 - ozon
#    * allow configurable warning reason
#    04/04/2012 - 1.2.8 - 82ndab-Bravo17
#    * Remove logfile errors
#    01/29/2012 - 1.2.7 - 82ndab-Bravo17
#    * Check for ROUND_END event to halve TK points for BF3
#    * Add configurable TK point 'half-life' to halve TK points at intervals in long rounds
#    * Add configurable duration for auto TK warning
#    01/06/2012 - 1.2.6 - 82ndab-Bravo17
#    * Add configurable values for sending damage messages
#    03/30/2011 - 1.2.5 - SGT
#    * Introduction of grudge level
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
import string
import re
import threading
from ConfigParser import NoOptionError
import time

import b3
import b3.events
import b3.plugin
import b3.cron


__version__ = '1.3.2'
__author__ = 'ThorN, mindriot, Courgette, xlr8or, SGT, 82ndab-Bravo17, ozon'


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


class TkPlugin(b3.plugin.Plugin):

    def __init__(self, console, config=None):
        b3.plugin.Plugin.__init__(self, console, config)
        self._adminPlugin = None

        # game types that have no team based game play and for which there should be
        # no tk detected
        self._ffa = ['dm', 'ffa', 'syc-ffa', 'lms']

        # games for which the plugin will have all tk points on EVT_GAME_ROUND_END events
        # instead of on EVT_GAME_EXIT events
        self._round_end_games = ['bf3']
        self._use_round_end = False

        self._default_messages = dict(
            ban='^7team damage over limit',
            forgive='^7$vname^7 has forgiven $aname [^3$points^7]',
            grudged='^7$vname^7 has a ^1grudge ^7against $aname [^3$points^7]',
            forgive_many='^7$vname^7 has forgiven $attackers',
            forgive_warning='^1ALERT^7: $name^7 auto-kick if not forgiven. Type ^3!forgive $cid ^7to forgive. [^3damage: $points^7]',
            no_forgive='^7no one to forgive',
            players='^7Forgive who? %s',
            forgive_info='^7$name^7 has ^3$points^7 TK points',
            forgive_clear='^7$name^7 cleared of ^3$points^7 TK points',
            tk_warning_reason='^3Do not attack teammates, ^1Attacked: ^7$vname ^7[^3$points^7]',
            tk_request_action='^7type ^3!fp ^7 to forgive ^3%s',
        )

        # settings
        self._maxPoints = 400
        self._levels = {
            0: (2.0, 1.0, 2),
            1: (2.0, 1.0, 2),
            2: (1.0, 0.5, 1),
            20: (1.0, 0.5, 0),
            40: (0.75, 0.5, 0)
        }
        self._maxLevel = 40
        self._round_grace = 7
        self._issue_warning = "sfire"
        self._grudge_enable = True
        self._grudge_level = 0
        self._private_messages = None
        self._damage_threshold = 100
        self._warn_level = 2
        self._tkpointsHalflife = 0
        self._cronTab_tkhalflife = None
        self._tk_warn_duration = '1h'

    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
        self.registerEvent(b3.events.EVT_GAME_EXIT)
        self.registerEvent(b3.events.EVT_GAME_ROUND_END)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)

        self._adminPlugin = self.console.getPlugin('admin')
        if self._adminPlugin:
            self._adminPlugin.registerCommand(self, 'forgive', 0, self.cmd_forgive, 'f')
            #self._adminPlugin.registerCommand('forgivenow', 0, self.cmd_forgivenow) # this command will forgive the person about to be kicked
            self._adminPlugin.registerCommand(self, 'forgivelist', 0, self.cmd_forgivelist, 'fl')
            self._adminPlugin.registerCommand(self, 'forgiveall', 0, self.cmd_forgiveall, 'fa')
            self._adminPlugin.registerCommand(self, 'forgiveinfo', 20, self.cmd_forgiveinfo, 'fi')
            self._adminPlugin.registerCommand(self, 'forgiveclear', 60, self.cmd_forgiveclear, 'fc')
            self._adminPlugin.registerCommand(self, 'forgiveprev', 0, self.cmd_forgivelast, 'fp')

            if self._grudge_enable:
                self._adminPlugin.registerCommand(self, 'grudge', self._grudge_level, self.cmd_grudge, 'grudge')

        if self._tkpointsHalflife > 0:
            minute, sec = self.crontab_time()
            self._cronTab_tkhalflife = b3.cron.OneTimeCronTab(self.halveTKPoints, second=sec, minute=minute)
            self.console.cron + self._cronTab_tkhalflife
            self.debug('TK Crontab started')

    def onLoadConfig(self):
        try:
            self._issue_warning = self.config.get('settings', 'issue_warning')
        except NoOptionError:
            self.debug("Using default value (%s) for issue_warning" % self._issue_warning)

        try:
            self._round_grace = self.config.getint('settings', 'round_grace')
        except NoOptionError:
            self.debug("Using default value (%s) for round_grace" % self._round_grace)

        try:
            self._levels = self.load_config_for_levels()
        except NoOptionError:
            self.debug("Using default value (%s) for levels" % ','.join(map(str, self._levels.keys())))
        except ValueError:
            self.error("config is inconsistent regarding levels. Falling back on default values")

        self._maxLevel = max(self._levels.keys())
        self.debug('tk max level is %s', self._maxLevel)

        try:
            self._maxPoints = self.config.getint('settings', 'max_points')
        except NoOptionError:
            self.debug("Using default value (%s) for max_points" % self._maxPoints)

        try:
            self._private_messages = self.config.getboolean('settings', 'private_messages')
        except:
            self._private_messages = True
        self.debug('Send messages privately ? %s' % self._private_messages)
        
        try:
            self._damage_threshold = self.config.getint('settings', 'damage_threshold')
        except:
            self._damage_threshold = 100
        self.debug('Damage Threshold is %s' % self._damage_threshold)
        
        try:
            self._tk_warn_duration = self.config.get('settings', 'warn_duration')
        except:
            self._tk_warn_duration = '1h'
        self.debug('TK Warning duration is %s' % self._tk_warn_duration)  
        
        try:
            self._warn_level = self.config.getint('settings', 'warn_level')
        except:
            self._warn_level = 2
        self.debug('Max warn level is %s' % self._warn_level)
        
        try:
            self._tkpointsHalflife = self.config.getint('settings', 'halflife')
        except:
            self._tkpointsHalflife = 0
        self.debug('Half life for TK points is %s (0 is disabled)' % self._tkpointsHalflife)
        
        if self.console.gameName in self._round_end_games:
            self._use_round_end = True
            self.debug('Using ROUND_END event to halve TK points')
        else:
            self.debug('Using GAME_EXIT event to halve TK points')

        #    10/20/2008 - 1.1.6b0 - mindriot
        #    * added grudge_enable to control grudge command registration
        try:
            self._grudge_enable = self.config.getboolean('settings', 'grudge_enable')
        except:
            self.debug('Using default value (%s) for grudge_enable', self._grudge_enable)
        try:
            self._grudge_level = self.config.getint('settings', 'grudge_level')
        except:
            self.debug('Using default value (%s) for grudge_level', self._grudge_level)

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

        elif (event.type == b3.events.EVT_GAME_EXIT and not self._use_round_end) or (event.type == b3.events.EVT_GAME_ROUND_END and self._use_round_end):
            if self._cronTab_tkhalflife:
                # remove existing crontab
                self.console.cron - self._cronTab_tkhalflife
            self.halveTKPoints('Map End: cutting all tk points in half')
            return
            
        elif event.type == b3.events.EVT_GAME_ROUND_START:
            if self._tkpointsHalflife > 0:
                if self._cronTab_tkhalflife:
                    # remove existing crontab
                    self.console.cron - self._cronTab_tkhalflife
                (min, sec) = self.crontab_time()
                self._cronTab_tkhalflife = b3.cron.OneTimeCronTab(self.halveTKPoints, second=sec, minute=min)
                self.console.cron + self._cronTab_tkhalflife
                self.debug('TK Crontab started')

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

    def halveTKPoints(self, msg=None):
        if msg == None:
            msg = ('Halving all TK Points')
        self.debug(msg)
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
        if self._tkpointsHalflife > 0: 
            if self._cronTab_tkhalflife:
                # remove existing crontab
                self.console.cron - self._cronTab_tkhalflife
            (min, sec) = self.crontab_time()
            self._cronTab_tkhalflife = b3.cron.OneTimeCronTab(self.halveTKPoints, second=sec, minute=min)
            self.console.cron + self._cronTab_tkhalflife
            #self.console.say('TK Crontab re-started')
            self.debug('TK Crontab re-started')
            
    def crontab_time(self):
        sec = self._tkpointsHalflife
        min = int(time.strftime('%M'))
        sec = sec + int(time.strftime('%S'))
        while sec > 59:
            min += 1
            sec -= 60
            
        if min > 59:
            min -= 60
            
        return (min, sec)    
    
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
        
        self.debug('Attacker: %s, TK Points: %s, attacker.maxLevel: %s, last warn time: %s, Console time: %s' % (attacker.exactName, points, attacker.maxLevel, a.lastWarnTime, self.console.time()))

        if self._round_grace and self._issue_warning and self.console.game.roundTime() < self._round_grace and a.lastWarnTime + 60 < self.console.time():
            a.lastWarnTime = self.console.time()
            self._adminPlugin.warnClient(attacker, self._issue_warning, None, False)
        elif points > self._damage_threshold and attacker.maxLevel < self._warn_level and a.lastWarnTime + 180 < self.console.time():
            a.lastWarnTime = self.console.time()
            warning = self._adminPlugin.warnClient(attacker, self.getMessage('tk_warning_reason', {'vname': victim.exactName, 'points': points}), None, False, newDuration = self._tk_warn_duration)
            a.warn(v.cid, warning)
            victim.message(self.getMessage('tk_request_action', attacker.exactName))

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
                client.message(self.getMessage('forgive_clear', {'name': sclient.exactName, 'points': points}))
                sclient.message(self.getMessage('forgive_clear', {'name': sclient.exactName, 'points': points}))
            else:
                self.console.say(self.getMessage('forgive_clear', {'name': sclient.exactName, 'points': points}))

            return True

    def load_config_for_levels(self):
        levels_data = {}
        is_valid = True

        levels = self.config.get('settings', 'levels').split(',')

        for lev in levels:
            # check the level number is valid
            try:
                level_number = int(lev)
            except ValueError:
                self.error("%r is not a valid level number" % lev)
                is_valid = False
                continue

            # check if we have a config section named after this level
            section_name = 'level_%s' % lev
            if section_name not in self.config.sections():
                self.error("section %r is missing from the config file" % section_name)
                is_valid = False
                continue

            # check that this section for that level is valid
            try:
                kill_multiplier = self.config.getfloat(section_name, 'kill_multiplier')
            except NoOptionError:
                self.error("option kill_multiplier is missing in section %s" % section_name)
                is_valid = False
            except ValueError, err:
                self.error("value for kill_multiplier is invalid. %s" % err)
                is_valid = False

            try:
                damage_multiplier = self.config.getfloat(section_name, 'damage_multiplier')
            except NoOptionError:
                self.error("option damage_multiplier is missing in section %s" % section_name)
                is_valid = False
            except ValueError, err:
                self.error("value for damage_multiplier is invalid. %s" % err)
                is_valid = False

            try:
                ban_length = self.config.getint(section_name, 'ban_length')
            except NoOptionError:
                self.error("option ban_length is missing in section %s" % section_name)
                is_valid = False
            except ValueError, err:
                self.error("value for ban_length is invalid. %s" % err)
                is_valid = False

            if is_valid:
                levels_data[level_number] = (kill_multiplier, damage_multiplier, ban_length)

        if not is_valid:
            raise ValueError
        else:
            return levels_data
