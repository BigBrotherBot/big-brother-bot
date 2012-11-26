#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Plugin for extra authentication of privileged users
# Copyright (C) 2005 Tim ter Laak (ttlogic@xlr8or.com)
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
# 1.0.1 - 23/08/2009 - Courgette
#     * fix indentation problem
# 1.0.2 - 28/08/2009 - xlr8or
#     * minor update
# 1.0.3 - 17/04/2010 - Bakes
#     * use hashlib if available instead of the deprecated md5
# 1.1 - 25/11/2012 - Courgette
#     * always read password from database to prevent security issues arising from bugged b3 game parsers
#
import string
from b3.clients import Client
import b3.events
import b3.plugin
from b3.functions import hash_password

__author__    = 'Tim ter Laak'
__version__ = '1.1'


class LoginPlugin(b3.plugin.Plugin):

    _pmcomm = ''

    def onLoadConfig(self):
        try:
            self.threshold = self.config.getint('settings', 'thresholdlevel') 
        except:
            self.threshold = 1000
            self.debug('Using default value (%i) for settings::thresholdlevel', self.threshold)
        try:
            self.passwdlevel = self.config.getint('settings', 'passwdlevel') 
        except:
            self.passwdlevel = 100
            self.debug('Using default value (%i) for settings::passwdlevel', self.passwdlevel)
        return


    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)
        self._adminPlugin = self.console.getPlugin('admin')
        if self._adminPlugin:
            self._adminPlugin.registerCommand(self, 'login', 2, self.cmd_login, secretLevel=1)
            self._adminPlugin.registerCommand(self, 'setpassword', self.passwdlevel, self.cmd_setpassword)

        # Whats the command to send a private message?
        if self.console.gameName[:5] == 'etpro':
            self._pmcomm = '/m'
        else:
            self._pmcomm = '/tell'
        self.debug('Using "%s" as the private messaging command' %self._pmcomm)


    def onEvent(self, event):
        if event.type == b3.events.EVT_CLIENT_AUTH:
            self.onAuth(event.client)
        else:
            self.debug('login.dumpEvent -- Type %s, Client %s, Target %s, Data %s', event.type, event.client, event.target, event.data)

    def onAuth(self, client):
        if client.maxLevel > self.threshold and not client.isvar(self, 'loggedin'):

            client_from_db = self._get_client_from_db(client.id)

            #save original groupbits
            client.setvar(self, 'login_groupbits', client_from_db.groupBits)

            #set new groupBits
            try:
                g = self.console.storage.getGroup('reg')
                client.groupBits = g.id
            except:
                client.groupBits = 2

            if not client_from_db.password:
                client.message('You need a password to use all your privileges. Ask the administrator to set a password for you.')
                return
            else:
                message = 'Login via console: %s %s !login yourpassword' %(self._pmcomm, client.cid)
                client.message(message)
                return

    def cmd_login(self, data, client, cmd=None):
        """\
        <password> - login a privileged user to his full capabilities
        """
        if client.isvar(self, 'loggedin'):
            client.message('You are already logged in.')
            return

        if not client.isvar(self, 'login_groupbits'):
            client.message('You do not need to log in.')
            return

        if data:
            digest = hash_password(data)
            client_from_db = self._get_client_from_db(client.id)
            if digest == client_from_db.password:
                client.setvar(self, 'loggedin', 1)
                client.groupBits = client.var(self, 'login_groupbits').value
                client.message('You are successfully logged in.')
                return
            else:
                client.message('^1***Access denied***^7')
                return
        else:
            message = 'Usage (via console): %s %s !login yourpassword' %(self._pmcomm, client.cid)
            client.message(message)
            return
        
    def cmd_setpassword(self, data, client, cmd=None):
        """\
        <password> [<name>] - set a password for a client
        """
        if not data:
            client.message('usage: %s%s <new password> [name]' % (cmd.prefix, cmd.command))
            return

        data = string.split(data)
        if len(data) > 1:
            sclient = self._adminPlugin.findClientPrompt(data[1], client)
            if not sclient: return        
            if client.maxLevel <= sclient.maxLevel and client.maxLevel < 100:
                client.message('You can only change passwords of yourself or lower level players.')
                return
        else:
            sclient = client

        sclient.password = hash_password(data[0])
        sclient.save()
        if client == sclient:
            client.message("your new password is saved")
        else:
            client.message("new password for %s saved" % sclient.name)


    def _get_client_from_db(self, client_id):
        return self.console.storage.getClient(Client(id=client_id))
