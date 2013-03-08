#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
# 2005/08/29 - 1.1.0 - ThorN
#   Converted to use new event handlers
# 2012/08/11 - 1.2 - Courgette
#   - Can define group for using the !spamins command different than mod_level
#   - Can define an alias for the !spamins command
#   - fix bug where the !spamins command would not accept uppercase argument
#   - refactor the plugin to allow game specific behavior to be injected at runtime
# 2012/08/11 - 1.3 - Courgette
#   - improve behavior when a spammer received a warning but continues to spam
# 2012/12/18 - 1.3.1 - Courgette
#   - fix regression that prevented the !spamins command to be registered since v1.2
#
from ConfigParser import NoOptionError
import b3, re
import b3.events
import b3.plugin

__author__  = 'ThorN, Courgette'
__version__ = '1.3.1'


class SpamcontrolPlugin(b3.plugin.Plugin):
    _maxSpamins = 10
    _modLevel = 20
    _falloffRate = 6.5

    # dict of <event type, func> that tell onEvent how to delegate event handling.
    # This mechanism allows game parsers to add behaviour for game specific events.
    eventHanlders = {}


    def onLoadConfig(self):
        try:
            self._maxSpamins = self.config.getint('settings', 'max_spamins')
            if self._maxSpamins < 0:
                self._maxSpamins = 0
        except (NoOptionError, ValueError), err:
            self._maxSpamins = 10
            self.warning("using default value %s for max_spamins. %s" % (self._maxSpamins, err))

        try:
            self._modLevel = self.console.getGroupLevel(self.config.get('settings', 'mod_level'))
        except (NoOptionError, KeyError), err:
            self.warning("using default value %s for mod_level. %s" % (self._modLevel, err))

        try:
            self._falloffRate = self.config.getfloat('settings', 'falloff_rate')
        except (NoOptionError, ValueError), err:
            self._falloffRate = 6.5
            self.warning("using default value %s for falloff_rate. %s" % (self._falloffRate, err))


    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_SAY)
        self.registerEvent(b3.events.EVT_CLIENT_TEAM_SAY)

        self.eventHanlders = {
            b3.events.EVT_CLIENT_SAY: self.onChat,
            b3.events.EVT_CLIENT_TEAM_SAY: self.onChat,
            }

        self._adminPlugin = self.console.getPlugin('admin')
        if self._adminPlugin:
            # register commands
            if 'commands' in self.config.sections():
                for cmd in self.config.options('commands'):
                    level = self.config.get('commands', cmd)
                    sp = cmd.split('-')
                    alias = None
                    if len(sp) == 2:
                        cmd, alias = sp

                    func = self.getCmd(cmd)
                    if func:
                        self._adminPlugin.registerCommand(self, cmd, level, func, alias)
                    else:
                        self.warning("cannot find command function for '%s'" % cmd)

    def getCmd(self, cmd):
        """ return the method for a given command  """
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
        return None

    def getTime(self):
        """ just to ease automated tests """
        return self.console.time()


    def cmd_spamins(self, data, client, cmd=None):
        """\
        [name] - display a spamins level
        """
        if data:
            sclient = self._adminPlugin.findClientPrompt(data, client)
        else:
            sclient = client

        if sclient:
            if sclient.maxLevel >= self._modLevel:
                cmd.sayLoudOrPM(client, '%s ^7is too cool to spam' % sclient.exactName)
            else:
                now = self.getTime()
                last_message_time = sclient.var(self, 'last_message_time', now).value
                gap = now - last_message_time

                maxspamins = spamins = sclient.var(self, 'spamins', 0).value
                spamins -= int(gap / self._falloffRate)

                if spamins < 1:
                    spamins = 0

                cmd.sayLoudOrPM(client, '%s ^7currently has %s spamins, peak was %s' % (sclient.exactName, spamins, maxspamins))


    def onEvent(self, event):
        if not event.client or event.client.maxLevel >= self._modLevel:
            return

        self.eventHanlders[event.type](event)


    def onChat(self, event):
        points = 0
        client = event.client
        text = event.data

        last_message = client.var(self, 'last_message').value

        color = re.match(r'\^[0-9]', event.data)
        if color and text == last_message:
            points += 5
        elif text == last_message:
            points += 3
        elif color:
            points += 2
        elif text.startswith('QUICKMESSAGE_'):
            points += 2
        else:
            points += 1

        if text[:1] == '!':
            points += 1

        self.add_spam_points(client, points, text)


    def add_spam_points(self, client, points, text):
        now = self.getTime()
        if client.var(self, 'ignore_till', now).value > now:
            #ignore the user
            raise b3.events.VetoEvent

        last_message_time = client.var(self, 'last_message_time', now).value
        gap = now - last_message_time

        if gap < 2:
            points += 1

        spamins = client.var(self, 'spamins', 0).value + points

        # apply natural points decrease due to time
        spamins -= int(gap / self._falloffRate)

        if spamins < 1:
            spamins = 0

        # set new values
        client.setvar(self, 'spamins', spamins)
        client.setvar(self, 'last_message_time', now)
        client.setvar(self, 'last_message', text)

        # should we warn ?
        if spamins >= self._maxSpamins:
            client.setvar(self, 'ignore_till', now + 2)
            self._adminPlugin.warnClient(client, 'spam')
            spamins = int(spamins / 1.5)
            client.setvar(self, 'spamins', spamins)
            raise b3.events.VetoEvent

