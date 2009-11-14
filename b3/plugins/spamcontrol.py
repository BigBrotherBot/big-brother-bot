#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
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
#    8/29/2005 - 1.1.0 - ThorN
#    Converted to use new event handlers

__author__  = 'ThorN'
__version__ = '1.1.2'



import b3, re, time
import b3.events
import b3.plugin

#--------------------------------------------------------------------------------------------------
class SpamcontrolPlugin(b3.plugin.Plugin):
    _maxSpamins = 10
    _modLevel = 20
    _falloffRate = 6.5

    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_SAY)
        self.registerEvent(b3.events.EVT_CLIENT_TEAM_SAY)

        self._adminPlugin = self.console.getPlugin('admin')
        if self._adminPlugin:
            self._adminPlugin.registerCommand(self, 'spamins', self._modLevel, self.cmd_spamins)

    def onLoadConfig(self):
        self._maxSpamins = self.config.getint('settings', 'max_spamins')
        self._modLevel = self.config.getint('settings', 'mod_level')
        self._falloffRate = self.config.getfloat('settings', 'falloff_rate')

    def cmd_spamins(self, data, client, cmd=None):
        """\
        <name> - display a spamins level
        """
        m = re.match('^([a-z0-9]+)$', data)
        if not m:
            client.message('^7Invalid parameters')
            return

        sclient = self._adminPlugin.findClientPrompt(data, client)

        if sclient:
            if sclient.maxLevel >= self._modLevel:
                cmd.sayLoudOrPM(client, '%s ^7is too cool to spam' % sclient.exactName)
            else:
                last_message_time = sclient.var(self, 'last_message_time', self.console.time()).value
                gap                  = (self.console.time() - last_message_time)

                maxspamins = spamins = sclient.var(self, 'spamins', 0).value
                spamins -= int(gap / self._falloffRate)

                if spamins < 1:
                    spamins = 0

                cmd.sayLoudOrPM(client, '%s ^7currently has %s spamins, peak was %s' % (sclient.exactName, spamins, maxspamins))

    def onEvent(self, event):
        if not event.client or event.client.maxLevel >= self._modLevel:
            return

        last_message_time = event.client.var(self, 'last_message_time', self.console.time()).value
        last_message      = event.client.var(self, 'last_message').value
        spamins           = event.client.var(self, 'spamins', 0).value
        gap                  = (self.console.time() - last_message_time)

        color = re.match(r'\^[0-9]', event.data)

        if color and event.data == last_message:
            spamins += 5
        elif event.data == last_message:
            spamins += 3
        elif color:
            spamins += 2
        elif len(event.data) > 13 and event.data[:13] == 'QUICKMESSAGE_':
            spamins += 2
        else:
            spamins += 1

        if gap < 2:
            spamins += 1

        if len(event.data) and event.data[:1] == '!':
            spamins += 1

        spamins -= int(gap / self._falloffRate)
        if spamins < 1:
            spamins = 0

        event.client.setvar(self, 'spamins', spamins)
        event.client.setvar(self, 'last_message_time', self.console.time())
        event.client.setvar(self, 'last_message', event.data)

        if spamins >= self._maxSpamins:
            event.client.setvar(self, 'ignore_till', self.console.time() + 30)
            self._adminPlugin.warnClient(event.client, 'spam')
            spamins = int(spamins / 1.5)
            event.client.setvar(self, 'spamins', spamins)
            raise b3.events.VetoEvent
        elif event.client.var(self, 'ignore_till').value > self.console.time():
            #ignore the user
            raise b3.events.VetoEvent


if __name__ == '__main__':
    from b3.fake import fakeConsole
    from b3.fake import joe

    p = SpamcontrolPlugin(fakeConsole, '@b3/conf/plugin_spamcontrol.xml')
    p.onStartup()
    
    p.info("---------- start spamming")
    joe.says("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says2team("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says2team("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says("i'm spammmmmmmmmming")
    p.info("_________ end of test ____________")
    time.sleep(1) # give console thread a chance to end gracefully 
