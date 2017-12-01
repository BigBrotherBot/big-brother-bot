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

import string
import b3.events
import b3.plugin

from b3.functions import hash_password
from b3.clients import Client
from ConfigParser import NoOptionError

__author__ = 'Tim ter Laak'
__version__ = '1.4'


class LoginPlugin(b3.plugin.Plugin):

    _adminPlugin = None

    _pmcomm = ''
    _threshold = 1000
    _passwdlevel = 100

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        self._threshold = self.getSetting('settings', 'thresholdlevel', b3.INT, self._threshold)
        self._passwdlevel = self.getSetting('settings', 'passwdlevel', b3.INT, self._passwdlevel)

    def onStartup(self):
        """
        Plugin startup.
        """
        self._adminPlugin = self.console.getPlugin('admin')

        # register the events needed
        self.registerEvent('EVT_CLIENT_AUTH', self.onAuth)

        # register our commands
        self._adminPlugin.registerCommand(self, 'login', 2, self.cmd_login, secretLevel=1)
        self._adminPlugin.registerCommand(self, 'setpassword', self._passwdlevel, self.cmd_setpassword)

        # Whats the command to send a private message?
        self._pmcomm = '/m' if self.console.gameName[:5] == 'etpro' else '/tell'
        self.debug('using "%s" as the private messaging command' % self._pmcomm)

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH
        """
        client = event.client
        if client.maxLevel > self._threshold and not client.isvar(self, 'loggedin'):
            client_from_db = self._get_client_from_db(client.id)
            # save original groupbits
            client.setvar(self, 'login_groupbits', client_from_db.groupBits)

            try:
                # set new groupBits
                g = self.console.storage.getGroup('reg')
                client.groupBits = g.id
            except Exception:
                client.groupBits = 2

            if not client_from_db.password:
                m = 'You need a password to use all your privileges: ask the administrator to set a password for you'
                client.message(m)
            else:
                m = 'Login via console: %s %s !login yourpassword' % (self._pmcomm, client.cid)
                client.message(m)

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def _get_client_from_db(self, client_id):
        """
        Retrieve a client from the storage layer.
        :param client_id: The client database id
        """
        return self.console.storage.getClient(Client(id=client_id))

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_login(self, data, client, cmd=None):
        """
        <password> - login a privileged user to his full capabilities
        """
        if client.isvar(self, 'loggedin'):
            client.message('You are already logged in')
            return

        if not client.isvar(self, 'login_groupbits'):
            client.message('You do not need to log in')
            return

        if data:
            digest = hash_password(data)
            client_from_db = self._get_client_from_db(client.id)
            if digest == client_from_db.password:
                client.setvar(self, 'loggedin', 1)
                client.groupBits = client.var(self, 'login_groupbits').value
                client.message('You are successfully logged in')
            else:
                client.message('^1***Access denied***^7')
        else:
            message = 'Usage (via console): %s %s !login yourpassword' % (self._pmcomm, client.cid)
            client.message(message)
        
    def cmd_setpassword(self, data, client, cmd=None):
        """
        <password> [<client>] - set a password for a client
        """
        if not data:
            client.message('Usage: %s%s <new password> [<client>]' % (cmd.prefix, cmd.command))
            return

        data = string.split(data)
        if len(data) > 1:
            sclient = self._adminPlugin.findClientPrompt(data[1], client)
            if not sclient:
                return
            if client.maxLevel <= sclient.maxLevel and client.maxLevel < 100:
                client.message('You can only change passwords of yourself or lower level players')
                return
        else:
            sclient = client

        sclient.password = hash_password(data[0])
        sclient.save()
        if client == sclient:
            client.message("Your new password has been saved")
        else:
            client.message("New password for %s saved" % sclient.name)