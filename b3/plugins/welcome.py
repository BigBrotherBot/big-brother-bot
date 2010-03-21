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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
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

__version__ = '1.1'
__author__    = 'ThorN'

import b3, threading, time, re
import b3.events
import b3.plugin

#--------------------------------------------------------------------------------------------------
class WelcomePlugin(b3.plugin.Plugin):
    _newbConnections = 0
    _welcomeFlags = 0
    _welcomeDelay = 0
    _cmd_greeting_minlevel = None

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
            
        self._welcomeFlags = self.config.getint('settings', 'flags')
        self._newbConnections = self.config.getint('settings', 'newb_connections')
        try:
            self._welcomeDelay = self.config.getint('settings', 'delay')
            if self._welcomeDelay < 15 or self._welcomeDelay > 90:
                self._welcomeDelay = 30
                self.debug('Welcome delay not in range 15-90 using 30 instead.')
        except:
            self._welcomeDelay = 30

    
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

    def onEvent(self, event):
        if event.type == b3.events.EVT_CLIENT_AUTH:
            if    self._welcomeFlags < 1 or \
                not event.client or \
                not event.client.id or \
                event.client.cid == None or \
                not event.client.connected or \
                event.client.pbid == 'WORLD' or \
                self.console.upTime() < 300:
                return

            t = threading.Timer(self._welcomeDelay, self.welcome, (event.client,))
            t.start()

    def welcome(self, client):
        _timeDiff = 0
        if client.lastVisit:
            self.debug('LastVisit: %s' %(self.console.formatTime(client.lastVisit)))
            _timeDiff = time.time() - client.lastVisit
        else:
            self.debug('LastVisit not available. Must be the first time.')
            _timeDiff = 1000000 # big enough so it will welcome new players

        # don't need to welcome people who got kicked or where already welcomed in the last hour
        if client.connected and _timeDiff > 3600:
            info = {
                'name'    : client.exactName,
                'id'    : str(client.id),
                'connections' : str(client.connections)
            }

            if client.maskedGroup:
                info['group'] = client.maskedGroup.name
                info['level'] = str(client.maskedGroup.level)
            else:
                info['group'] = 'None'
                info['level'] = '0'

            if client.connections >= 2:
                #info['lastVisit'] = self.console.formatTime(client.timeEdit)
                info['lastVisit'] = self.console.formatTime(client.lastVisit)
            else:
                info['lastVisit'] = 'Unknown'

            if client.connections >= 2:
                if client.maskedGroup:
                    if self._welcomeFlags & 16:
                        client.message(self.getMessage('user', info))
                elif self._welcomeFlags & 1:
                    client.message(self.getMessage('newb', info))

                if self._welcomeFlags & 2 and client.connections < self._newbConnections:
                    self.console.say(self.getMessage('announce_user', info))
            else:
                if self._welcomeFlags & 4:
                    client.message(self.getMessage('first', info))
                if self._welcomeFlags & 8:
                    self.console.say(self.getMessage('announce_first', info))

            if self._welcomeFlags & 32 and client.greeting:
                info['greeting'] = client.greeting % info
                self.console.say(self.getMessage('greeting', info))
        else:
            if _timeDiff <= 3600:
                self.debug('Client already welcomed in the past hour')
