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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# 2013/04/13 - 1.2.1 - Courgette
#  * refactoring
#  * prevent setting a custom greeting which would use the $greeting placeholder
#  * fix newb message that was broken since we added the Guest default group to the admin plugin
# 2010/10/17 - 1.2 - Courgette
#  * add min_gap to customize how long the bot must wait before welcoming a
#    player again (in seconds)
#  * add tests
# 2010/03/21 - 1.1 - Courgette
#    import cmd_greeting from the admin plugin 
# 3/4/2009 - 1.0.6 - xlr8or
#    Added welcome delay setting to config
# 3/3/2009 - 1.0.5 - xlr8or
#    Fixed another error that caused an exception on new users
# 2/28/2009 - 1.0.4 - xlr8or
#    Removed error generated in welcoming thread on first time players
# 2/26/2009 - 1.0.3 - xlr8or
#    Do not welcome players that where already welcomed in the last hour
import threading
import time
import re
from ConfigParser import NoOptionError
import b3
import b3.events
import b3.plugin

__version__ = '1.2.1'
__author__ = 'ThorN'

F_FIRST = 4
F_NEWB = 1
F_USER = 16
F_ANNOUNCE_FIRST = 8
F_ANNOUNCE_USER = 2
F_CUSTOM_GREETING = 32

#--------------------------------------------------------------------------------------------------
class WelcomePlugin(b3.plugin.Plugin):
    _newbConnections = 0
    _welcomeFlags = 0
    _welcomeDelay = 0
    _cmd_greeting_minlevel = None
    _min_gap = 3600

    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)

    def onLoadConfig(self):
        try:
            self._cmd_greeting_minlevel = self.config.getint('commands', 'greeting')
        except:
            self._cmd_greeting_minlevel = 20
            self.warning('using default value %s for command !greeting' % self._cmd_greeting_minlevel)
        
        self._adminPlugin = self.console.getPlugin('admin')
        if self._adminPlugin:
            self._adminPlugin.registerCommand(self, 'greeting', self._cmd_greeting_minlevel, self.cmd_greeting)

        try:
            self._welcomeFlags = self.config.getint('settings', 'flags')
        except (NoOptionError, KeyError), err:
            self._welcomeFlags = 63
            self.warning("Using default value %s for 'settings/flags'. %s" % (self._welcomeFlags, err))
        except Exception, err:
            self._welcomeFlags = 63
            self.error("Using default value %s for 'settings/flags'. %s" % (self._welcomeFlags, err))

        try:
            self._newbConnections = self.config.getint('settings', 'newb_connections')
        except (NoOptionError, KeyError), err:
            self._newbConnections = 15
            self.warning("Using default value %s for 'settings/newb_connections'. %s" % (self._newbConnections, err))
        except Exception, err:
            self._newbConnections = 15
            self.error("Using default value %s for 'settings/newb_connections'. %s" % (self._newbConnections, err))

        try:
            self._welcomeDelay = self.config.getint('settings', 'delay')
            if self._welcomeDelay < 15 or self._welcomeDelay > 90:
                self._welcomeDelay = 30
                self.debug('Welcome delay not in range 15-90 using 30 instead.')
            self.info('delay set to %s. The bot will wait %ss after a player connects to write the welcome message' % (self._welcomeDelay, self._welcomeDelay))
        except:
            self._welcomeDelay = 30

        try:
            self._min_gap = self.config.getint('settings', 'min_gap')
            if self._min_gap < 0:
                self._min_gap = 0
            self.info('min_gap set to %s. The bot will not welcome a player more than once every %s seconds' % (self._min_gap, self._min_gap))
        except:
            self._min_gap = 3600
            self.warning('error while reading min_gap from config. min_gap set to %s (default).' % (self._min_gap))
            
    def cmd_greeting(self, data, client, cmd=None):
        """\
        [<greeting>] - set or list your greeting (use 'none' to remove)
        """
        if data.lower() == 'none':
            client.greeting = ''
            client.save()
            client.message(self.getMessage('greeting_cleared'))
        elif data:
            prepared_data = re.sub(r'\$(name|maxLevel|group|connections)', r'%(\1)s', data)

            if len(prepared_data) > 255:
                client.message('^7Your greeting is too long')
            else:
                try:
                    client.message('Greeting Test: %s' % (str(prepared_data) % {
                        'name': client.exactName,
                        'maxLevel': client.maxLevel,
                        'group': getattr(client.maxGroup, 'name', None),
                        'connections': client.connections
                    }))
                except ValueError, msg:
                    client.message(self.getMessage('greeting_bad', msg))
                    return False
                else:
                    client.greeting = prepared_data
                    client.save()
                    client.message(self.getMessage('greeting_changed', data))
                    return True
        else:
            if client.greeting:
                client.message(self.getMessage('greeting_yours', client.greeting))
            else:
                client.message(self.getMessage('greeting_empty'))

    def onEvent(self, event):
        if event.type == b3.events.EVT_CLIENT_AUTH:
            if self._welcomeFlags < 1 or \
                    not event.client or \
                    event.client.id is None or \
                    event.client.cid is None or \
                    not event.client.connected or \
                    event.client.pbid == 'WORLD':
                return
            if self.console.upTime() < 300:
                self.debug('not welcoming player because the bot started less than 5 min ago')
                return
            t = threading.Timer(self._welcomeDelay, self.welcome, (event.client,))
            t.start()

    def welcome(self, client):
        if client.lastVisit:
            self.debug('LastVisit: %s' % self.console.formatTime(client.lastVisit))
            _timeDiff = time.time() - client.lastVisit
        else:
            self.debug('LastVisit not available. Must be the first time.')
            _timeDiff = 1000000  # big enough so it will welcome new players

        # don't need to welcome people who got kicked or where already 
        # welcomed in before _min_gap s ago
        if client.connected and _timeDiff > self._min_gap:
            info = self.get_client_info(client)
            if client.connections >= 2:
                if client.maskedLevel > 0:
                    if self._welcomeFlags & F_USER:
                        client.message(self.getMessage('user', info))
                elif self._welcomeFlags & F_NEWB:
                    client.message(self.getMessage('newb', info))

                if self._welcomeFlags & F_ANNOUNCE_USER and client.connections < self._newbConnections:
                    self.console.say(self.getMessage('announce_user', info))
            else:
                if self._welcomeFlags & F_FIRST:
                    client.message(self.getMessage('first', info))
                if self._welcomeFlags & F_ANNOUNCE_FIRST:
                    self.console.say(self.getMessage('announce_first', info))

            if self._welcomeFlags & F_CUSTOM_GREETING and client.greeting:
                _info = {'greeting': client.greeting % info}
                _info.update(info)
                self.console.say(self.getMessage('greeting', _info))
        else:
            if _timeDiff <= self._min_gap:
                self.debug('Client already welcomed in the past %s seconds' % self._min_gap)

    def get_client_info(self, client):
        assert client
        info = {
            'name': client.exactName,
            'id': str(client.id),
            'connections': str(client.connections)
        }

        if client.maskedGroup:
            info['group'] = client.maskedGroup.name
            info['level'] = str(client.maskedGroup.level)
        else:
            info['group'] = 'None'
            info['level'] = '0'

        if client.connections >= 2 and client.lastVisit:
            info['lastVisit'] = self.console.formatTime(client.lastVisit)
        else:
            info['lastVisit'] = 'Unknown'

        return info