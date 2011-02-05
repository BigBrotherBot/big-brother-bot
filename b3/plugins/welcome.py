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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# 2010/10/17 - 1.2 - Courgette
#  * add min_gap to customize how long the bot must wait before welcoming a 
#    player again (in seconds)
#  * add tests
# 2010/03/21 - 1.1 - Courgette
#    import cmd_greeting from the admin plugin 
# 3/4/2009 - 1.0.6 - xlr8or
#    Added welcome delay setting to config
# 3/3/2009 - 1.0.5 - xlr8or
#    Fixed another error that caused an exception on new users
# 2/28/2009 - 1.0.4 - xlr8or
#    Removed error generated in welcoming thread on first time players
# 2/26/2009 - 1.0.3 - xlr8or
#    Do not welcome players that where already welcomed in the last hour

__version__ = '1.1'
__author__    = 'ThorN'

import b3, threading, time, re
import b3.events
import b3.plugin

#--------------------------------------------------------------------------------------------------
class WelcomePlugin(b3.plugin.Plugin):
    _newbConnections = 0
    _welcomeFlags = 0
    _welcomeDelay = 0
    _cmd_greeting_minlevel = None
    _min_gap = 3600

    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)

    def onLoadConfig(self):
        try:
            self._cmd_greeting_minlevel = self.config.getint('commands', 'greeting')
        except:
            self._cmd_greeting_minlevel = 20
            self.warning('using default value %s for command !greeting' % self._cmd_greeting_minlevel)
        
        self._adminPlugin = self.console.getPlugin('admin')
        if self._adminPlugin:
            self._adminPlugin.registerCommand(self, 'greeting', self._cmd_greeting_minlevel, self.cmd_greeting)
            
        self._welcomeFlags = self.config.getint('settings', 'flags')
        self._newbConnections = self.config.getint('settings', 'newb_connections')
        try:
            self._welcomeDelay = self.config.getint('settings', 'delay')
            if self._welcomeDelay < 15 or self._welcomeDelay > 90:
                self._welcomeDelay = 30
                self.debug('Welcome delay not in range 15-90 using 30 instead.')
            self.info('delay set to %s. The bot will wait %ss after a player connects to write the welcome message' % (self._welcomeDelay, self._welcomeDelay))
        except:
            self._welcomeDelay = 30

        try:
            self._min_gap = self.config.getint('settings', 'min_gap')
            if self._min_gap < 0:
                self._min_gap = 0
            self.info('min_gap set to %s. The bot will not welcome a player more than once every %s seconds' % (self._min_gap, self._min_gap))
        except:
            self._min_gap = 3600
            self.warning('error while reading min_gap from config. min_gap set to %s (default).' % (self._min_gap))
            

    def cmd_greeting(self, data, client, cmd=None):
        """\
        [<greeting>] - set or list your greeting (use 'none' to remove)
        """
        if data.lower() == 'none':
            client.greeting = ''
            client.save()
            client.message(self.getMessage('greeting_cleared'))
        elif data:
            data = re.sub(r'\$([a-z]+)', r'%(\1)s', data)

            if len(data) > 255:
                client.message('^7Your greeting is too long')
            else:
                try:
                    client.message('Greeting Test: %s' % (str(data) %
                        {'name' : client.exactName, 'greeting' : client.greeting, 'maxLevel' : client.maxLevel, 'group' : getattr(client.maxGroup, 'name', None), 'connections' : client.connections}))
                except ValueError, msg:
                    client.message(self.getMessage('greeting_bad', msg))
                    return False
                else:
                    client.greeting = data
                    client.save()
                    client.message(self.getMessage('greeting_changed', client.greeting))
                    return True
        else:
            if client.greeting:
                client.message(self.getMessage('greeting_yours', client.greeting))
            else:
                client.message(self.getMessage('greeting_empty'))

    def onEvent(self, event):
        if event.type == b3.events.EVT_CLIENT_AUTH:
            if    self._welcomeFlags < 1 or \
                not event.client or \
                event.client.id == None or \
                event.client.cid == None or \
                not event.client.connected or \
                event.client.pbid == 'WORLD':
                return
            if self.console.upTime() < 300:
                self.debug('not welcoming player because the bot started less than 5 min ago')
                return
            t = threading.Timer(self._welcomeDelay, self.welcome, (event.client,))
            t.start()

    def welcome(self, client):
        _timeDiff = 0
        if client.lastVisit:
            self.debug('LastVisit: %s' %(self.console.formatTime(client.lastVisit)))
            _timeDiff = time.time() - client.lastVisit
        else:
            self.debug('LastVisit not available. Must be the first time.')
            _timeDiff = 1000000 # big enough so it will welcome new players

        # don't need to welcome people who got kicked or where already 
        # welcomed in before _min_gap s ago
        if client.connected and _timeDiff > self._min_gap:
            info = {
                'name'    : client.exactName,
                'id'    : str(client.id),
                'connections' : str(client.connections)
            }

            if client.maskedGroup:
                info['group'] = client.maskedGroup.name
                info['level'] = str(client.maskedGroup.level)
            else:
                info['group'] = 'None'
                info['level'] = '0'

            if client.connections >= 2:
                #info['lastVisit'] = self.console.formatTime(client.timeEdit)
                info['lastVisit'] = self.console.formatTime(client.lastVisit)
            else:
                info['lastVisit'] = 'Unknown'

            if client.connections >= 2:
                if client.maskedGroup:
                    if self._welcomeFlags & 16:
                        client.message(self.getMessage('user', info))
                elif self._welcomeFlags & 1:
                    client.message(self.getMessage('newb', info))

                if self._welcomeFlags & 2 and client.connections < self._newbConnections:
                    self.console.say(self.getMessage('announce_user', info))
            else:
                if self._welcomeFlags & 4:
                    client.message(self.getMessage('first', info))
                if self._welcomeFlags & 8:
                    self.console.say(self.getMessage('announce_first', info))

            if self._welcomeFlags & 32 and client.greeting:
                info['greeting'] = client.greeting % info
                self.console.say(self.getMessage('greeting', info))
        else:
            if _timeDiff <= self._min_gap:
                self.debug('Client already welcomed in the past %s seconds' % self._min_gap)



