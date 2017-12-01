# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

__author__  = 'PtitBigorneau - www.ptitbigorneau.fr'
__version__ = '1.5.2'

import b3
import b3.plugin
import b3.events

from b3.functions import getCmd


class FirstkillPlugin(b3.plugin.Plugin):

    _adminPlugin = None

    _firstkill = True
    _firsttk = True
    _firsths = False

    _kill = 0
    _tk = 0
    _hs = 0

    _default_messages = {
        'first_kill': '^2First Kill^3: $client killed $target',
        'first_kill_by_headshot': '^2First Kill ^5by Headshot^3: $client killed $target',
        'first_teamkill': '^1First TeamKill^3: $client teamkilled $target',
    }

    ####################################################################################################################
    #                                                                                                                  #
    #   STARTUP                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        self._firstkill = self.getSetting('settings', 'firstkill', b3.BOOL, self._firstkill)
        self._firsttk = self.getSetting('settings', 'firsttk', b3.BOOL, self._firsttk)
        if self.console.gameName in ('iourt41', 'iourt42', 'iourt43'):
            self._firsths = self.getSetting('settings', 'firsths', b3.BOOL, self._firsths)

    def onStartup(self):
        """
        Initialize plugin.
        """
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            raise AttributeError('could not find admin plugin')

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

        if self.console.gameName not in ('iourt41', 'iourt42', 'iourt43'):
            self.info('NOTE: !firsths command is available only in UrbanTerror 4.x game serie')
            self._adminPlugin.unregisterCommand('firsths')

        # register events needed
        self.registerEvent('EVT_CLIENT_KILL', self.onClientKill)
        self.registerEvent('EVT_CLIENT_KILL_TEAM', self.onClientKillTeam)
        self.registerEvent('EVT_GAME_MAP_CHANGE', self.onMapChange)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onMapChange(self, _):
        """
        Handle EVT_ROUND_START
        """
        self._kill = 0
        self._tk = 0
        self._hs = 0

    def onClientKill(self, event):
        """
        Handle EVT_CLIENT_KILL
        """
        self._kill += 1
        if self._firstkill and self._kill == 1:
            client = event.client
            target = event.target
            if self._firsths and \
                self.console.gameName in ('iourt41', 'iourt42', 'iourt43') and \
                    event.data[2] in (self.console.HL_HEAD, self.console.HL_HELMET) and \
                        event.data[1] not in (self.console.UT_MOD_BLED, self.console.UT_MOD_HEGRENADE):
                self._hs += 1
                if self._hs == 1:
                    self.announce_first_kill_by_headshot(client, target)
                else:
                    self.announce_first_kill(client, target)
            else:
                self.announce_first_kill(client, target)

    def onClientKillTeam(self, event):
        """
        Handle EVT_CLIENT_KILL_TEAM
        """
        self._tk += 1
        if self._firsttk and self._tk == 1:
            self.announce_first_teamkill(event.client, event.target)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def announce_something(self, message):
        """
        Announce something by printing it on the screen
        :param message: the message to be printed
        """
        if self.console.gameName in ('iourt41', 'iourt42', 'iourt43'):
            self.console.write('bigtext "%s"' % message)
        elif self.console.gameName[:3] == 'cod':
            self.console.say(message)
        else:
            self.console.saybig(message)

    def announce_first_kill(self, client, target):
        """
        Announce the First Kill on the current map
        :param client: the client who made the kill
        :param target: the target who suffered the kill
        """
        self.announce_something(self.getMessage('first_kill', {'client': client.exactName, 'target': target.exactName}))

    def announce_first_kill_by_headshot(self, client, target):
        """
        Announce the First Kill (with headshot) on the current map
        :param client: the client who made the kill
        :param target: the target who suffered the kill
        """
        self.announce_something(self.getMessage('first_kill_by_headshot', {'client': client.exactName, 'target': target.exactName}))

    def announce_first_teamkill(self, client, target):
        """
        Announce the First TeamKill on the current map
        :param client: the client who made the kill
        :param target: the target who suffered the kill
        """
        self.announce_something(self.getMessage('first_teamkill', {'client': client.exactName, 'target': target.exactName}))

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_firstkill(self, data, client, cmd=None):
        """
        [<on|off>] - activate / deactivate firstkill
        """
        if not data:
            cmd.sayLoudOrPM(client, '^7Firstkill: %s' % '^2ON' if self._firstkill else '^1OFF')
        else:
            data = data.lower()
            if data not in ('on', 'off'):
                client.message('^7Invalid data, try !help firstkill')
            elif data == 'on':
                self._firstkill = True
                cmd.sayLoudOrPM(client, '^7Firstkill: ^2ON')
            else:
                self._firstkill = False
                cmd.sayLoudOrPM(client, '^7Firstkill: ^1OFF')

    def cmd_firsttk(self, data, client, cmd=None):
        """
        [<on|off>] - activate / deactivate first teamkill
        """
        if not data:
            cmd.sayLoudOrPM(client, '^7First Teamkill: %s' % '^2ON' if self._firsttk else '^1OFF')
        else:
            data = data.lower()
            if data not in ('on', 'off'):
                client.message('^7Invalid data, try !help firsttk')
            elif data == 'on':
                self._firsttk = True
                cmd.sayLoudOrPM(client, '^7First Teamkill: ^2ON')
            else:
                self._firsttk = False
                cmd.sayLoudOrPM(client, '^7First Teamkill: ^1OFF')

    def cmd_firsths(self, data, client, cmd=None):
        """
        [<on|off>] - activate / deactivate first kill by headshot
        """
        if not data:
            cmd.sayLoudOrPM(client, '^7First Kill by Headshot: %s' % '^2ON' if self._firsths else '^1OFF')
        else:
            data = data.lower()
            if data not in ('on', 'off'):
                client.message('^7Invalid data, try !help firsttk')
            elif data == 'on':
                self._firsths = True
                cmd.sayLoudOrPM(client, '^7First Kill by Headshot: ^2ON')
            else:
                self._firsths = False
                cmd.sayLoudOrPM(client, '^7First Kill by Headshot: ^1OFF')