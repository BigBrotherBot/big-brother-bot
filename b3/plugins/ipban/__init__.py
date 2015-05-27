#
# IPban Plugin for BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2014 Mark Weirath (xlr8or@xlr8or.com)
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
# CHANGELOG
#
# 06-12-2014 : v1.0.0beta : xlr8or - irst edition of ipban
# 23-02-2015 : v1.1.0beta : Fenix  - added missing 'settings' section in plugin configuration file
#                                  - fixed plugin not correctly loading maxlevel property
#                                  - correctly return list of banned ips in getBanIps and getTempBanIps
#                                  - optimized SQL quieries and IP ban check workflow
#                                  - updated plugin module structure for easier install
#                                  - fixed usage of deprecated method startup()
# 26-03-2015 : v1.2.0beta : Fenix  - made IPban a built in plugin
#                                  - removed B3 1.9.x backwards compatibility

__version__ = '1.2.0beta'
__author__ = 'xlr8or'

import b3
import b3.events
import b3.lib
import b3.plugin

from time import time
from ConfigParser import NoOptionError


class IpbanPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _maxLevel = 1

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize plugin settings
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            raise AttributeError('could not find admin plugin')

        if self.console.isFrostbiteGame():
            # EVT_PUNKBUSTER_NEW_CONNECTION is raised when the parser fills in
            # the ip attribute on a already initialized Client object instance
            self.registerEvent('EVT_PUNKBUSTER_NEW_CONNECTION', self.onPlayerConnect)
        else:
            # don't use EVT_CLIENT_CONNECT since we need the client group for level exclusion
            self.registerEvent('EVT_CLIENT_AUTH', self.onPlayerConnect)

        self.debug('banned ips: %s' % self.getBanIps())
        self.debug('banned ips: %s' % self.getTempBanIps())
        self.debug('plugin started')

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        try:
            self._maxLevel = self.console.getGroupLevel(self.config.get('settings', 'maxlevel'))
        except (NoOptionError, KeyError), err:
            self.error(err)
        self.debug('maximum level affected: %s' % self._maxLevel)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onPlayerConnect(self, event):
        """
        Examine players ip address and allow/deny connection.
        """
        client = event.client
        # check the level of the connecting client before applying the filters
        if client.maxLevel > self._maxLevel:
            self.debug('%s is a higher level user and allowed to connect' % client.name)
        else:
            self.debug('checking player: <cid:%s,name:%s,ip:%s>' % (client.cid, client.name, client.ip))
            # check for active bans and tempbans
            if client.ip in self.getBanIps():
                self.debug('client refused: <cid:%s,name:%s,ip:%s>' % (client.cid, client.name, client.ip))
                client.kick('Netblocker: client refused: %s (%s) has an active Ban' % (client.ip, client.name))
            elif client.ip in self.getTempBanIps():
                self.debug('client refused: <cid:%s,name:%s,ip:%s>' % (client.cid, client.name, client.ip))
                client.kick('Netblocker: client refused: %s (%s) has an active TempBan' % (client.ip, client.name))
            else:
                self.debug('client accepted (no active Ban/TempBan found): <cid:%s,name:%s,ip:%s>' % (client.cid, client.name, client.ip))

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def getBanIps(self):
        """
        Returns a list of banned IPs
        """
        banned = []
        cursor = self.console.storage.query("SELECT clients.ip AS target_ip FROM penalties INNER JOIN clients ON "
                                            "penalties.client_id = clients.id WHERE penalties.type = 'Ban' AND "
                                            "penalties.inactive = 0 AND penalties.time_expire = -1 GROUP BY clients.ip")
        if cursor:
            while not cursor.EOF:
                banned.append(cursor.getValue('target_ip'))
                cursor.moveNext()
        cursor.close()
        return banned

    def getTempBanIps(self):
        """
        Returns a list of TempBanned IPs
        """
        banned = []
        cursor = self.console.storage.query("SELECT clients.ip AS target_ip FROM penalties INNER JOIN clients ON "
                                            "penalties.client_id = clients.id WHERE penalties.type = 'TempBan' AND "
                                            "penalties.inactive = 0 AND penalties.time_expire > %s "
                                            "GROUP BY clients.ip" % int(time()))
        if cursor:
            while not cursor.EOF:
                banned.append(cursor.getValue('target_ip'))
                cursor.moveNext()
        cursor.close()
        return banned

if __name__ == '__main__':
    print '\nThis is version ' + __version__ + ' by ' + __author__ + ' for BigBrotherBot.\n'