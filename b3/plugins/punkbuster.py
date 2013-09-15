#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
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
# 19/07/2011 - 1.1.0 - Freelander
#    Support for ftp access to pbbans.dat
# 27/08/2009 - 1.0.9 - Bakes
#    Use command levels set in punkbuster plugin config not admin plugin.
# 11/30/2005 - 1.0.8 - ThorN
#    Use PluginCronTab instead of CronTab

__author__  = 'ThorN'
__version__ = '1.1.0'

import b3, time
import b3.plugin
import b3.cron
from b3 import functions
import StringIO
import ftplib

#--------------------------------------------------------------------------------------------------
class PunkbusterPlugin(b3.plugin.Plugin):
    _cronTab = None
    _rebuildBans = 0
    _remoteBansFile = False
    _ftpConfig = None

    def onStartup(self):
        self._adminPlugin = self.console.getPlugin('admin')
    
        if self._adminPlugin:
            
            if self.console.PunkBuster is None:
                self.warning('Could not register commands because Punkbuster is disabled in your b3.xml configuration file')
                return
            
            self._adminPlugin.registerCommand(self, 'pbss', self.config.getint('commands', 'pbss'), self.cmd_pbss)
            self._adminPlugin.registerCommand(self, 'pbbuildbans', self.config.getint('commands', 'pbbuildbans'), self.cmd_pbbuildbans)

    def onLoadConfig(self):
        if self.config.get('settings','bans_file')[0:6] == 'ftp://':
            self._bansFile = self.config.get('settings','bans_file')
            self._remoteBansFile = True
            self._ftpConfig = functions.splitDSN(self._bansFile)
            self.info('Accessing pbbans.dat file in remote mode')
        else:
            self._bansFile = self.console.getAbsolutePath(self.config.get('settings', 'bans_file'))


        self._rebuildBans = self.config.get('settings', 'rebuild_bans')

        if self._cronTab:
            # remove old crontab
            self.console.cron - self._cronTab

        if self._rebuildBans == '0' or self._rebuildBans == 0:
            self._rebuildBans = 0
        else:
            minute, hour, day, month, dow = self._rebuildBans.split(' ')
            self._cronTab = b3.cron.PluginCronTab(self, self.rebuildBans, '0', minute, hour, day, month, dow)
            self.console.cron + self._cronTab

    def rebuildBans(self):
        """\
        Rebuild pbbans.dat from database
        """
        cursor = self.console.storage.query("""\
SELECT DISTINCT(c.id), c.name, c.ip, c.pbid, p.time_add, p.reason FROM penalties p, clients c
WHERE c.id = p.client_id && type = 'Ban' && p.inactive = 0 && 
p.time_expire = -1
ORDER BY p.time_add""")

        i = 0
        if self._remoteBansFile:
            f = StringIO.StringIO()
        else:
            f = file(self._bansFile , 'w')

        while not cursor.EOF:
            r = cursor.getRow()

            if r['reason'] != '':            
                f.write('[%s] %s "%s" "%s" %s" ""\r\n\r\n' % (time.strftime('%m.%d.%Y %H:%M:%S', time.localtime(int(r['time_add']))), r['pbid'], r['name'], r['ip'], r['reason']))
            else:
                f.write('[%s] %s "%s" "%s"\r\n\r\n' % (time.strftime('%m.%d.%Y %H:%M:%S', time.localtime(int(r['time_add']))), r['pbid'], r['name'], r['ip']))

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
            self.debug('Uploaded pbbans.dat to FTP server successfully.')
        else:
            f.close()
            self.debug('Updated pbbans.dat successfully.')

        self.console.write('PB_SV_BanEmpty')
        self.console.write('PB_SV_BanLoad')

        return i

    def cmd_pbss(self, data, client=None, cmd=None):
        """\
        <player> - Capture a screenshot from the player
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters, you must supply a player name')
            return False

        sclient = self._adminPlugin.findClientPrompt(m[0], client)
        if sclient:
            client.message('^3PunkBuster: ^7 %s' % self.console.PunkBuster.getSs(sclient))

    def cmd_pbbuildbans(self, data, client=None, cmd=None):
        """\
        Rebuild punkbuster ban file
        """
        bans = self.rebuildBans()
        client.message('^3PunkBuster: ^7 rebuilt %s bans' % bans)
