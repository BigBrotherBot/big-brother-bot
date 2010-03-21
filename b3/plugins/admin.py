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
#   3/21/2010 - 1.4.7 - Bakes
#    * moved the !ci command to the pingwatch plugin
#    * moved part of cmd_maprotate to the parser.
#   3/7/2010 - 1.4.6 - Courgette
#    * fix crash on bot startup when loading a plugin which does not requires any config
#      file but still registers commands
#   1/27/2010 - 1.4.5 - Courgette
#    * the iamgod check warns if the command is explicitly enabled by config file but
#      superadmins are found in database
#   1/27/2010 - 1.4.4 - xlr8or
#    * added some verbose info to startup()
#   9/1/2009 - 1.4.3 - xlr8or
#    * check database connection before checking groups
#   8/24/2009 - 1.4.2 - courgette
#    * warning messages are also sent by pm to the admin that give them
#   8/22/2009 - 1.4.1 - courgette
#    * warning messages are shown only to the warned player. This is to prevent the bot from spaming the console.
#   8/19/2009 - 1.4.0 - courgette
#    * penalizeClient() will try to delegate unknown penalty types to inflictCustomPenalty() of the current parser.
#      Requires parser.py v1.10+
#   7/22/2009 - 1.3.5 - xlr8or
#    Generate better documented error when groupstable is empty
#   10/05/2008 - 1.3.4b0 - mindriot
#      * Removed hard code of 1 day for long_tempban_level - now controlled with new setting 'long_tempban_max_duration'
#   8/29/2005 - 1.2.2 - ThorN
#    Moved pbss command to punkbuster plugin
#   8/13/2005 - 1.2.1 - ThorN
#    Added penalizeClient()
#    Moved greeting to welcome plugin
#   7/23/2005 - 1.1.0 - ThorN
#    Made it so registerCommand() will check a plugins config "commands" section for command level overrides
#    Added ci command
#    Added data field to warnClient(), warnKick(), and checkWarnKick()

__version__ = '1.4.7'
__author__  = 'ThorN, xlr8or, Courgette'

import b3, string, re, time, threading, sys, traceback, thread, random
import ConfigParser

from b3 import functions
from b3 import clients
import b3.events
import b3.plugin
import b3.timezones
import copy