if __name__ == '__main__':
    from b3.fake import fakeConsole
    from b3.fake import joe
    from b3.config import XmlConfigParser
    
    conf = XmlConfigParser()
    conf.setXml("""
<configuration plugin="welcome">
    <settings name="commands">
        <set name="greeting">20</set>
    </settings>
    <settings name="settings">
        <!--
        who to welcome
        1 = welcome newb
        2 = welcome announce_user
        4 = welcome first
        8 = welcome announce_first
        16 = welcome user
        32 = custom greetings
        add numbers, 63 = all
        -->
        <set name="flags">63</set>
        <!-- Maximum number of connections a user has to be considere a newb for the newb message -->
        <set name="newb_connections">15</set>
    <!-- Time in seconds after connection to display the message (range: 15-90) -->
    <set name="delay">15</set>
    <!-- Time in seconds the bot must wait before welcoming a player again. 
      i.e.: if you set min_gap to 3600 seconds (one hour) then the bot will not
      welcome a player more than once per hour
    -->
    <set name="min_gap">6</set>
    </settings>
    <settings name="messages">
        <!--
        Welcome messages
        $name = player name
        $id = player id
        $lastVisit = last visit time (only on welcome_user and welcome_newb)
        $group = players group (only on welcome_user)
        $connections = number of times a user has connected (only on welcome_user and welcome_announce_user)
        -->
        <!-- displayed to admins and regs -->
        <set name="user">^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit^7, you're a ^2$group^7, played $connections times</set>
        <!-- displayed to users who have not yet registered -->
        <set name="newb">^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit. Type !register in chat to register. Type !help for help</set>
        <!-- displayed to everyone when a player with less than 15 connections joins -->
        <set name="announce_user">^7Everyone welcome back $name^7, player number ^3#$id^7, to the server, played $connections times</set>
        <!-- displayed to a user on his first connection -->
        <set name="first">^7Welcome $name^7, this must be your first visit, you are player ^3#$id. Type !help for help</set>
        <!-- displayed to everyone when a player joins for the first time -->
        <set name="announce_first">^7Everyone welcome $name^7, player number ^3#$id^7, to the server</set>
        <!-- displayed if a user has a greeting -->
        <set name="greeting">^7$name^7 joined: $greeting</set>

        <!-- command answers : -->
        <set name="greeting_empty">^7You have no greeting set</set>
        <set name="greeting_yours">^7Your greeting is %s</set>
        <set name="greeting_bad">^7Greeting is not formated properly: %s</set>
        <set name="greeting_changed">^7Greeting changed to: %s</set>
        <set name="greeting_cleared">^7Greeting cleared</set>
    </settings>
</configuration>
    """)

    ## trick the console in thinking it was started an hour ago
    def myUpTime_func():
        return 3600
    fakeConsole.upTime = myUpTime_func
    
    p = WelcomePlugin(fakeConsole, conf)
    p.onStartup()
    # override _welcomeDelay which makes testing a pain
    p._welcomeDelay = 1
    
    print "--------------------------------"
    joe.connects(0)
    time.sleep(2)

    joe.disconnects()
    joe.connected = True
    joe.connects(2)
    time.sleep(8)

    joe.disconnects()
    joe.connected = True
    joe.connects(4)
    time.sleep(5)

    time.sleep(60)
