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

__version__ = '2.1'
__author__  = 'Ismael, SGT, Fenix'

import b3
import b3.config
import b3.cron
import b3.functions
import b3.plugin
import os
import thread

from b3.functions import clamp

class NickregPlugin(b3.plugin.Plugin):

    adminPlugin = None
    crontab = None
    ignore_till = 0

    interval = 30
    min_level = 20
    min_level_global_manage = 100
    max_nicks = 3

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        self.min_level = self.getSetting('settings', 'min_level', b3.LEVEL, 20)
        self.min_level_global_manage = self.getSetting('settings', 'min_level_global_manage', b3.LEVEL, 100, lambda x: clamp(x, minv=self.min_level))
        self.max_nicks = self.getSetting('settings', 'max_nicks', b3.INTEGER, 3)
        self.interval = self.getSetting('settings', 'interval', b3.INTEGER, 30)

    def onStartup(self):
        """
        Initialize plugin settings
        """
        self.adminPlugin = self.console.getPlugin('admin')
        if not self.adminPlugin:
            raise AttributeError('could not find admin plugin')

        # create database tables (if needed)
        if 'nicks' not in self.console.storage.getTables():
            sql_path_main = b3.getAbsolutePath('@b3/plugins/nickreg/sql')
            sql_path = os.path.join(sql_path_main, self.console.storage.dsnDict['protocol'], 'nickreg.sql')
            self.console.storage.queryFromFile(sql_path)

        # register our commands
        self.adminPlugin.registerCommand(self, 'registernick', self.min_level, self.cmd_regnick,  'regnick')
        self.adminPlugin.registerCommand(self, 'deletenick', self.min_level, self.cmd_delnick,  'delnick')
        self.adminPlugin.registerCommand(self, 'listnick', self.min_level, self.cmd_listnick)

        # register our events
        self.registerEvent('EVT_CLIENT_NAME_CHANGE', self.on_client_name_change)
        self.registerEvent('EVT_GAME_MAP_CHANGE', self.on_map_change)

        # install crontab
        self.crontab = b3.cron.PluginCronTab(self, self.execute_crontab, '*/%s' % self.interval)
        self.console.cron + self.crontab

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def on_map_change(self, _):
        """
        Handle EVT_GAME_MAP_CHANGE
        """
        # on a new map wait skip the first self.interval seconds of name checks
        self.ignore_till = self.console.time() + self.interval

    def on_client_name_change(self,  event):
        """
        Handle EVT_CLIENT_NAME_CHANGE.
        """
        thread.start_new_thread(self.check_client_for_nick_steal, (event.client,))

    ####################################################################################################################
    #                                                                                                                  #
    #    CRON                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def execute_crontab(self):
        """
        Check if connected clients are stealing a nickname.
        """
        if self.console.time() >= self.ignore_till:
            for client in self.console.clients.getList():
                if client.maxLevel == 100:
                    self.debug('not checking %s(@%s) for nickname stealing: he is a superadmin', client.name, client.id)
                    continue
                # make sure not to check clients too soon (add an extra second to the interval time
                # to make sure not to match equal values which will result in no nickname check at all.
                if client.isvar(self, 'nick_check_time'):
                    last_nick_check_delta = self.console.time() - client.var(self, 'nick_check_time').value
                    if last_nick_check_delta < self.interval + 1:
                        self.debug('not checking %s(@%s) for nickname stealing: '
                                   'last check run %ss ago', client.name, client.id, last_nick_check_delta)
                    continue
                # run the nickname check for this client
                self.check_client_for_nick_steal(client)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def _process_name(self, name):
        """
        Normalize the given name by removing color codes, leading/trailing spaces,
        escaping single quotes and making it lowercase.
        :param name: the name to normalize
        """
        return b3.functions.escape(self.console.stripColors(name).lower(), "'")

    def warn_client_for_nick_steal(self, client):
        """
        Warn a client for nickname stealing.
        :param client: the client to warn.
        """
        self.adminPlugin.warnClient(client, 'You are using a registered nickname, please change it!', None, False, '', '10m')

    def check_client_for_nick_steal(self, client):
        """
        Check if the given client is stealing a nickname.
        :param client: the client whose nickname we want to check.
        """
        if client and client.id and client.pbid not in ('WORLD', 'Server'):

            self.debug('checking if client @%s is using a registered nickname (%s)', client.id, client.name)
            cursor = self.console.storage.query("""SELECT * FROM nicks WHERE name LIKE '%s'""" % self._process_name(client.name))
            if cursor.EOF:
                self.debug('nickname "%s" does not seem to be registered: client @%s is legit', client.name, client.id)
            else:
                row = cursor.getRow()
                if int(row['client_id']) != int(client.id):
                    self.debug('warning client @%s for nickname stealing (%s): owner is client @%s', client.id, client.name, row['client_id'])
                    self.warn_client_for_nick_steal(client)
                else:
                    self.debug('client @%s is the owner of registered nickname (%s): everything ok', client.id, client.name)

                cursor.close()

            client.setvar(self, 'nick_check_time', self.console.time())

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################
                            
    def cmd_listnick(self, data, client, cmd=None):
        """
        [<client>] - list registered nicknames
        """
        if not data:
            sclient = client
        else:
            sclient = self.adminPlugin.findClientPrompt(data, client)
            if not sclient:
                return

        if sclient.id != client.id and (client.maxLevel < self.min_level_global_manage or sclient.maxLevel > client.maxLevel):
            client.message("^7You can't see ^1%s ^7registered nicknames!" % sclient.name)
            return

        cursor = self.console.storage.query("""SELECT * FROM nicks WHERE client_id = %s""" % sclient.id)
        if cursor.EOF:
            cmd.sayLoudOrPM(client, '^7%s ^7has no registered nickname' % sclient.name)
            cursor.close()
        else:
            registered = []
            while not cursor.EOF:
                row = cursor.getRow()
                registered.append('^7[^1%s^7] ^3%s' % (row['id'], row['name']))
                cursor.moveNext()
            cmd.sayLoudOrPM(client, '^7%s ^7has registered nickname(s): %s' % (sclient.name, ', '.join(registered)))
            cursor.close()
        
    def cmd_regnick(self, data, client, cmd=None):
        """
        - register current name as yours
        """
        cursor = self.console.storage.query("""SELECT * FROM nicks WHERE name LIKE '%s'""" % self._process_name(client.name))
        if not cursor.EOF:
            client.message('^7Nick ^1%s ^7is already registered' % client.name)
            cursor.close()
            return

        cursor.close()
        cursor = self.console.storage.query("""SELECT COUNT(*) AS num_registered FROM nicks WHERE client_id = %s""" % client.id)
        num_registered = cursor.getValue('num_registered', 0)
        if num_registered >= self.max_nicks:
            client.message('^7You already have ^1%s ^7registered nicknames' % self.max_nicks)
            cursor.close()
            return

        cursor.close()
        self.console.storage.query("""INSERT INTO nicks (client_id, name) VALUES ('%s', '%s')""" % (client.id, self._process_name(client.name)))
        client.message('^7Your nick is now registered')

    def cmd_delnick(self,  data,  client,  cmd=None):
        """
        <id> - delete selected nick
        """
        if not data:
            client.message('^7Missing data, try !help deletenick')
            return

        if not data.isdigit():
            client.message('^7Invalid data, try !help deletenick')
            return

        cursor = self.console.storage.query("""SELECT * FROM nicks WHERE id = %s""" % data)
        if cursor.EOF:
            client.message('^7Invalid nick id supplied: ^1%s' % data)
            cursor.close()
            return

        row = cursor.getOneRow()
        sclient = self.adminPlugin.findClientPrompt('@%s' % row['client_id'])
        if sclient:
            # if there is no client matching the id of the client who this nick belongs to just keep going:
            # clients are never deleted but it may happen that the user delete the entry manually
            if sclient.id != client.id and (client.maxLevel < self.min_level_global_manage or sclient.maxLevel > client.maxLevel):
                client.message("^7You can't delete ^1%s ^7registered nicknames!" % sclient.name)
                return

        # proceed with the removal
        self.console.storage.query("""DELETE FROM nicks WHERE id = %s""" % data)
        client.message("^7Deleted nick: ^1%s" % row['name'])