#--------------------------------------------------------------------------------------------------
class AdminPlugin(b3.plugin.Plugin):
    _commands = {}
    _parseUserCmdRE = re.compile(r'^(?P<cid>\'[^\']{2,}\'|[0-9]+|[^\s]{2,}|@[0-9]+)\s?(?P<parms>.*)$')
    _long_tempban_max_duration = 1440 # 60m/h x 24h = 1440m = 1d

    cmdPrefix = '!'
    cmdPrefixLoud = '@'

    PENALTY_KICK = 'kick'
    PENALTY_TEMPBAN = 'tempban'
    PENALTY_WARNING = 'warning'
    PENALTY_BAN = 'ban'

    def startup(self):
        self.registerEvent(b3.events.EVT_CLIENT_SAY)
        self.registerEvent(b3.events.EVT_CLIENT_PRIVATE_SAY)
        self.createEvent('EVT_ADMIN_COMMAND', 'Admin Command')

        cmdPrefix = self.config.get('settings', 'command_prefix')
        if cmdPrefix:
            self.cmdPrefix = cmdPrefix

        #cmdPrefixLoud = self.config.get('settings', 'command_prefix_loud')
        #if cmdPrefixLoud:
        #    self.cmdPrefixLoud = cmdPrefixLoud

        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = self.getCmd(cmd)
                if func:
                    self.registerCommand(self, cmd, level, func, alias)

        if not self.console.storage.db:
            self.error('There is no database connection! Cannot store or retrieve any information. Fix the database connection first!')
        else:
            try:
                superadmins = self.console.clients.lookupSuperAdmins()
            except Exception, msg:
                # no proper groups available, cannot continue
                self.critical('Seems your groupstable in the database is empty. Please recreate your database using the proper sql syntax - use b3/docs/b3.sql - (%s)' %msg)
            
            if self._commands.has_key('iamgod') \
                and self._commands['iamgod'].level is not None \
                and self._commands['iamgod'].level[0] >= 0:
                ## here the config file for the admin plugin explicitly enables the iamgod command
                if len(superadmins) == 0:
                    self.verbose('!iamgod command enabled by config file. Be sure to disable it after typing !iamgod.')
                else:
                    self.warning('!iamgod command enabled by config file but %s superadmin are already registered. ' +
                        'Make sure to disable the iamgod command in the admin plugin', len(superadmins))
            elif len(superadmins) == 0:
                self.verbose('No SuperAdmins found, enabling !iamgod')
                # There are no superadmins, enable the !iamgod command
                self.registerCommand(self, 'iamgod', 0, self.getCmd('iamgod'))
            else:
                self.verbose('SuperAdmin(s) found, no need for !iamgod')

    def registerCommand(self, plugin, command, level, handler, alias=None, secretLevel=None):
        if not handler:
            self.error('Command "%s" registration failed, no handler' % command)
            return False

        if plugin.config and plugin != self and plugin.config.has_option('commands', command):
            # override default level with level in config
            level = plugin.config.get('commands', command)
            
        if secretLevel is None:
            secretLevel = self.config.getint('settings', 'hidecmd_level')

        try:
            self._commands[command] = Command(plugin, command, level, handler, handler.__doc__, alias, secretLevel)

            if self._commands[command].alias:
                self._commands[self._commands[command].alias] = self._commands[command]

            self._commands[command].prefix = self.cmdPrefix
            self._commands[command].prefixLoud = self.cmdPrefixLoud

            self.debug('Command "%s (%s)" registered with %s for level %s' % (command, alias, self._commands[command].func.__name__, self._commands[command].level))
            return True
        except Exception, msg:
            self.error('Command "%s" registration failed %s' % (command, msg))
            return False

    def handle(self, event):
        if event.type == b3.events.EVT_CLIENT_SAY:
            self.OnSay(event)
        elif event.type == b3.events.EVT_CLIENT_PRIVATE_SAY and event.target and event.client.id == event.target.id:
            self.OnSay(event, True)

    def aquireCmdLock(self, cmd, client, delay, all=True):
        if client.maxLevel >= 20:
            return True
        elif cmd.time + delay <= self.console.time():
            return True
        else:
            return False

    def OnSay(self, event, private=False):
        self.debug('OnSay handle %s:"%s"', event.type, event.data)

        if self.console.debug and len(event.data) >= 3 and event.data[:1] == '#':
            if event.data[1:] == 'clients':
                self.debug('Clients:')
                for k, c in self.console.clients.items():
                    self.debug('client %s (#%i id: %s cid: %s level: %s group: %s) obj: %s', c.name, id(c), c.id, c.cid, c.maxLevel, c.groupBits, c)
            elif event.data[1:] == 'groups':
                self.debug('Groups for %s:', event.client.name)
                for g in event.client.groups:
                    self.debug('group (id: %s, name: %s, level: %s)', g.id, g.name, g.level)

            elif event.data[1:5] == 'vars':
                try:
                    data = event.data[7:].strip()
                    if data:
                        sclient = self.findClientPrompt(data, event.client)
                        if not sclient: return
                    else:
                        sclient = event.client
                except:
                    sclient = event.client

                self.debug('Vars for %s:', sclient.name)

                try:
                    for k,v in sclient._pluginData.items():
                        self.debug('\tplugin %s:', k)
                        for kk,vv in v.items():
                            self.debug('\t\t%s = %s', kk, str(vv.value))
                except Exception, e:
                    self.debug('Error getting vars: %s', e)
                self.debug('End of vars')
            elif event.data[1:7] == 'tkinfo':
                try:
                    data = event.data[9:].strip()
                    if data:
                        sclient = self.findClientPrompt(data, event.client)
                        if not sclient: return
                    else:
                        sclient = event.client
                except:
                    sclient = event.client

                self.debug('Tkinfo for %s:', sclient.name)

                try:
                    for k,v in sclient._pluginData.items():

                        for kk,vv in v.items():
                            if kk == 'tkinfo':
                                self.debug('\tplugin %s:', k)
                                tkinfo = vv.value
                                self.debug('\t\tcid = %s', tkinfo.cid)
                                self.debug('\t\tattackers = %s', str(tkinfo.attackers))
                                self.debug('\t\tattacked = %s', str(tkinfo.attacked))
                                self.debug('\t\tpoints = %s', tkinfo.points)
                                self.debug('\t\t_grudged = %s', str(tkinfo._grudged))
                                self.debug('\t\tlastAttacker = %s', tkinfo.lastAttacker)
                except Exception, e:
                    self.debug('Error getting Tkinfo: %s', e)
                self.debug('End of Tkinfo')

        elif len(event.data) >= 2 and (event.data[:1] == self.cmdPrefix or event.data[:1] == self.cmdPrefixLoud):
            self.debug('Handle command %s' % event.data)

            if event.data[1:2] == self.cmdPrefix or event.data[1:2] == self.cmdPrefixLoud or event.data[1:2] == '1':
                # self.is the alias for say
                cmd = 'say'
                data = event.data[2:]
            else:
                cmd = string.split(event.data[1:], ' ', 1)

                if len(cmd) == 2:
                    cmd, data = cmd
                else:
                    cmd  = cmd[0]
                    data = ''



            try:
                command = self._commands[cmd.lower()]
            except Exception, msg:
                if event.client.authed and event.client.maxLevel < self.config.getint('settings', 'admins_level'):
                    if event.client.var(self, 'fakeCommand').value:
                        event.client.var(self, 'fakeCommand').value += 1
                    else:
                        event.client.setvar(self, 'fakeCommand', 1)

                    if event.client.var(self, 'fakeCommand').toInt() >= 3:
                        event.client.setvar(self, 'fakeCommand', 0)
                        self.warnClient(event.client, 'fakecmd', None, False)
                        return

                event.client.message(self.getMessage('unknown_command', cmd))
                return

            cmd = cmd.lower()

            if not command.plugin.isEnabled():
                return

            elif not event.client.authed and command.level > 0:
                event.client.message('^7Please try your command after you have been authenticated')
                self.console.clients.authorizeClients()
                return

            elif private:
                # self.is a silent command
                if event.client.maxLevel < command.secretLevel:
                    event.client.message('^7You do not have sufficient access to do silent commands')
                    return False

            if command.canUse(event.client):
                try:
                    if event.data[:1] == self.cmdPrefixLoud and event.client.maxLevel >= 9:
                        results = command.executeLoud(data, event.client)
                    else:
                        results = command.execute(data, event.client)
                except Exception, msg:
                    event.client.message('^7There was an error processing your command')
                    raise
                else:
                    self.console.queueEvent(self.console.getEvent('EVT_ADMIN_COMMAND', (command.func, data, results), event.client))
            else:
                if event.client.maxLevel < self.config.getint('settings', 'admins_level'):
                    if event.client.var(self, 'noCommand').value:
                        event.client.var(self, 'noCommand').value += 1
                    else:
                        event.client.setvar(self, 'noCommand', 1)

                    if event.client.var(self, 'noCommand').toInt() >= 3:
                        event.client.setvar(self, 'noCommand', 0)
                        self.warnClient(event.client, 'nocmd', None, False)
                        return
                
                if command.level == None:
                    event.client.message('^7%s%s command is disabled' % (self.cmdPrefix, cmd))
                else:
                    event.client.message('^7You do not have sufficient access to use %s%s' % (self.cmdPrefix, cmd))

    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func

        return None

    def setCmdLevel(self, command, level):
        if command.__class__ is not Command:
            try:
                command = self._commands[command]
            except:
                raise KeyError, '^7Could not find command %s' % command
                return False

        level = str(level)
        if level.lower() == 'none':
            level = None
        elif level.count('-') == 1:
            level = level.split('-', 1)
            level = (int(level[0]), int(level[1]))
        else:
            level = (int(level), 100)

        if command.level == level:
            raise Warning, '^7Command %s is already level %s' % (command.command, level)
            return True
        else:
            if level == None:
                level = 'none';
            elif level[1] == 100:
                level = level[0]
            else:
                level = '%s-%s' % level

            self.config.set('commands', command.command, level)
            self.saveConfig()

            command.level = level
            return True

    def getAdmins(self):
        return self.console.clients.getClientsByLevel(self.config.getint('settings', 'admins_level'))

    def findClientPrompt(self, id, client=None):
        matches = self.console.clients.getByMagic(id)
        if matches:
            if len(matches) > 1:
                names = []
                for p in matches:
                    names.append('[^2%s^7] %s' % (p.cid, p.name))

                if client:
                    client.message(self.getMessage('players_matched', id, string.join(names, ', ')))
                return False
            else:
                return matches[0]
        else:
            if client:
                client.message(self.getMessage('no_players', id))
            return None

    def parseUserCmd(self, cmd, req=False):
        m = re.match(self._parseUserCmdRE, cmd)

        if m:
            cid = m.group('cid')
            parms = m.group('parms')

            if req and not len(parms): return None

            if cid[:1] == "'" and cid[-1:] == "'":
                cid = cid[1:-1]

            return (cid, parms)
        else:
            return None

    def getReason(self, reason):
        if not reason:
            return ''

        r = self.getWarning(reason)
        if r:
            return r[1]
        else:
            return reason

    def getSpam(self, spam):
        if not spam:
            return ''

        try:
            s = self.config.getTextTemplate('spamages', spam)

            if s[:9] == '/warning#':
                expire, warning = self.getWarning(s[9:]).split(',', 1)
                s = warning.strip()
            elif s[:1] == '/':
                s = self.config.getTextTemplate('spamages', s[1:])
                if s[:1] == '/':
                    self.error('getSpam: Possible spam recursion %s, %s', spam, s)
                    return None
            
            return s
        except ConfigParser.NoOptionError:
            return None
        except Exception, msg:
            self.error('getSpam: Could not get spam "%s": %s\n%s', spam, msg, traceback.extract_tb(sys.exc_info()[2]))
            return None

    def getWarning(self, warning):
        if not warning:
            warning = 'default'

        try:
            w = self.config.getTextTemplate('warn_reasons', warning)

            if w[:1] == '/':
                w = self.config.getTextTemplate('warn_reasons', w[1:])
                if w[:1] == '/':
                    self.error('getWarning: Possible warning recursion %s, %s', warning, w)
                    return None

            expire, warning = w.split(',', 1)
            warning = warning.strip()

            if warning[:6] == '/spam#':
                warning = self.getSpam(warning[6:])

            return (functions.time2minutes(expire.strip()), warning)
        except ConfigParser.NoOptionError:
            return None
        except Exception, msg:
            self.error('getWarning: Could not get warning "%s": %s\n%s', warning, msg, traceback.extract_tb(sys.exc_info()[2]))
            return None

    def assert_commandData(self, data, client, cmd, *formatArgs):
        data = cmd.parseData(data, *formatArgs)
        if not data[0]:
            client.message(data[1])
            return False
        else:
            return data[0]

    #--------------------------------------------------------------------------------------------------
    def cmd_die(self, data, client, cmd=None):
        """\
        - shutdown b3
        """
        cmd.sayLoudOrPM(client, '^7Shutting down ^3%s' % data)
        self.console.die()

    def cmd_restart(self, data, client, cmd=None):
        """\
        - restart b3
        """
        cmd.sayLoudOrPM(client, '^7Shutting down for restart...')
        self.console.restart()

    def cmd_reconfig(self, data, client, cmd=None):
        """\
        - re-load all configs
        """
        self.console.reloadConfigs()
        cmd.sayLoudOrPM(client, '^7Re-loaded configs')

    def cmd_mask(self, data, client, cmd=None):
        """\
        <group> [<name>] - hide level
        """

        m = self.parseUserCmd(data)

        if not m:
            client.message('^7Invalid parameters')
            return False
        elif m[1] == '':
            groupName = m[0]
            sclient = client
        else:
            groupName = m[0]
            sclient = self.findClientPrompt(m[1], client)
            if not sclient:
                return False

        try:
            group = clients.Group(keyword=groupName)
            group = self.console.storage.getGroup(group)
        except:
            client.message('^7Group %s does not exist' % groupName)
            return False

        sclient.maskLevel = group.id
        sclient._maskGroup = None
        sclient.save()

        if sclient != client:
            client.message('^7Masked %s as %s' % (sclient.name, group.name))
        sclient.message('^7Masked as %s' % group.name)

    def cmd_unmask(self, data, client, cmd=None):
        """\
        [<name>] - un-hide level
        """

        m = self.parseUserCmd(data)

        if not m:
            sclient = client
        else:
            sclient = self.findClientPrompt(m[0], client)

        if sclient:
            sclient.maskLevel = 0
            sclient._maskGroup = None
            sclient.save()

            if sclient != client:
                client.message('^7Un-Masked %s' % sclient.name)
            sclient.message('^7Un-Masked')

    def cmd_greeting(self, data, client, cmd=None):
        """\
        [<greeting>] - set or list your greeting (use 'none' to remove)
        """
        if data.lower() == 'none':
            client.greeting = ''
            client.save()
            client.message(self.getMessage('greeting_cleared'))
        elif data:
            data = re.sub(r'\$([a-z]+)', r'%(\1)s', data)

            if len(data) > 255:
                client.message('^7Your greeting is too long')
            else:
                try:
                    client.message('Greeting Test: %s' % (str(data) %
                        {'name' : client.exactName, 'greeting' : client.greeting, 'maxLevel' : client.maxLevel, 'group' : getattr(client.maxGroup, 'name', None), 'connections' : client.connections}))
                except ValueError, msg:
                    client.message(self.getMessage('greeting_bad', msg))
                    return False
                else:
                    client.greeting = data
                    client.save()
                    client.message(self.getMessage('greeting_changed', client.greeting))
                    return True
        else:
            if client.greeting:
                client.message(self.getMessage('greeting_yours', client.greeting))
            else:
                client.message(self.getMessage('greeting_empty'))

    def cmd_clear(self, data, client, cmd=None):
        """\
        [<player>] - clear all tk points and warnings
        """
        if data:
            sclient = self.findClientPrompt(data, client)

            if sclient:
                self.clearAll(sclient, client)

                self.console.say('%s^7 has cleared %s^7 of all points' % (client.exactName, sclient.exactName))
        else:
            for cid,c in self.console.clients.items():
                self.clearAll(c, client)

            self.console.say('%s^7 has cleared everyones points' % client.exactName)

    def clearAll(self, sclient, client=None):
        for w in sclient.warnings:
            admin = None
            try:
                admin = self.console.storage.getClient(clients.Client(id=w.adminId))
                # client object needs console to get groups
                admin.console = self.console
            except:
                # warning given by the bot (censor, tk, etc) have adminId = 0 which match no client in storage
                pass
                
            if admin is None or admin.maxLevel <= client.maxLevel:
                w.inactive = 1
                self.console.storage.setClientPenalty(w)

        self._tkPlugin = self.console.getPlugin('tk')
        if self._tkPlugin:
            self._tkPlugin.forgiveAll(sclient.cid)

        sclient.save()

    def cmd_map(self, data, client, cmd=None):
        """\
        <map> - switch current map
        """

        if not data:
            client.message('^7You must supply a map to change to.')
            return

        self.console.say('^7Changing map to %s' % data)
        time.sleep(1)
        self.console.write('map %s' % data)

    def cmd_maprotate(self, data, client, cmd=None):
        """\
        - switch to the next map in rotation
        """

        self.console.say('^7Changing map to next map')
        time.sleep(1)
        self.console.rotateMap()

    def cmd_b3(self, data, client, cmd=None):
        """\
        - say b3's version info
        """

        if len(data) > 0 and client.maxLevel >= self.config.getint('settings', 'admins_level'):
            data = data.lower().strip()

            if data == 'poke':
                self.console.say('^7Do not poke b3 %s^7!' % client.exactName)
            elif data == 'expose':
                self.console.say('^7Do expose b3 to sunlight %s^7!' % client.exactName)
            elif data == 'stare':
                self.console.say('^7Do not stare at b3 %s^7!' % client.exactName)
            elif data == 'stab':
                self.console.say('^7b3 is invincible, %s^7 could not penetrate he hide of b3.' % client.exactName)
            elif data == 'bite':
                self.console.say('^7b3 breaks %s^7\'s teeth with its metalic frame.' % client.exactName)
            elif data == 'fuck':
                self.console.say('^7b3 doesn\'t need your hand me out %s^7.' % client.exactName)
            elif data == 'slap':
                self.console.say('^7%s^7 is not Rick James.' % client.exactName)
            elif data == 'fight':
                self.console.say('^7%s^7 is knocked out by b3.' % client.exactName)
            elif data == 'feed':
                self.console.say('^7b3 enjoys your nourishment %s^7.' % client.exactName)
            elif data == 'throw':
                self.console.say('^7b3 can fly %s^7, and you throw like a sissy.' % client.exactName)
            elif data == 'furniture':
                self.console.say('^7b3 does make a lovely lamp %s^7.' % client.exactName)
            elif data == 'indeed':
                self.console.say('^7You WOULD say that %s^7.' % client.exactName)
            elif data == 'flog':
                self.console.say('^7You are so kinky %s^7.' % client.exactName)
            elif data == 'sexor':
                self.console.say('^7Mmmmm %s^7.' % client.exactName)
            elif data == 'hate':
                self.console.say('^7Don\'t hate the player, %s^7, hate the game.' % client.exactName)
            elif data == 'smoke':
                self.console.say('^7b3 has been known to cause lung cancer when smoked %s^7.' % client.exactName)
            elif data == 'maul':
                self.console.say('^7b3 casts a spell of invisibility, you can\'t find  %s^7.' % client.exactName)
            elif data == 'procreate':
                self.console.say('^7b3 2.0 will soon be on the way %s^7.' % client.exactName)
            elif data == 'shoot':
                self.console.say('^7Your hit detection is off %s^7, b3 is unharmed.' % client.exactName)
            elif data == 'kick':
                client.kick('^7as requested', '', None)
            elif data == 'triangulate':
                self.console.say('^7b3 is at %s.' % self.console._publicIp)
        else:
            cmd.sayLoudOrPM(client, '%s ^7- uptime: [^2%s^7]' % (b3.version, functions.minutesStr(self.console.upTime() / 60.0)))

    def cmd_about(self, data, client, cmd=None):
        """\
        <plugin> - Get information about a particular plugin
        """
        pass

    def cmd_enable(self, data, client, cmd=None):
        """\
        <plugin> - enable a disabled plugin
        """
        data = data.strip().lower()

        if not data:
            client.message('^7You must supply a plugin name to enable.')
            return
        elif data == 'admin':
            client.message('^7You cannot disable/enable the admin plugin.')
            return

        plugin = self.console.getPlugin(data)
        if plugin:
            if plugin.isEnabled():
                client.message('^7Plugin %s is already enabled.' % data)
            else:
                plugin.enable()
                self.console.say('^7%s is now ^2ON' % plugin.__class__.__name__)
        else:
            client.message('^7No plugin named %s loaded.' % data)

    def cmd_disable(self, data, client, cmd=None):
        """\
        <plugin> - disable a plugin
        """
        data = data.strip().lower()

        if not data:
            client.message('^7You must supply a plugin name to disable.')
            return
        elif data == 'admin':
            client.message('^7You cannot disable/enable the admin plugin.')
            return

        plugin = self.console.getPlugin(data)
        if plugin:
            if not plugin.isEnabled():
                client.message('^7Plugin %s is already disable.' % data)
            else:
                plugin.disable()
                self.console.say('^7%s is now ^1OFF' % plugin.__class__.__name__)
        else:
            client.message('^7No plugin named %s loaded.' % data)

    def cmd_register(self, data, client, cmd=None):
        """\
        - register youself as a basic user
        """
        try:
            group = clients.Group(keyword='user')
            group = self.console.storage.getGroup(group)
        except:
            return False

        if client.inGroup(group):
            client.message(self.getMessage('groups_already_in', client.exactName, group.name))
        elif client.maxLevel >= group.level:
            client.message('^7You are already in a higher level group')
        else:
            client.setGroup(group)
            client.save()

            self.console.say(self.getMessage('regme_annouce', client.exactName, group.name))
            return True

    def cmd_help(self, data, client, cmd=None):
        """\
        [<command|level>] - get info on how to use a command, you can use *<command> for partial matches
        """
        commands = []
        if re.match(r'^[0-9]+$', data):
            mlevel = int(data)
            for c, cmd in self._commands.iteritems():
                if cmd.level != None and cmd.level[0] == mlevel and cmd.canUse(client):
                    if cmd.command not in commands:
                        commands.append(cmd.command)
        elif data[:1] == '*':
            search = data[1:]
            for c, cmd in self._commands.iteritems():
                if string.find(cmd.command, search) != -1 and cmd.canUse(client) and cmd.command not in commands:
                    if cmd.command not in commands:
                        commands.append(cmd.command)
        elif data:
            try:
                cmd = self._commands[data]
                if cmd.canUse(client):
                    cmd.sayLoudOrPM(client, self.getMessage('help_command', self.cmdPrefix, cmd.command, cmd.help))
            except:
                client.message(self.getMessage('help_no_command', data))
            return
        else:
            for c, cmd in self._commands.iteritems():
                if cmd.canUse(client):
                    if cmd.command not in commands:
                        commands.append(cmd.command)

        if len(commands) == 0:
            cmd.sayLoudOrPM(client, self.getMessage('help_none'))
        else:
            commands.sort()
            cmd.sayLoudOrPM(client, self.getMessage('help_available', string.join(commands, ', ')))

    def cmd_list(self, data, client, cmd=None):
        """\
        - list all connected players
        """
        thread.start_new_thread(self.doList, (client, cmd))

    def doList(self, client, cmd):
        names = []
        for c in self.console.clients.getClientsByLevel():
            names.append(self.getMessage('player_id', c.cid, c.name))

        cmd.sayLoudOrPM(client, string.join(names, ', '))
        return True

    def cmd_groups(self, data, client, cmd=None):
        """\
        <name> - lists all the player's groups
        """
        m = self.parseUserCmd(data)
        if m:
            lclient = self.findClientPrompt(m[0], client)
        else:
            lclient = client

        if lclient:
            if len(lclient.groups):
                glist = []
                for group in lclient.groups:
                    glist.append(group.keyword);

                cmd.sayLoudOrPM(client, self.getMessage('groups_in', lclient.exactName, string.join(glist, ', ')))
                return True
            else:
                cmd.sayLoudOrPM(client, self.getMessage('groups_none', lclient.exactName))

    def cmd_admins(self, data, client, cmd=None):
        """\
        - lists all the online admins
        """
        self.debug('trying to get admins')
        clist = self.getAdmins()

        if len(clist) > 0:
            nlist = []
            for c in clist:
                if c.maskGroup:
                    nlist.append('%s^7 [^3%s^7]' % (c.exactName, c.maskGroup.level))
                else:
                    nlist.append('%s^7 [^3%s^7]' % (c.exactName, c.maxLevel))

            cmd.sayLoudOrPM(client, self.getMessage('admins', string.join(nlist, ', ')))
        else:
            self.debug('no admins found')

    def cmd_rebuild(self, data, client, cmd=None):
        """\
        - sync up connected players
        """
        self.console.clients.sync()
        client.message('Synchronizing client info')

    def cmd_regtest(self, cid, client, cmd=None):
        """\
        - display your current user status
        """

        if client and client.maskGroup:
            cmd.sayLoudOrPM(client, self.getMessage('leveltest', client.exactName, client.id, client.maskGroup.name, client.maskGroup.level, self.console.formatTime(client.timeAdd)))
        elif client and client.maxGroup:
            cmd.sayLoudOrPM(client, self.getMessage('leveltest', client.exactName, client.id, client.maxGroup.name, client.maxLevel, self.console.formatTime(client.timeAdd)))
        else:
            cmd.sayLoudOrPM(client, self.getMessage('leveltest', client.exactName, client.id, 'no groups', 0, self.console.formatTime(client.timeAdd)))

        return True

    def cmd_admintest(self, cid, client, cmd=None):
        """\
        - display your current user status
        """
        return self.cmd_regtest(cid, client, cmd)

    def cmd_leveltest(self, data, client, cmd=None):
        """\
        [<name>] - display a user's status
        """
        m = self.parseUserCmd(data)
        if m:
            sclient = self.findClientPrompt(m[0], client)
        else:
            sclient = client

        if sclient:
            if m and sclient.maskGroup:
                cmd.sayLoudOrPM(client, self.getMessage('leveltest', sclient.exactName, sclient.id, sclient.maskGroup.name, sclient.maskGroup.level, self.console.formatTime(sclient.timeAdd)))
            elif not sclient.maxGroup:
                cmd.sayLoudOrPM(client, self.getMessage('leveltest_nogroups', sclient.exactName, sclient.id))
            else:
                cmd.sayLoudOrPM(client, self.getMessage('leveltest', sclient.exactName, sclient.id, sclient.maxGroup.name, sclient.maxLevel, self.console.formatTime(sclient.timeAdd)))

        return True

    def cmd_cmdlevel(self, data, client, cmd=None):
        """\
        <command> <level> - set a commands level
        """
        m = re.match('^([a-z]+) ([0-9]+)$', data, re.I)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cmd   = m.group(1)
        level = int(m.group(2))

        try:
            self.setCmdLevel(cmd, level)
        except Warning, msg:
            client.message(str(msg))
        except KeyError, msg:
            client.message(str(msg))
        except Exception, msg:
            client.message('^7Error setting level for %s: %s' % (cmd, str(msg)))
        else:
            client.message('^7Command %s set to level %s' % (cmd, level))
            return True

    def cmd_newgroup(self, data, client, cmd=None):
        """\
        <keyword> <level> <name> - create a new group
        """
        m = re.match('^([a-z]+) ([0-9]+) (.*)$', data, re.I)
        if not m:
            client.message('^7Invalid parameters')
            return False

        keyword, level, name = m.groups()

        try:
            group = clients.Group(keyword=keyword)
            group = self.console.storage.getGroup(group)
            client.message('^7Group %s already exists' % group.keyword)
            return False
        except:
            raise NotImplementedError, 'Not implemented !newgroup'
            #group = clients.Group.new(keyword=keyword, name=name, level=level)
            client.message('^7Group %s created' % group.keyword)
            return True

    def cmd_delgroup(self, data, client, cmd=None):
        """\
        <group> - remove a group and remove all clients from the group
        """
        m = re.match('^([a-z]+)$', data, re.I)
        if not m:
            client.message('^7Invalid parameters')
            return False

        keyword = m.group(1)

        try:
            group = clients.Group(keyword=keyword)
            group = self.console.storage.getGroup(group)
        except:
            client.message('^7Group %s does not exist' % keyword)
            return False

        raise NotImplementedError, 'Not implemented !delgroup'

        # remove all the clients from the group
        for c in group.clients:
            c.removeGroup(group)

        group.destroySelf()

        for cid, c in self.console.clients.items():
            c.refreshLevel()

        client.message('^7Deleted group %s' % keyword)
        return True

    def cmd_makereg(self, data, client, cmd=None):
        """\
        <name> <group> - make a name a regular
        """

        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid = m[0]

        try:
            group = clients.Group(keyword='reg')
            group = self.console.storage.getGroup(group)
        except:
            client.message('^7Group reg does not exist')
            return False

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.inGroup(group):
                client.message(self.getMessage('groups_already_in', sclient.exactName, group.name))
            elif sclient.maxLevel >= group.level:
                client.message('^7%s ^7is already in a higher level group' % sclient.exactName)
            else:
                sclient.setGroup(group)
                sclient.save()

                cmd.sayLoudOrPM(client, self.getMessage('groups_put', sclient.exactName, group.name))
                return True

    def cmd_putgroup(self, data, client, cmd=None):
        """\
        <client> <group> - add a client to a group
        """
        m = re.match('^(.{2,}) ([a-z0-9]+)$', data, re.I)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m.groups()

        try:
            group = clients.Group(keyword=keyword)
            group = self.console.storage.getGroup(group)
        except:
            client.message('^7Group %s does not exist' % keyword)
            return False

        if group.level >= client.maxLevel and client.maxLevel < 100:
            client.message('^7Group %s is beyond your reach' % group.name)
            return False

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.inGroup(group):
                client.message(self.getMessage('groups_already_in', sclient.exactName, group.name))
            else:
                sclient.setGroup(group)
                sclient.save()

                cmd.sayLoudOrPM(client, self.getMessage('groups_put', sclient.exactName, group.name))
                return True

    def cmd_say(self, data, client, cmd=None):
        """\
        - say a message to all players
        """
        self.console.say(self.getMessage('say', client.exactName, data))
        return True

    def cmd_ungroup(self, cid, client, cmd=None):
        """\
        <client> <group> - remove a client from a group
        """
        m = re.match('^([^ ]{2,}) ([a-z]+)$', cid)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m.groups()

        try:
            group = clients.Group(keyword=keyword)
            group = self.console.storage.getGroup(group)
        except:
            client.message('^7Group %s does not exist' % keyword)
            return False

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.inGroup(group):
                sclient.remGroup(group)
                sclient.save()

                cmd.sayLoudOrPM(client, '^7%s^7 removed from group %s' % (sclient.exactName, group.name))
                return True
            else:
                client.message('^7%s^7 is not in group %s' % (sclient.exactName, group.name))

    def cmd_editgroup(self, data, client, cmd=None):
        """\
        <group> <-n|-k|-l> <value> - change a group's settings
        """
        m = re.match('^([a-z]+) -([a-z]) ([a-z0-9 ^]+)$', data, re.I)
        if not m:
            client.message('^7Invalid parameters')
            return False

        keyword, option, value = m.groups()

        try:
            group = clients.Group(keyword=keyword)
            group = self.console.storage.getGroup(group)
            mykeyword = group.keyword
        except:
            client.message('^7Group %s does not exist' % keyword)
            return False

        raise NotImplementedError, 'Not implemented !editgroup'

        if option == 'n':
            group.name = value
            client.message('^7Changed name of group %s to %s' % (mykeyword, group.name))
        elif option == 'l':
            group.level = int(value)

            # refresh levels for all the connected clients
            for cid,c in self.console.clients.items():
                if group in c.groups:
                    c.refreshLevel()

            client.message('^7Changed level of group %s to %s' % (mykeyword, group.level))
        elif option == 'k':
            group.keyword = value
            client.message('^7Changed keyword of group %s to %s' % (mykeyword, group.keyword))

    def cmd_iamgod(self, data, client, cmd=None):
        """\
        - register yourself as the super admin
        """
        superadmins = self.console.clients.lookupSuperAdmins()
        if len(superadmins) > 1:
            # There are already superadmins, disable this command
            if self._commands.has_key('iamgod'):
                self._commands.pop('iamgod')
            return

        try:
            group = clients.Group(keyword='superadmin')
            group = self.console.storage.getGroup(group)
        except Exception, e:
            self.error('^7Could not get superadmin group: %s', e)
            return False

        try:
            command = self._commands['iamgod']
        except:
            self.error('iamgod command not found')
            return False
        else:
            try:
                self.setCmdLevel(command, 'none')
            except Exception, msg:
                self.error('problem setting iamgod command level  %s', msg)
            else:
                if group in client.groups:
                    client.message('^7You are already a %s' % group.exactName)
                    return True

                client.setGroup(group)
                client.save()

                client.message('^7You are now a %s' % group.name)

                self.bot('^7Created %s %s - %s', group.name, client.name, client.guid)

            return True

    def cmd_time(self, data, client=None, cmd=None):
        """\
        [<timezone/offset>] - display the servers current time
        """
        cmd.sayLoudOrPM(client, self.getMessage('time', self.console.formatTime(time.time(), data)))

        return True

    def cmd_seen(self, data, client=None, cmd=None):
        """\
        <name> - when was a player last seen?
        """

        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        data = m[0]

        clients = self.console.clients.lookupByName(data)

        if len(clients) == 0:
            client.message(self.getMessage('no_players', data))
        else:
            for c in clients:
                cmd.sayLoudOrPM(client, self.getMessage('seen', c.exactName, self.console.formatTime(c.timeEdit)))

        return True

    def cmd_lookup(self, data, client=None, cmd=None):
        """\
        <name> - lookup a player in the database
        """

        if not self.console.storage.status():
            cmd.sayLoudOrPM(client, '^7Cannot lookup, database apears to be ^1DOWN')
            return

        m = re.match('^(.{1,})$', data)
        if not m:
            client.message('^7Invalid parameters')
            return False


        clients = self.console.clients.lookupByName(data)

        if len(clients) == 0:
            client.message(self.getMessage('no_players', data))
        else:
            for c in clients:
                cmd.sayLoudOrPM(client, self.getMessage('lookup_found', c.id, c.exactName, self.console.formatTime(c.timeEdit)))

        return True

    def cmd_status(self, data, client=None, cmd=None):
        """\
        - Report status of bot
        """
        if self.console.storage.status():
            cmd.sayLoudOrPM(client, '^7Database appears to be ^2UP')
        else:
            cmd.sayLoudOrPM(client, '^7Database appears to be ^1DOWN')

    def cmd_scream(self, data, client=None, cmd=None):
        """\
        <message> - yell a message to all player
        """
        thread.start_new_thread(self.sayMany, (data, 5, 1))

    def sayMany(self, msg, times=5, delay=1):
        for c in range(1,times + 1):
            self.console.say('^%i%s' % (c, msg))
            time.sleep(delay)

    def cmd_find(self, data, client=None, cmd=None):
        """\
        <name> - test to find a connected player
        """

        m = self.parseUserCmd(data)

        if not m:
            client.message('^7Invalid parameters')
            return False

        cid = m[0]
        sclient = self.findClientPrompt(cid, client)

        if sclient:
            cmd.sayLoudOrPM(client, '^7Found player matching %s [^2%s^7] %s' % (cid, sclient.cid, sclient.exactName))

    def cmd_clientinfo(self, data, client=None, cmd=None):
        """\
        <name> <field> - get info about a client
        """
        m = self.parseUserCmd(data, True)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, field = m

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            try:
                cmd.sayLoudOrPM(client, '%s^7: %s^7 is %s' % (sclient.exactName, field, getattr(sclient, field)))
            except:
                client.message('^7Unrecognized field %s' % field)

    def cmd_kick(self, data, client=None, cmd=None):
        """\
        <name> [<reason>] - kick a player
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m
        reason = self.getReason(keyword)

        if not reason and client.maxLevel < self.config.getint('settings', 'noreason_level'):
            client.message('^1ERROR: ^7You must supply a reason')
            return False

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.cid == client.cid:
                self.console.say(self.getMessage('kick_self', client.exactName))
                return True
            elif sclient.maxLevel >= client.maxLevel:
                if sclient.maskGroup:
                    client.message('^7%s ^7is a masked higher level player, can\'t kick' % client.exactName)
                else:
                    self.console.say(self.getMessage('kick_denied', sclient.exactName, client.exactName, sclient.exactName))
                return True
            else:
                sclient.kick(reason, keyword, client)
                return True
        elif re.match('^[0-9]+$', cid):
            # failsafe, do a manual client id ban
            self.console.kick(cid, reason, client)

    def cmd_kickall(self, data, client=None, cmd=None):
        """\
        <pattern> [<reason>] - kick all players matching <pattern>
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m
        reason = self.getReason(keyword)

        if not reason and client.maxLevel < self.config.getint('settings', 'noreason_level'):
            client.message('^1ERROR: ^7You must supply a reason')
            return False

        matches = self.console.clients.getByMagic(cid)
        for sclient in matches:
            if sclient.cid == client.cid:
                continue
            elif sclient.maxLevel >= client.maxLevel:
                continue
            else:
                sclient.kick(reason, keyword, client)

    def cmd_spank(self, data, client=None, cmd=None):
        """\
        <name> [<reason>] - spank a player, naughty boy!
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m
        reason = self.getReason(keyword)

        if not reason and client.maxLevel < self.config.getint('settings', 'noreason_level'):
            client.message('^1ERROR: ^7You must supply a reason')
            return False

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.cid == client.cid:
                self.console.say(self.getMessage('kick_self', client.exactName))
                return True
            elif sclient.maxLevel >= client.maxLevel:
                if sclient.maskGroup:
                    client.message('^7%s ^7is a masked higher level player, can\'t spank' % client.exactName)
                else:
                    self.console.say(self.getMessage('kick_denied', sclient.exactName, client.exactName, sclient.exactName))
                return True
            else:
                if reason:
                    self.console.say(self.getMessage('spanked_reason', sclient.exactName, client.exactName, reason))
                else:
                    self.console.say(self.getMessage('spanked', sclient.exactName, client.exactName))
                sclient.kick(reason, keyword, client, silent=True)
                return True
        elif re.match('^[0-9]+$', cid):
            # failsafe, do a manual client id ban
            self.console.kick(cid, reason, client)

    def cmd_spankall(self, data, client=None, cmd=None):
        """\
        <pattern> [<reason>] - kick all players matching <pattern>
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m
        reason = self.getReason(keyword)

        if not reason and client.maxLevel < self.config.getint('settings', 'noreason_level'):
            client.message('^1ERROR: ^7You must supply a reason')
            return False

        matches = self.console.clients.getByMagic(cid)
        for sclient in matches:
            if sclient.cid == client.cid:
                continue
            elif sclient.maxLevel >= client.maxLevel:
                continue
            else:
                if reason:
                    self.console.say(self.getMessage('spanked_reason', sclient.exactName, client.exactName, reason))
                else:
                    self.console.say(self.getMessage('spanked', sclient.exactName, client.exactName))
                sclient.kick(reason, keyword, client, silent=True)

    def cmd_permban(self, data, client=None, cmd=None):
        """\
        <name> [<reason>] - ban a player permanently
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m
        reason = self.getReason(keyword)

        if not reason and client.maxLevel < self.config.getint('settings', 'noreason_level'):
            client.message('^1ERROR: ^7You must supply a reason')
            return False

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.cid == client.cid:
                self.console.say(self.getMessage('ban_self', client.exactName))
                return True
            elif sclient.maxLevel >= client.maxLevel:
                if sclient.maskGroup:
                    client.message('^7%s ^7is a masked higher level player, can\'t ban' % client.exactName)
                else:
                    self.console.say(self.getMessage('ban_denied', client.exactName, sclient.exactName))
                return True
            else:
                sclient.groupBits = 0
                sclient.save()

                sclient.ban(reason, keyword, client)
                return True
        elif re.match('^[0-9]+$', cid):
            # failsafe, do a manual client id ban
            self.console.ban(cid, reason, client)

    def cmd_ban(self, data, client=None, cmd=None):
        """\
        <name> [<reason>] - ban a player
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m
        reason = self.getReason(keyword)

        if not reason and client.maxLevel < self.config.getint('settings', 'noreason_level'):
            client.message('^1ERROR: ^7You must supply a reason')
            return False

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.cid == client.cid:
                self.console.say(self.getMessage('ban_self', client.exactName))
                return True
            elif sclient.maxLevel >= client.maxLevel:
                if sclient.maskGroup:
                    client.message('^7%s ^7is a masked higher level player, can\'t ban' % client.exactName)
                else:
                    self.console.say(self.getMessage('ban_denied', client.exactName, sclient.exactName))
                return True
            else:
                sclient.groupBits = 0
                sclient.save()

                duration = self.config.getDuration('settings', 'ban_duration')
                sclient.tempban(reason, keyword, duration, client)
                return True
        elif re.match('^[0-9]+$', cid):
            # failsafe, do a manual client id ban
            duration = self.config.getDuration('settings', 'ban_duration')
            self.console.tempban(cid, reason, duration, client)

    def cmd_banall(self, data, client=None, cmd=None):
        """\
        <pattern> [<reason>] - ban all players matching <pattern>
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m
        reason = self.getReason(keyword)

        if not reason and client.maxLevel < self.config.getint('settings', 'noreason_level'):
            client.message('^1ERROR: ^7You must supply a reason')
            return False

        duration = self.config.getDuration('settings', 'ban_duration')
        matches = self.console.clients.getByMagic(cid)
        for sclient in matches:
            if sclient.cid == client.cid:
                continue
            elif sclient.maxLevel >= client.maxLevel:
                continue
            else:
                sclient.tempban(reason, keyword, duration, client)

    def cmd_baninfo(self, data, client=None, cmd=None):
        """\
        <name> - display how many bans a user has
        """

        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        sclient = self.findClientPrompt(m[0], client)
        if sclient:
            bans = sclient.numBans
            if bans:
                cmd.sayLoudOrPM(client, '^7%s ^7has %s active bans' % (sclient.exactName, bans))
            else:
                cmd.sayLoudOrPM(client, '^7%s ^7has no active bans' % sclient.exactName)

    def cmd_runas(self, data, client=None, cmd=None):
        """\
        <name> <command> - run a command as a different user
        """

        m = self.parseUserCmd(data)
        if not m or m[1] == '':
            client.message('^7Invalid parameters')
            return False

        sclient = self.findClientPrompt(m[0], client)
        if sclient:
            self.OnSay(b3.events.Event(b3.events.EVT_CLIENT_SAY, m[1], sclient))

    def cmd_unban(self, data, client=None, cmd=None):
        """\
        <name> - un-ban a player
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, reason = m
        reason = self.getReason(reason)

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            for w in sclient.bans:
                if w.adminId:
                    try:
                        admin = self.console.storage.getClient(clients.Client(id=w.adminId))
                        if admin.maxLevel > client.maxLevel:
                            client.message('^7You can not clear a ban from ' % admin.exactName)
                            return
                    except:
                        pass

            sclient.unban(reason, client)

    def cmd_aliases(self, data, client=None, cmd=None):
        """\
        <name> - list a players aliases
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid = m[0]

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.maskGroup:
                cmd.sayLoudOrPM(client, '^7%s^7 has no aliases' % sclient.exactName)
            else:
                myaliases = []
                for a in sclient.aliases:
                    myaliases.append('%s^7' % a.alias)
                    if len(myaliases) > 10:
                        myaliases.append('^7[^2and more^7]')
                        break

                if len(myaliases):
                    cmd.sayLoudOrPM(client, self.getMessage('aliases', sclient.exactName, string.join(myaliases, ', ')))
                else:
                    cmd.sayLoudOrPM(client, '^7%s^7 has no aliases' % sclient.exactName)

    def cmd_warns(self, data, client=None, cmd=None):
        """\
        - list warnings
        """
        ws = []
        for w in self.config.options('warn_reasons'):
            if w != 'default' and w != 'generic':
                ws.append(w)

        client.message('^7Warnings: %s' % string.join(ws, ', '))



    def cmd_notice(self, data, client=None, cmd=None):
        """\
        <name> <notice> - Add a good/bad behavior note for the player
        """
        m = self.parseUserCmd(data)
        if not m or m[0] == '' or m[1] == '':
            client.message('^7Invalid parameters')
            return False

        cid, notice = m
        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.maxLevel >= client.maxLevel:
                client.message('^7Can not add notice to higher level admin %s' % sclient.exactName)
            else:
                sclient.notice(notice, None, client)
                client.message('^7Notice %s added to %s' % (notice, sclient.exactName))

    def cmd_warn(self, data, client=None, cmd=None):
        """\
        <name> [<warning>] - warn user
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        cid, keyword = m
        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.id == client.id:
                client.message(self.getMessage('warn_self', client.exactName))
            elif sclient.maxLevel >= client.maxLevel:
                client.message(self.getMessage('warn_denied', client.exactName, sclient.exactName))
            else:
                if sclient.var(self, 'warnTime').toInt() > self.console.time() - self.config.getint('warn', 'warn_delay'):
                    client.message('^7Only one warning per %s seconds can be issued' % self.config.getint('warn', 'warn_delay'))
                    return False

                self.warnClient(sclient, keyword, client)

    def penalizeClient(self, type, client, reason, keyword=None, duration=0, admin=None, data=''):
        if reason == None:
            reason = self.getReason(keyword)

        duration = functions.time2minutes(duration)

        if type == self.PENALTY_KICK:
            client.kick(reason, keyword, admin, False, data)
        elif type == self.PENALTY_TEMPBAN:
            client.tempban(reason, keyword, duration, admin, False, data)
        elif type == self.PENALTY_BAN:
            client.ban(reason, keyword, admin, False, data)
        elif type == self.PENALTY_WARNING:
            self.warnClient(client, keyword, admin, True, data, duration)
        else:
            if self.console.inflictCustomPenalty(type, client=client, reason=reason, duration=duration, admin=admin, data=data) is not True:
                self.error('penalizeClient(): type %s not found', type)

    def warnClient(self, sclient, keyword, admin=None, timer=True, data='', newDuration=None):
        try:
            duration, warning = self.getWarning(keyword)
        except:
            duration, warning = self.getWarning('generic')
            warning = '%s %s' % (warning, keyword)

        if newDuration:
            duration = newDuration

        warnRecord = sclient.warn(duration, warning, keyword, admin, data)
        warning = sclient.exactName + '^7, ' + warning

        if timer:
            sclient.setvar(self, 'warnTime', self.console.time())

        warnings = sclient.numWarnings
        try:
            pmglobal = self.config.get('warn', 'pm_global')
        except:
            pmglobal = '0'
        if pmglobal == '1':
            msg = self.config.getTextTemplate('warn', 'message', warnings=warnings, reason=warning)
            sclient.message(msg)
            if admin:
                admin.message(msg)
        else:
            self.console.say(self.config.getTextTemplate('warn', 'message', warnings=warnings, reason=warning))
        if warnings >= self.config.getint('warn', 'instant_kick_num'):
            self.warnKick(sclient, admin)
        elif warnings >= self.config.getint('warn', 'alert_kick_num'):
            duration = functions.minutesStr(self.warnKickDuration(sclient))

            warn = sclient.lastWarning
            if warn:
                self.console.say(self.config.getTextTemplate('warn', 'alert', name=sclient.exactName, warnings=warnings, duration=duration, reason=warn.reason))
            else:
                self.console.say(self.config.getTextTemplate('warn', 'alert', name=sclient.exactName, warnings=warnings, duration=duration, reason='Too many warnings'))

            sclient.setvar(self, 'checkWarn', True)
            t = threading.Timer(25, self.checkWarnKick, (sclient, admin, data))
            t.start()

        return warnRecord


    def checkWarnKick(self, sclient, client=None, data=''):
        if not sclient.var(self, 'checkWarn').value:
            return

        sclient.setvar(self, 'checkWarn', False)

        kick_num = self.config.getint('warn', 'alert_kick_num')
        warnings = sclient.numWarnings
        if warnings >= kick_num:
            self.warnKick(sclient, client, data)

    def warnKickDuration(self, sclient):
        if sclient.numWarnings > self.config.getint('warn', 'tempban_num'):
            duration = self.config.getDuration('warn', 'tempban_duration')
        else:
            duration = 0
            for w in sclient.warnings:
                duration += w.duration * 60
            duration = (duration / self.config.getint('warn', 'duration_divider')) / 60

            maxDuration = self.config.getDuration('warn', 'max_duration')
            if duration > maxDuration:
                duration = maxDuration

        return duration

    def warnKick(self, sclient, client=None, data=''):
        msg = sclient.numWarnings
        keyword = ''
        warn = sclient.lastWarning
        if warn:
            msg = warn.reason
            keyword = warn.keyword

        duration = self.warnKickDuration(sclient)

        if duration > 0:
            if duration >= 300 and duration <= 600:
                msg = '^3peeing ^7in the gene pool'

            sclient.tempban(self.config.getTextTemplate('warn', 'reason', reason=msg), keyword, duration, client, False, data)

    def cmd_warntest(self, data, client=None, cmd=None):
        """\
        <warning> - test a warning
        """
        try:
            duration, warning = self.getWarning(data)
        except:
            duration, warning = self.getWarning('generic')
            warning = '%s %s' % (warning, data)

        warning = warning % { 'name' : client.exactName }

        client.message('^2TEST: %s' % self.config.getTextTemplate('warn', 'message', warnings=1, reason=warning))

        return True

    def cmd_warnremove(self, data, client=None, cmd=None):
        """\
        <name> - remove a users last warning
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        sclient = self.findClientPrompt(m[0], client)
        if sclient:
            w = sclient.lastWarning
            if not sclient.numWarnings or not w:
                client.message('^7No warnings found for %s' % sclient.exactName)
                return

            if w.adminId:
                try:
                    admin = self.console.storage.getClient(clients.Client(id=w.adminId))
                    if admin.maxLevel > client.maxLevel:
                        client.message('^7You can not clear a warning from %s' % admin.exactName)
                    return
                except:
                    pass

            w.inactive = 1
            self.console.storage.setClientPenalty(w)

            cmd.sayLoudOrPM(client, '%s ^7last warning cleared: ^3%s' % (sclient.exactName, w.reason))

    def cmd_warnclear(self, data, client=None, cmd=None):
        """\
        <name> - clear all of a users warnings
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        sclient = self.findClientPrompt(m[0], client)
        if sclient:
            if not sclient.numWarnings:
                client.message('^7No warnings found for %s' % sclient.exactName)
                return

            cleared = 0
            failed = 0
            for w in sclient.warnings:
                if w.adminId:
                    try:
                        admin = self.console.storage.getClient(clients.Client(id=w.adminId))
                        if admin.maxLevel > client.maxLevel:
                            failed += 1
                        break
                    except:
                        pass

                cleared += 1
                w.inactive = 1
                self.console.storage.setClientPenalty(w)

            if failed and cleared:
                cmd.sayLoudOrPM(client, '^7Cleared ^3%s ^7warnings and left ^3%s ^7warnings for %s' % (failed, cleared, sclient.exactName))
            elif failed:
                client.message('^7Could not clear ^3%s ^7warnings for %s' % (failed, sclient.exactName))
            else:
                self.console.say('^7All warnings cleared for %s' % sclient.exactName)

    def cmd_warninfo(self, data, client=None, cmd=None):
        """\
        <name> - display how many warning points a user has
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        sclient = self.findClientPrompt(m[0], client)
        if sclient:
            warns = sclient.numWarnings

            if warns:
                msg = ''
                warn = sclient.firstWarning
                if warn:
                    expire = functions.minutesStr((warn.timeExpire - (self.console.time())) / 60)
                    msg = ', expires in ^2%s' % expire

                warn = sclient.lastWarning
                if warn:
                    msg += '^7: ^3%s' % warn.reason

                message = '^7%s ^7has ^1%s ^7active warnings%s' % (sclient.exactName, warns, msg)
            else:
                message = '^7%s ^7has no active warnings' % sclient.exactName

            cmd.sayLoudOrPM(client, message)

    def cmd_maps(self, data, client=None, cmd=None):
        """\
        - list the server's map rotation
        """
        if not self.aquireCmdLock(cmd, client, 60, True):
            client.message('^7Do not spam commands')
            return

        maps = self.console.getMaps()
        if maps:
            cmd.sayLoudOrPM(client, '^7Map Rotation: ^2%s' % string.join(maps, '^7, ^2'))
        else:
            client.message('^7Error: could not get map list')

    def cmd_nextmap(self, data, client=None, cmd=None):
        """\
        - list the next map in rotation
        """
        if not self.aquireCmdLock(cmd, client, 60, True):
            client.message('^7Do not spam commands')
            return

        map = self.console.getNextMap()
        if map:
            cmd.sayLoudOrPM(client, '^7Next Map: ^2%s' % map)
        else:
            client.message('^7Error: could not get map list')

    def cmd_pause(self, data, client=None, cmd=None):
        """\
        <duration> - pause the bot from parsing
        """
        m = re.match('^([0-9]+[a-z]*)$', data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        duration = functions.time2minutes(data)

        self.console.say('^7Sleeping for %s' % functions.minutesStr(duration))
        time.sleep(duration * 60)
        self.console.say('^7Waking up after sleep')
        self.console.input.seek(0, 2)

    def cmd_spam(self, data, client=None, cmd=None):
        """\
        <name> <message> - spam a predefined message
        """
        m = re.match('^([^ ]{2,})$', data)
        if not m:
            client.message('^7Invalid parameters')
            return False

        keyword = m.group(1)
        s = self.getSpam(keyword)
        if s:
            self.console.say(s)
        else:
            client.message('^7Could not find spam message %s' % keyword)

    def cmd_rules(self, data, client=None, cmd=None):
        """\
        - say the rules
        """
        if not self.aquireCmdLock(cmd, client, 60, True):
            client.message('^7Do not spam commands')
            return

        m = self.parseUserCmd(data)
        if m:
            if client.maxLevel >= self.config.getint('settings', 'admins_level'):
                sclient = self.findClientPrompt(m[0], client)
                if not sclient:
                    return

                if sclient.maxLevel >= client.maxLevel:
                    client.message('%s ^7already knows the rules' % sclient.exactName)
                    return
                else:
                    client.message('^7Sir, Yes Sir!, spamming rules to %s' % sclient.exactName)
            else:
                client.message('^7Stop trying to spam other players')
                return
        elif cmd.loud:
            thread.start_new_thread(self._sendRules, (None,))
            return
        else:
            sclient = client

        thread.start_new_thread(self._sendRules, (sclient,))

    def _sendRules(self, sclient):
        rules = []

        for i in range(1, 20):
            try:
                rule = self.config.getTextTemplate('spamages', 'rule%s' % i)
                rules.append(rule)
            except:
                break

        if sclient:
            for rule in rules:
                sclient.message(rule)
                time.sleep(1)
        else:
            for rule in rules:
                self.console.say(rule)
                time.sleep(1)

    def cmd_spams(self, data, client=None, cmd=None):
        """\
        - list spam messages
        """
        ws = []
        for w in self.config.options('spamages'):
            ws.append(w)

        client.message('^7Spamages: %s' % string.join(ws, ', '))

    def cmd_tempban(self, data, client=None, cmd=None):
        """\
        <name> <duration> [<reason>] - temporarily ban a player
        """
        m = self.parseUserCmd(data)

        if not m:
            client.message('^7Invalid parameters')
            return False

        cid = m[0]
        m = re.match('^([0-9]+[dwhsm]*)(?:\s(.+))?$', m[1], re.I)
        if not m:
            client.message('^7Invalid parameters')
            return False

        duration, keyword = m.groups()
        duration = functions.time2minutes(duration)
        #    10/05/2008 - 1.3.4b0 - mindriot
        #      * Removed hard code of 1 day for long_tempban_level - now controlled with new setting 'long_tempban_max_duration'
        try:
            long_tempban_max_duration = self.config.getDuration('settings', 'long_tempban_max_duration')
        except:
            long_tempban_max_duration = self._long_tempban_max_duration
            self.debug('Using default value (%s) for long_tempban_max_duration', self._long_tempban_max_duration)

        if client.maxLevel < self.config.getint('settings', 'long_tempban_level') and duration > long_tempban_max_duration:
            # temp ban for maximum specified in settings
            duration = long_tempban_max_duration

        
        reason = self.getReason(keyword)

        if not reason and client.maxLevel < self.config.getint('settings', 'noreason_level'):
            client.message('^1ERROR: ^7You must supply a reason')
            return False
        elif not duration:
            client.message('^7You must supply a duration to ban for')
            return False

        sclient = self.findClientPrompt(cid, client)
        if sclient:
            if sclient.cid == client.cid:
                self.console.say(self.getMessage('temp_ban_self', client.exactName))
                return True
            elif sclient.maxLevel >= client.maxLevel:
                if sclient.maskGroup:
                    client.message('^7%s ^7is a masked higher level player, can\'t temp ban' % client.exactName)
                else:
                    self.console.say(self.getMessage('temp_ban_denied', client.exactName, sclient.exactName))
                return True
            else:
                sclient.tempban(reason, keyword, duration, client)
                return True
        elif re.match('^[0-9]+$', cid):
            # failsafe, do a manual client id ban
            self.console.tempban(cid, reason, duration, client)

    def cmd_poke(self, data, client=None, cmd=None):
        """\
        <player> - Notify a player that he needs to move
        """

        m = self.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters, you must supply a player name')
            return False

        if m[0] == 'b3':
            self.warnClient(client, 'Do not poke b3!', None, False, '', 1)
        else:
            sclient = self.findClientPrompt(m[0], client)
            if sclient:
                self.console.say('^7%s %s^7!' % (random.choice(('Wake up', '*poke*', 'Attention', 'Get up', 'Go', 'Move out')), sclient.exactName))

#--------------------------------------------------------------------------------------------------
#commandstxt = file('commands.txt', 'w')
class Command:
    command  = ''
    help     = ''
    level    = 0
    secretLevel = 0
    func     = None
    alias    = ''
    plugin = None
    time = 0
    prefix = '!'
    prefixLoud = '@'

    PLAYER_DATA = re.compile(r'^([\w\d\s-]+|@\d+|\d+)$', re.I)
    _reType = type(re.compile('.*'))

    def __init__(self, plugin, cmd, level, func, help=None, alias=None, secretLevel=100):
        self.command = cmd.strip()
        self.func = func
        self.plugin = plugin
        self.loud = False

        if help:
            self.help = help.strip()
        if alias:
            self.alias = alias.strip()

        level = str(level)
        if level.lower() == 'none':
            self.level = None
        elif level.count('-') == 1:
            level = level.split('-', 1)
            self.level = (int(level[0]), int(level[1]))
        else:
            self.level = (int(level), 100)

        if secretLevel is None:
            self.secretLevel = 100

        #global commandstxt
        #commandstxt.write('%s (%s) %s, levels %s - %s\n' % (self.command, self.alias, self.help, self.level[0], self.level[1]))
        #commandstxt.flush()

    def canUse(self, client):
        if self.level == None:
            return False
        elif int(client.maxLevel) >= self.level[0] and int(client.maxLevel) <= self.level[1]:
            return True
        else:
            return False

    def execute(self, data, client):
        self.func(data, client, copy.copy(self))
        self.time = self.plugin.console.time()

    def executeLoud(self, data, client):
        cmd = copy.copy(self)
        cmd.loud = True
        self.func(data, client, cmd)
        self.time = self.plugin.console.time()

    def sayLoudOrPM(self, client, message):
        if self.loud:
            self.plugin.console.say(message)
        else:
            client.message(message)

    def parseData(self, data, *args):
        p = self.splitData(data)

        if not len(args):
            return p

        params = {}

        for i in range(0, min(len(args), len(p))):
            params[args[i][0]] = p[i]

        if len(p) > i:
            params[args[i][0]] = ' '.join(p[i:])

        badfield = None
        valid = True
        for a in args:
            if (not params.has_key(a[0]) or len(params[a[0]]) == 0):
                if len(a) == 3:
                    # set the default
                    params[a[0]] = a[2]
                else:
                    badfield = a[0]
                    valid = False
                    break

            if len(a) > 1:
                if type(a[1]) == self._reType:
                    # see if it matches regexp
                    valid = re.match(a[1], params[a[0]])

                    if not valid:
                        badfield = a[0]
                else:
                    # see if it can be converted to type
                    try:
                        params[a[0]] = a[1](params[a[0]])
                    except:
                        badfield = a[0]
                        valid = False

        if valid:
            return (params, None)
        else:
            help = ['^1Input Error! ^7Example: ']
            if self.loud:
                help.append('%s%s' % (self.prefixLoud, self.command))
            else:
                help.append('%s%s' % (self.prefix, self.command))

            for a in args:
                if len(a) == 3:
                    #optional
                    parm = '[%s]' % a[0]
                else:
                    parm = '<%s>' % a[0]

                if a[0] == badfield:
                    parm = '^1%s^7' % parm

                help.append(parm)

            return (None, ' '.join(help))

    def splitData(self, data):
        params = []
        buf = ''
        inQuote  = False
        inDQuote = False
        for c in str(data).strip():
            if c == "'":
                if inDQuote:
                    buf += c
                elif inQuote:
                    params.append(buf)
                    buf = ''
                    inQuote = False
                elif len(buf):
                    buf += c
                else:
                    inQuote = True
                    buf = ''
            elif c == '"':
                if inDQuote:
                    params.append(buf)
                    buf = ''
                    inDQuote = False
                elif inQuote:
                    buf += c
                elif len(buf):
                    buf += c
                else:
                    inDQuote = True
                    buf = ''
            elif c.isspace():
                if len(buf):
                    if inDQuote or inQuote:
                        if not buf[-1].isspace():
                            buf += c
                    else:
                        params.append(buf)
                        buf = ''
            else:
                buf += c

        if len(buf):
            params.append(buf)

        return params
    
if __name__ == '__main__':
    from b3.fake import FakeConsole
    from b3.fake import joe
    import time
    
    print "___________________________________"
    fakeConsole = FakeConsole('@b3/conf/b3.xml')
    p = AdminPlugin(fakeConsole, '@b3/conf/plugin_admin.xml')
    
    def say(msg):
        p.OnSay(b3.events.Event(b3.events.EVT_CLIENT_SAY, msg, joe))

    say('#test')
    say('#clients')
    say('#groups')
    say('#vars')
    say('#varsjoe')
    say('#tkinfo')
    say('#tkinfojoe')
    say('!!')
    say('!help')
    say('hello')
    
