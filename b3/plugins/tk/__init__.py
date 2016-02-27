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
import b3.cron
import string
import re
import threading
import time

from ConfigParser import NoOptionError

__version__ = '1.5'
__author__ = 'ThorN, mindriot, Courgette, xlr8or, SGT, 82ndab-Bravo17, ozon, Fenix'


class TkInfo(object):

    def __init__(self, plugin, cid):
        self._attackers = {}
        self._attacked = {}
        self._warnings = {}
        self._lastAttacker = None
        self._grudged = []
        self.plugin = plugin
        self.cid = cid
        self.lastwarntime = 0

    def _get_attackers(self):
        return self._attackers

    def _get_attacked(self):
        return self._attacked

    def forgive(self, cid):
        try:
            points = self._attackers[cid]
            del self._attackers[cid]
        except KeyError:
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
        except KeyError:
            pass

        try:
            w = self._warnings[cid]
        except KeyError:
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
        except KeyError:
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
        except KeyError:
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

    loadAfterPlugins = ['spawnkill']

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
        self._adminPlugin = self.console.getPlugin('admin')

        # game types that have no team based game play and for which there should be no tk detected
        self._ffa = ['dm', 'ffa', 'syc-ffa', 'lms']

        # games for which the plugin will have all tk points on EVT_GAME_ROUND_END events
        # instead of on EVT_GAME_EXIT events
        self._round_end_games = ['bf3']
        self._use_round_end = False

        self._default_messages = {
            'ban': '^7team damage over limit',
            'forgive': '^7$vname^7 has forgiven $aname [^3$points^7]',
            'grudged': '^7$vname^7 has a ^1grudge ^7against $aname [^3$points^7]',
            'forgive_many': '^7$vname^7 has forgiven $attackers',
            'forgive_warning': '^1ALERT^7: $name^7 auto-kick if not forgiven. Type ^3!forgive $cid ^7to forgive. [^3damage: $points^7]',
            'no_forgive': '^7no one to forgive',
            'players': '^7Forgive who? %s',
            'forgive_info': '^7$name^7 has ^3$points^7 TK points',
            'forgive_clear': '^7$name^7 cleared of ^3$points^7 TK points',
            'tk_warning_reason': '^3Do not attack teammates, ^1Attacked: ^7$vname ^7[^3$points^7]',
            'tk_request_action': '^7type ^3!fp ^7 to forgive ^3%s',
        }

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
        self._private_messages = True
        self._damage_threshold = 100
        self._warn_level = 2
        self._tkpointsHalflife = 0
        self._cronTab_tkhalflife = None
        self._tk_warn_duration = '1h'

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        self._issue_warning = self.getSetting('settings', 'issue_warning', b3.STR, self._issue_warning)
        self._round_grace = self.getSetting('settings', 'round_grace', b3.INT, self._round_grace)
        self._maxPoints = self.getSetting('settings', 'max_points', b3.INT, self._maxPoints)
        self._private_messages = self.getSetting('settings', 'private_messages', b3.BOOL, self._private_messages)
        self._damage_threshold = self.getSetting('settings', 'damage_threshold', b3.INT, self._damage_threshold)
        self._tk_warn_duration = self.getSetting('settings', 'warn_duration', b3.STR, self._tk_warn_duration)
        self._warn_level = self.getSetting('settings', 'warn_level', b3.INT, self._warn_level)
        self._tkpointsHalflife = self.getSetting('settings', 'halflife', b3.INT, self._tkpointsHalflife)
        self._grudge_enable = self.getSetting('settings', 'grudge_enable', b3.BOOL, self._grudge_enable)
        self._grudge_level = self.getSetting('settings', 'grudge_level', b3.INT, self._grudge_level)

        try:
            self._levels = self.load_config_for_levels()
            self.debug('loaded levels: %s' % ','.join(map(str, self._levels.keys())))
        except NoOptionError:
            self.warning('could not find levels in config file, '
                         'using default: %s' % ','.join(map(str, self._levels.keys())))
        except ValueError, e:
            self.error('could not load levels from config value: %s' % e)
            self.debug('using default levels' % ','.join(map(str, self._levels.keys())))

        self._maxLevel = max(self._levels.keys())
        self.debug('teamkill max level is %s', self._maxLevel)

        if self.console.gameName in self._round_end_games:
            self._use_round_end = True
            self.debug('using ROUND_END event to halve TK points')
        else:
            self.debug('using GAME_EXIT event to halve TK points')

    def load_config_for_levels(self):
        """
        Load teamkill configuration values for levels
        """
        levels_data = {}
        is_valid = True

        levels = []
        raw_levels = self.config.get('settings', 'levels').split(',')

        def getLevelSectionName(level):
            """
            find config level section based on level as a group keyword or level.

            :return None if section not found, or the section name
            """
            if 'level_%s' % level in self.config.sections():
                return 'level_%s' % level
            elif 'level_%s' % self.console.getGroupLevel(level) in self.config.sections():
                return 'level_%s' % self.console.getGroupLevel(level)

        for lev in raw_levels:
            # check the level number is valid
            try:
                level_number = int(self.console.getGroupLevel(lev))
                levels.append(level_number)
            except KeyError:
                self.error("%r is not a valid level" % lev)
                is_valid = False
                continue

            # check if we have a config section named after this level
            section_name = getLevelSectionName(lev)
            if section_name is None:
                self.error("section %r is missing from the config file" % ('level_%s' % lev))
                is_valid = False
                continue

            # init to remove warnings
            kill_multiplier = 0
            damage_multiplier = 0
            ban_length = 0

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

    def onStartup(self):
        """
        Plugin startup
        """
        # register events needed
        self.registerEvent('EVT_CLIENT_DAMAGE_TEAM')
        self.registerEvent('EVT_CLIENT_KILL_TEAM')
        self.registerEvent('EVT_CLIENT_DISCONNECT')
        self.registerEvent('EVT_GAME_EXIT')
        self.registerEvent('EVT_GAME_ROUND_END')
        self.registerEvent('EVT_GAME_ROUND_START')

        self._adminPlugin.registerCommand(self, 'forgive', 0, self.cmd_forgive, 'f')
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

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onEvent(self, event):
        """
        Handle intercepted events
        """
        if self.console.game.gameType in self._ffa:
            # game type is deathmatch, ignore
            return
        elif event.type == self.console.getEventID('EVT_CLIENT_DAMAGE_TEAM'):
            if event.client.maxLevel <= self._maxLevel:
                self.clientDamage(event.client, event.target, int(event.data[0]))

        elif event.type == self.console.getEventID('EVT_CLIENT_KILL_TEAM'):
            if event.client.maxLevel <= self._maxLevel:
                self.clientDamage(event.client, event.target, int(event.data[0]), True)

        elif event.type == self.console.getEventID('EVT_CLIENT_DISCONNECT'):
            self.forgiveAll(event.data)
            return

        elif (event.type == self.console.getEventID('EVT_GAME_EXIT') and not self._use_round_end) or \
                (event.type == self.console.getEventID('EVT_GAME_ROUND_END') and self._use_round_end):
            if self._cronTab_tkhalflife:
                # remove existing crontab
                self.console.cron - self._cronTab_tkhalflife
            self.halveTKPoints('map end: cutting all teamkill points in half')
            return

        elif event.type == self.console.getEventID('EVT_GAME_ROUND_START'):
            if self._tkpointsHalflife > 0:
                if self._cronTab_tkhalflife:
                    # remove existing crontab
                    self.console.cron - self._cronTab_tkhalflife
                (m, s) = self.crontab_time()
                self._cronTab_tkhalflife = b3.cron.OneTimeCronTab(self.halveTKPoints, second=s, minute=m)
                self.console.cron + self._cronTab_tkhalflife
                self.debug('TK crontab started')

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

                self.console.say(self.getMessage('forgive_warning', {'name': event.client.exactName,
                                                                     'points': points, 'cid': event.client.cid}) + msg)
                event.client.setvar(self, 'checkBan', True)
                t = threading.Timer(30, self.checkTKBan, (event.client,))
                t.start()

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def checkTKBan(self, client):
        """
        Check if we have to tempban a client for teamkilling.
        :param client: The client on who perform the check
        """
        client.setvar(self, 'checkBan', False)
        tkinfo = self.getClientTkInfo(client)
        if tkinfo.points >= self._maxPoints:
            self.forgiveAll(client.cid)
            mult = len(tkinfo.attacked)
            if mult < 1:
                mult = 1

            duration = self.getMultipliers(client)[2] * mult
            for cid, a in tkinfo.attacked.items():
                self.forgive(cid, client, True)

            client.tempban(self.getMessage('ban'), 'tk', duration)

    def halveTKPoints(self, msg=None):
        """
        Halve all the teamkill points
        """
        if msg is None:
            msg = 'halving all TK Points'
        self.debug(msg)
        for cid, c in self.console.clients.items():
            tkinfo = self.getClientTkInfo(c)
            for acid, points in tkinfo.attackers.items():
                points = int(round(points / 2))
                if points == 0:
                    self.forgive(acid, c, True)
                else:
                    try:
                        tkinfo.attackers[acid] = points
                    except KeyError:
                        pass

        if self._tkpointsHalflife > 0: 
            if self._cronTab_tkhalflife:
                # remove existing crontab
                self.console.cron - self._cronTab_tkhalflife
            (m, s) = self.crontab_time()
            self._cronTab_tkhalflife = b3.cron.OneTimeCronTab(self.halveTKPoints, second=s, minute=m)
            self.console.cron + self._cronTab_tkhalflife
            #self.console.say('TK Crontab re-started')
            self.debug('TK crontab re-started')
            
    def crontab_time(self):
        s = self._tkpointsHalflife
        m = int(time.strftime('%M'))
        s += int(time.strftime('%S'))
        while s > 59:
            m += 1
            s -= 60
        if m > 59:
            m -= 60
        return m, s
    
    def getMultipliers(self, client):
        level = ()
        for lev, mult in self._levels.iteritems():
            if lev <= client.maxLevel:
                level = mult

        if not level:
            return 0, 0, 0

        #self.debug('getMultipliers = %s', level)
        #self.debug('round time %s' % self.console.game.roundTime())
        if self._round_grace and self.console.game.roundTime() < self._round_grace:
            # triple tk damage for first 15 seconds of round
            level = (level[0] * 1.5, level[1] * 3, level[2])

        return level

    def clientDamage(self, attacker, victim, points, killed=False):
        points = int(min(100, points))

        a = self.getClientTkInfo(attacker)
        v = self.getClientTkInfo(victim)

        # 10/20/2008 - 1.1.6b0 - mindriot
        # * in clientDamage, kill and damage mutlipliers were reversed - changed if killed: to [0] and else: to [1]
        if killed:        
            points = int(round(points * self.getMultipliers(attacker)[0]))
        else:
            points = int(round(points * self.getMultipliers(attacker)[1]))

        a.damage(v.cid, points)
        v.damaged(a.cid, points)
        
        self.debug('attacker: %s, TK points: %s, attacker.maxLevel: %s, last warn time: %s, console time: %s' % (
                   attacker.exactName, points, attacker.maxLevel, a.lastwarntime, self.console.time()))

        if self._round_grace and self._issue_warning and \
                self.console.game.roundTime() < self._round_grace and \
                a.lastwarntime + 60 < self.console.time():
            a.lastwarntime = self.console.time()
            self._adminPlugin.warnClient(attacker, self._issue_warning, None, False)
        elif points > self._damage_threshold and \
                attacker.maxLevel < self._warn_level and \
                a.lastwarntime + 180 < self.console.time():
            a.lastwarntime = self.console.time()
            msg = self.getMessage('tk_warning_reason', {'vname': victim.exactName, 'points': points})
            warning = self._adminPlugin.warnClient(attacker, msg, None, False, newDuration=self._tk_warn_duration)
            a.warn(v.cid, warning)
            victim.message(self.getMessage('tk_request_action', attacker.exactName))

    def getClientTkInfo(self, client):
        """
        Return client teamkill info.
        """
        if not client.isvar(self, 'tkinfo'):
            client.setvar(self, 'tkinfo', TkInfo(self, client.cid))
        if not client.isvar(self, 'checkBan'):
            client.setvar(self, 'checkBan', False)
        return client.var(self, 'tkinfo').value

    def forgive(self, acid, victim, silent=False):
        """
        Forgive a client.
        :param acid: The attacket slot number
        :param victim: The victim client object instance
        :param silent: Whether or not to announce the forgive
        """
        v = self.getClientTkInfo(victim)
        points = v.forgive(acid)
        attacker = self.console.clients.getByCID(acid)
        if attacker:
            a = self.getClientTkInfo(attacker)
            a.forgiven(victim.cid)

            if not silent:
                if self._private_messages:
                    variables = {'vname': victim.exactName, 'aname': attacker.name, 'points': points}
                    victim.message(self.getMessage('forgive', variables))
                    variables = {'vname': victim.exactName, 'aname': attacker.name, 'points': points}
                    attacker.message(self.getMessage('forgive', variables))
                else:
                    variables = {'vname': victim.exactName, 'aname': attacker.name, 'points': points}
                    self.console.say(self.getMessage('forgive', variables))
        elif not silent:
            if self._private_messages:
                variables = {'vname': victim.exactName, 'aname': acid, 'points': points}
                victim.message(self.getMessage('forgive', variables))
            else:
                variables = {'vname': victim.exactName, 'aname': acid, 'points': points}
                self.console.say(self.getMessage('forgive', variables))

        return points

    def grudge(self, acid, victim, silent=False):
        """
        Grudge a client.
        :param acid: The slot number of the client to grudge
        :param victim: The victim client object instance
        :param silent: Whether or not to announce this grudge
        """
        attacker = self.console.clients.getByCID(acid)
        if attacker:
            v = self.getClientTkInfo(victim)
            points = v.getAttackerPoints(attacker.cid)
            v.grudge(attacker.cid)

            if not silent:
                if self._private_messages:
                    variables = {'vname': victim.exactName, 'aname': attacker.name, 'points': points}
                    victim.message(self.getMessage('grudged', variables))
                    variables = {'vname': victim.exactName, 'aname': attacker.name, 'points': points}
                    attacker.message(self.getMessage('grudged', variables))
                else:
                    variables = {'vname': victim.exactName, 'aname': attacker.name, 'points': points}
                    self.console.say(self.getMessage('grudged', variables))
            return points
        return False

    def forgiveAll(self, acid):
        """
        Forgive all the clients
        """
        attacker = self.console.clients.getByCID(acid)
        if not attacker:
            return

        a = self.getClientTkInfo(attacker)
        a._attacked = {}

        # forgive all his points
        points = 0
        for cid, c in self.console.clients.items():
            v = self.getClientTkInfo(c)
            points += v.forgive(acid)
            a.forgiven(v.cid)

        return points

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_grudge(self, data, client, cmd=None):
        """
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
        """
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
        """
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
        """
        - forgive all attackers' tk points
        """
        v = self.getClientTkInfo(client)
        if len(v.attackers) > 0:
            forgave = []
            for cid, points in v.attackers.items():
                if v.isGrudged(cid):
                    continue

                attacker = self.console.clients.getByCID(cid)
                points = self.forgive(cid, client, True)
                if attacker and points:
                    forgave.append('%s^7 [^3%s^7]' % (attacker.name, points))
                    if self._private_messages:
                        attacker.message(self.getMessage('forgive_many', {'vname': client.exactName,
                                                                          'attackers': attacker.exactName}))

            if len(forgave):
                if self._private_messages:
                    variables = {'vname': client.exactName, 'attackers': string.join(forgave, ', ')}
                    client.message(self.getMessage('forgive_many', variables))
                else:
                    variables = {'vname': client.exactName, 'attackers': string.join(forgave, ', ')}
                    self.console.say(self.getMessage('forgive_many', variables))
            else:
                client.message(self.getMessage('no_forgive'))
        else:
            client.message(self.getMessage('no_forgive'))

    def cmd_forgivelist(self, data, client, cmd=None):
        """
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
        """
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

            cmd.sayLoudOrPM(client, self.getMessage('forgive_info', {'name': sclient.exactName,
                                                                     'points': tkinfo.points}) + msg)

    def cmd_forgiveclear(self, data, client, cmd=None):
        """
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