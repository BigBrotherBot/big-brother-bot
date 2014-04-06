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
#    04/23/2010 - 1.2.2 - Bakes
#       Fix to !ci after bug reported by sgt
#    03/28/2010 - 1.2.1 - xlr8or
#       Add default _minLevel for !ci if config option is missing
#    03/21/2010 - 1.2.0 - Bakes
#       Added the !ci command from the admin plugin.
#    11/30/2005 - 1.1.3 - ThorN
#       Use PluginCronTab instead of CronTab
#    8/29/2005 - 1.1.0 - ThorN
#       Converted to use new event handlers

__author__ = 'ThorN'
__version__ = '1.2.2'


import b3
import b3.events
import b3.plugin
import b3.cron
from ConfigParser import NoOptionError


class PingwatchPlugin(b3.plugin.Plugin):
    _interval = 0
    _maxPing = 0
    _maxPingDuration = 0
    _ignoreTill = 0
    _cronTab = None
    _maxCiPing = 500
    _minLevel = 20

    def onStartup(self):
        """\
        Initialize plugin
        """
        self.registerEvent(self.console.getEventID('EVT_GAME_EXIT'), self.onGameExit)
        self._ignoreTill = self.console.time() + 120  # dont check pings on startup

    def onLoadConfig(self):
        """\
        Load plugin configuration
        """
        try:
            self._minLevel = self.config.get('commands', 'ci')
        except NoOptionError:
            pass 

        self._interval = self.config.getint('settings', 'interval')
        self._maxPing = self.config.getint('settings', 'max_ping')
        self._maxPingDuration = self.config.getint('settings', 'max_ping_duration')

        if self._cronTab:
            # remove existing crontab
            self.console.cron - self._cronTab

        self._cronTab = b3.cron.PluginCronTab(self, self.check, '*/%s' % self._interval)
        self.console.cron + self._cronTab
        self._adminPlugin = self.console.getPlugin('admin')
        self._adminPlugin.registerCommand(self, 'ci', self._minLevel, self.cmd_ci)

    def onGameExit(self, event):
        """\
        Handle intercepted events
        """
        # ignore ping watching for 2 minutes
        self._ignoreTill = self.console.time() + 120

    def check(self):
        """\
        Check for clients with high ping
        """
        if not self.isEnabled() or self.console.time() <= self._ignoreTill:
            # we are not supposed to check
            return

        for cid, ping in self.console.getPlayerPings().items():
            # loop through all the connected clients
            # self.console.verbose('ping %s = %s', cid, ping)
            if ping <= self._maxPing:
                continue

            client = self.console.clients.getByCID(cid)
            if not client:
                continue

            if not client.isvar(self, 'highping'):
                self.console.verbose('set ping watch %s = %s', cid, ping)
                client.setvar(self, 'highping', self.console.time())
                return

            self.console.verbose('set high ping check %s = %s (%s)', cid, ping, client.var(self, 'highping', 0).value)
            if self.console.time() - client.var(self, 'highping', 0).value > self._maxPingDuration:
                if ping == 999:
                    self.console.say('^7%s ^7ping detected as Connection Interrupted (CI)' % client.name)
                else:
                    self.console.say('^7%s ^7ping detected as too high %s' % (client.name, ping))

    def cmd_ci(self, data, client=None, cmd=None):
        """\
        <client> - Kick a client that has an interrupted connection
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Missing data, try !help ci')
            return False

        sclient = self._adminPlugin.findClientPrompt(m[0], client)
        if not sclient:
            return

        try:
            players = self.console.getPlayerPings()
            ping = players[str(sclient.cid)]
            if ping > self._maxCiPing:
                sclient.kick(self._adminPlugin.getReason('ci'), 'ci', client)
            else:
                client.message('^7%s ^7is not CI' % sclient.exactName)
        except KeyError:
            pass