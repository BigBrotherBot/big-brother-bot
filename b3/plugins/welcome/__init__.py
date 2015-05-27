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
import threading
import time
import re

from b3.functions import getCmd
from ConfigParser import NoOptionError

__version__ = '1.4'
__author__ = 'ThorN, xlr8or, Courgette'

F_FIRST = 4
F_NEWB = 1
F_USER = 16
F_ANNOUNCE_FIRST = 8
F_ANNOUNCE_USER = 2
F_CUSTOM_GREETING = 32


class WelcomePlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _newbConnections = 15
    _welcomeFlags = F_FIRST | F_NEWB | F_USER | F_ANNOUNCE_FIRST | F_ANNOUNCE_USER | F_CUSTOM_GREETING
    _welcomeDelay = 30
    _min_gap = 3600

    _default_messages = {
        'first': '^7Welcome $name^7, this must be your first visit, you are player ^3#$id. Type !help for help',
        'newb': '^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit. '
                'Type !register in chat to register. Type !help for help',
        'user': '^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit^7, '
                'you\'re a ^2$group^7, played $connections times',
        'announce_first': '^7Everyone welcome $name^7, player number ^3#$id^7, to the server',
        'announce_user': '^7Everyone welcome back $name^7, player number ^3#$id^7, to the server, '
                         'played $connections times',
        'greeting': '^7$name^7 joined: $greeting',
        'greeting_empty': '^7You have no greeting set',
        'greeting_yours': '^7Your greeting is %s',
        'greeting_bad': '^7Greeting is not formatted properly: %s',
        'greeting_changed': '^7Greeting changed to: %s',
        'greeting_cleared': '^7Greeting cleared',
    }

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize the plugin
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

        # register events needed
        self.registerEvent('EVT_CLIENT_AUTH', self.onAuth)

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        self._load_config_flags()

        try:
            self._newbConnections = self.config.getint('settings', 'newb_connections')
            self.debug('loaded settings/newb_connections: %s' % self._newbConnections)
        except (NoOptionError, ValueError), e:
            self._newbConnections = 15
            self.error('could not load settings/newb_connections config value: %s' % e)
            self.debug('using default value (%s) for settings/newb_connections' % self._newbConnections)

        try:
            self._welcomeDelay = self.config.getint('settings', 'delay')
            self.debug('loaded settings/delay: %s' % self._welcomeDelay)
            if self._welcomeDelay < 15 or self._welcomeDelay > 90:
                self._welcomeDelay = 30
                self.debug('welcome delay not in range 15-90: using 30 instead')
        except (NoOptionError, ValueError), e:
            self._welcomeDelay = 30
            self.error('could not load settings/delay config value: %s' % e)
            self.debug('using default value (%s) for settings/delay' % self._welcomeDelay)

        self.info('welcomer delay set to %s: the bot will wait %ss after a player connects '
                  'to write the welcome message' % (self._welcomeDelay, self._welcomeDelay))

        try:
            self._min_gap = self.config.getint('settings', 'min_gap')
            self.debug('loaded settings/min_gap: %s' % self._min_gap)
            if self._min_gap < 0:
                self._min_gap = 0
                self.debug('min_gap must be positive or 0: using 0 instead')
        except (NoOptionError, ValueError), e:
            self._min_gap = 3600
            self.error('could not load settings/min_gap config value: %s' % e)
            self.debug('using default value (%s) for settings/min_gap' % self._min_gap)

        self.info('min_gap set to %s: the bot will not welcome a player more than once '
                  'every %s seconds' % (self._min_gap, self._min_gap))

    def _load_config_flags(self):
        """
        Load configuration flags
        """
        flag_options = [
            ("welcome_first", F_FIRST),
            ("welcome_newb", F_NEWB),
            ("welcome_user", F_USER),
            ("announce_first", F_ANNOUNCE_FIRST),
            ("announce_user", F_ANNOUNCE_USER),
            ("show_user_greeting", F_CUSTOM_GREETING)
        ]

        config_options = zip(*flag_options)[0]

        def set_flag(flag):
            self._welcomeFlags |= flag

        def unset_flag(flag):
            self._welcomeFlags &= ~flag

        if not any(map(lambda o: self.config.has_option('settings', o), config_options)):
            if self.config.has_option('settings', 'flags'):
                # old style config
                try:
                    self._welcomeFlags = self.config.getint('settings', 'flags')
                    self.debug('loaded settings/flags: %s' % self._welcomeFlags)
                except (NoOptionError, ValueError), e:
                    self.error('could not load settings/flags config value: %s' % e)
                    self.debug('using default value (%s) for settings/flags' % self._welcomeFlags)
            else:
                self.warning("could not find any of '%s' in config: all welcome messages will be shown" %
                             "', '".join(config_options))
        else:
            for opt, F in flag_options:
                if self.config.has_option("settings", opt):
                    try:
                        _ = self.config.getboolean("settings", opt)
                        set_flag(F) if _ else unset_flag(F)
                    except (NoOptionError, ValueError), e:
                        self.error('could not load settings/%s config value: %s' % (opt, e))
                        self.debug('using default value (yes) for settings/%s' % opt)
                else:
                    set_flag(F)
                    self.warning('could not find settings/%s config value' % opt)
                    self.debug('using default value (yes) for settings/%s' % opt)

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH
        """
        if self._welcomeFlags <= 0 or \
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

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def welcome(self, client):
        """
        Welcome a player
        """
        if client.lastVisit:
            self.debug('lastVisit: %s' % self.console.formatTime(client.lastVisit))
            _timeDiff = time.time() - client.lastVisit
        else:
            self.debug('lastVisit not available: must be the first time')
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
                self.debug('client already welcomed in the past %s seconds' % self._min_gap)

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

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_greeting(self, data, client, cmd=None):
        """
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