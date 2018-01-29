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

__author__ = 'ThorN'
__version__ = '1.3'

import b3
import b3.plugin
import b3.cron
import StringIO
import ftplib
import time

from b3 import functions
from b3.functions import getCmd
from ConfigParser import NoOptionError


class PunkbusterPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _cronTab = None
    _remoteBansFile = False
    _ftpConfig = None
    _bansFile = '~/cod/pb/pbbans.dat'
    _rebuildBans = '0 0 * * *'

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize the plugin.
        """
        self._adminPlugin = self.console.getPlugin('admin')

        if self.console.PunkBuster is None:
            self.warning('could not register commands because Punkbuster is disabled in your b3 configuration file')
            return False

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

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        try:
            self._bansFile = self.config.get('settings', 'bans_file')
            self.debug('loaded settings/bans_file: %s' % self._bansFile)
        except NoOptionError, e:
            self.error('could not load settings/bans_file config value: %s' % e)
            self.debug('using default value (%s) for settings/bans_file' % self._bansFile)

        if self._bansFile[0:6] == 'ftp://':
            self._remoteBansFile = True
            self._ftpConfig = functions.splitDSN(self._bansFile)
            self.info('accessing pbbans.dat file in remote mode')
        else:
            self._bansFile = self.console.getAbsolutePath(self._bansFile)

        try:
            self._rebuildBans = self.config.get('settings', 'rebuild_bans')
            self.debug('loaded settings/rebuild_bans: %s' % self._rebuildBans)
        except NoOptionError, e:
            self.error('could not load settings/rebuild_bans config value: %s' % e)
            self.debug('using default value (%s) for settings/rebuild_bans' % self._rebuildBans)

        if self._cronTab:
            # remove old crontab
            self.console.cron - self._cronTab

        if self._rebuildBans != '0':
            minute, hour, day, month, dow = self._rebuildBans.split(' ')
            self._cronTab = b3.cron.PluginCronTab(self, self.rebuild_bans, '0', minute, hour, day, month, dow)
            self.console.cron + self._cronTab

    ####################################################################################################################
    #                                                                                                                  #
    #    FUNCTIONS                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    def rebuild_bans(self):
        """
        Rebuild pbbans.dat from database
        """
        q = """SELECT DISTINCT(c.id), c.name, c.ip, c.pbid, p.time_add, p.reason
               FROM penalties p, clients c
               WHERE c.id = p.client_id && type = 'Ban' && p.inactive = 0 && p.time_expire = -1
               ORDER BY p.time_add"""

        cursor = self.console.storage.query(q)

        i = 0
        if self._remoteBansFile:
            f = StringIO.StringIO()
        else:
            f = file(self._bansFile, 'w')

        while not cursor.EOF:
            r = cursor.getRow()
            if r['reason'] != '':            
                f.write('[%s] %s "%s" "%s" %s" ""\r\n\r\n' % (time.strftime('%m.%d.%Y %H:%M:%S',
                                                              time.localtime(int(r['time_add']))),
                                                              r['pbid'], r['name'], r['ip'], r['reason']))
            else:
                f.write('[%s] %s "%s" "%s"\r\n\r\n' % (time.strftime('%m.%d.%Y %H:%M:%S',
                                                       time.localtime(int(r['time_add']))),
                                                       r['pbid'], r['name'], r['ip']))

            i += 1
            cursor.moveNext()

        cursor.close()

        if self._remoteBansFile:
            ftp = ftplib.FTP(self._ftpConfig['host'], self._ftpConfig['user'], self._ftpConfig['password'])
            f.seek(0)
            try:
                ftp.storbinary('STOR %s' % self._ftpConfig['path'], f)
            except Exception, err:
                self.error('ERROR: %s' % err)
            ftp.quit()
            self.debug('uploaded pbbans.dat to FTP server successfully')
        else:
            f.close()
            self.debug('updated pbbans.dat successfully')

        self.console.write('PB_SV_BanEmpty')
        self.console.write('PB_SV_BanLoad')

        return i

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_pbss(self, data, client=None, cmd=None):
        """
        <client> - capture a screenshot from the player
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Missing data, try !help pbss')
            return

        sclient = self._adminPlugin.findClientPrompt(m[0], client)
        if sclient:
            client.message('^3PunkBuster: ^7%s' % self.console.PunkBuster.getSs(sclient))

    def cmd_pbbuildbans(self, data, client=None, cmd=None):
        """\
        Rebuild punkbuster ban file
        """
        bans = self.rebuild_bans()
        client.message('^3PunkBuster: ^7rebuilt %s bans' % bans)