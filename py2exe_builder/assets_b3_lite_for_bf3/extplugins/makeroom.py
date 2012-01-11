#
# Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette
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
# Changelog:
#
# 2011-05-12 - 1.1
# * messages can be customized in the plugin config file
# 2011-05-29 - 1.1.1
# * fix saving the kick into database
# 2011-06-08 - 1.2
# * add info message and delay between info message and actual kick
# 2011-06-20 - 1.3
# * add an automation feature to keep some free slot
# 2011-07-09 - 1.3.1
# * fix issue in automation mode where the last player to connect
#   would not be kicked if his level is equals to the non_member_level 
# 2011-07-11 - 1.4.0
# * fix automated mode where any last connected player would be the one kicked
#   whatever his level
# 2011-07-11 - 1.4.1 
# * just more debug messages
#
__version__ = '1.4.1'
__author__  = 'Courgette'

from ConfigParser import NoOptionError
from b3.config import ConfigParser
from b3.plugin import Plugin
from b3.events import EVT_CLIENT_AUTH
import time
import string
import threading

class MakeroomPlugin(Plugin):
    """
    This plugin provides a command to free a slot kicking the last connected player from
    the lowest group
    """
    _adminPlugin = None
    _non_member_level = None
    _automation_enabled = None #None if not installed, False if installed but disabled
    _total_slots = None
    _min_free_slots = None
    

    def onLoadConfig(self):
        # get the admin plugin
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False

        # register our commands
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


        # load non-member group level
        try:
            self._non_member_level = self.config.getint('global_settings', 'immunity_level')
        except:
            self._non_member_level = 2
        self.info('non member level : %s' % self._non_member_level)

        try:
            self._delay = self.config.getfloat('global_settings', 'delay')
        except:
            self._delay = 5.0
        self.info('delay before kick: %s seconds' % self._delay)

        if not self.config.has_section('automation'):
            self.uninstall_automation()
        else:
            self.loadConfigAutomation()
            
            
    def loadConfigAutomation(self):
        try:
            self._automation_enabled = self.config.getboolean('automation', 'enabled')
        except NoOptionError:
            self._automation_enabled = False
        except ValueError, err:
            self.warning("bad value for setting automation/enabled. Expected 'yes' or 'no'. %s", err)
            self._automation_enabled = False
        self.info('automation enabled : %s' % self._automation_enabled)

        try:
            self._total_slots = self.config.getint('automation', 'total_slots')
            self.info('automation/total_slots : %s' % self._total_slots)
        except (NoOptionError, ValueError), err:
            self.warning("No value or bad value for automation/total_slots. %s", err)
            self.uninstall_automation()
        else:
            if self._total_slots < 2:
                self.warning("automation/total_slots cannot be less than 2")
                self.uninstall_automation()
                return
            try:
                self._min_free_slots = self.config.getint('automation', 'min_free_slots')
                self.info('automation/min_free_slots : %s' % self._min_free_slots)
            except (NoOptionError, ValueError), err:
                self.warning("No value or bad value for automation/min_free_slots. %s", err)
                self.uninstall_automation()
            if self._min_free_slots < 0:
                self.warning("automation/min_free_slots cannot be less than 0")
                self.uninstall_automation()
            if self._min_free_slots >= self._total_slots:
                self.warning("automation/min_free_slots must be less than automation/total_slots")
                self.uninstall_automation()
                

    def uninstall_automation(self):
        self._automation_enabled = None
        # remove !makeroomauto command
        if self._adminPlugin._commands.has_key('makeroomauto'):
            self._adminPlugin._commands.pop('makeroomauto')
        self.warning("Could not set up automation")
            

    def onStartup(self):
        if self._automation_enabled is not None:
            self.registerEvent(EVT_CLIENT_AUTH)


    def onEvent(self, event):
        if event.type == EVT_CLIENT_AUTH:
            if self._automation_enabled:
                self.check_free_slots(event.client)
                

    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func


    def cmd_makeroomauto(self, data=None, client=None, cmd=None):
        """\
        <on/off> - enable or disable automation
        """
        if not client:
            return
        if not data or data.lower() not in ('on', 'off'):
            client.message('^7expecting \'on\' or \'off\'')
            return
        self._automation_enabled = data.lower() == 'on'
        if self._automation_enabled:
            client.message("Makeroom automation is ON")
        else:
            client.message("Makeroom automation is OFF")
      

    def cmd_makeroom(self, data=None, client=None, cmd=None):
        """\
        free a slot
        """
        clients = self.console.clients.getClientsByLevel(min=0, max=self._non_member_level)
        self.debug("players subject to kick : %r", ["%s(%s)" % (x, x.maxLevel) for x in clients])
        clientToKick = None
        if len(clients) == 0:
            if client:
                client.message('No non-member found to kick !')
        else:
            if self._delay == 0:
                self._free_a_slot(client)
            else:
                try:
                    info_message = self.getMessage('info_message', self.console.getMessageVariables(client=client))
                except ConfigParser.NoOptionError:
                    info_message = "Making room for clan member, please come back again"
                self.console.say(info_message)
                threading.Timer(self._delay, self._free_a_slot, (client, )).start()


    def _free_a_slot(self, client):
        clients = self.console.clients.getClientsByLevel(min=0, max=self._non_member_level)
        self.debug("players subject to kick : %r", ["%s(%s)" % (x, x.maxLevel) for x in clients])
        clientToKick = None
        if len(clients) == 0:
            if client:
                client.message('No non-member found to kick !')
        else:
            # sort players by group and connection time
            clientsByGroup = sorted(clients, key=lambda x:x.maxLevel)
            #self.debug([(x.name, x.maxLevel) for x in clientsByGroup])
            lowestGroup = clientsByGroup[0].maxLevel
            lowestClients = [x for x in clientsByGroup if x.maxLevel == lowestGroup]
            #self.debug([(x.name, x.timeAdd) for x in lowestClients])
            clientsByTime = sorted(lowestClients, key=lambda x:x.timeAdd, reverse=True)
            #self.debug([(x.name, x.timeAdd) for x in clientsByTime])
            client2kick = clientsByTime[0]
            try:
                kick_message = self.getMessage('kick_message', self.console.getMessageVariables(client=client2kick))
            except ConfigParser.NoOptionError:
                kick_message = "kicking %s to free a slot" % client2kick.name
            self.console.say(kick_message)
            time.sleep(1.5)
            try:
                kick_reason = self.getMessage('kick_reason', self.console.getMessageVariables(client=client2kick))
            except ConfigParser.NoOptionError:
                kick_reason = "to free a slot"
            client2kick.kick(reason=kick_reason, keyword="makeroom", silent=True, admin=client)


    def check_free_slots(self, last_connected_client):
        nb_players = len(self.console.clients.getList())
        nb_free_slots = self._total_slots - nb_players
        self.debug("%s/%s connected players. Free slots : %s. %r", nb_players, self._total_slots, nb_free_slots, ["%s(%s)"%(x,x.maxLevel) for x in self.console.clients.getList()])
        if nb_free_slots < self._min_free_slots:
            self.debug("last_connected_client.maxLevel : %s", last_connected_client.maxLevel)
            if last_connected_client.maxLevel <= self._non_member_level:
                self.info("last connected player will be kicked")
                info_message = "Keeping a free slot, please come back again"
                self.console.say(info_message)
                kick_reason = "to free a slot"
                if self._delay == 0:
                    last_connected_client.kick(reason=kick_reason, keyword="makeroom", silent=True)
                else:
                    threading.Timer(self._delay, last_connected_client.kick, (), {'reason':kick_reason, 'keyword':"makeroom", 'silent':True}).start()
            else:
                self.info("someone will be kicked")
                self.cmd_makeroom()


if __name__ == '__main__':

    from b3.fake import fakeConsole, moderator
    from b3.fake import FakeClient
    from b3.config import XmlConfigParser

    conf1 = XmlConfigParser()
    conf1.loadFromString("""
        <configuration plugin="makeroom">

            <settings name="global_settings">
                <!-- level under which players to kick will be chosen from (default: 2) -->
                <set name="non_member_level">2</set>
                <!-- delay in seconds between the time the info_message is shown and the kick happens.
                If you set this to 0, then no info_message will be shown and kick will happen
                instantly -->
                <set name="delay">1</set>
            </settings>

            <settings name="commands">
                <!-- Command to free a slot -->
                <set name="makeroom-mr">20</set>
                <!-- Command to enable/disable automation -->
                <set name="makeroomauto-mrauto">60</set>
            </settings>

            <settings name="messages">
                <!-- You can use the following keywords in your messages :
                    $clientname
                    $clientguid
                -->
                <!-- kick_message will be displayed to all players when a player is kicked to free a slot -->
                <set name="kick_messaged">kicking $clientname to free a slot</set>
                <!-- kick_reason will be displayed to the player to be kicked -->
                <set name="kick_reasond">to make room for a server member</set>
                <!-- info_message will be displayed to all before a player get kicked -->
                <set name="info_message">Making ROOM !!!!!</set>
            </settings>
            
            <settings name="automation">
                <!-- enabled : yes/no
                  If yes, then this plugin will make sure that min_free_slots are kept free
                  and kick all connecting player until min_free_slots are free.
                 -->
                <set name="enabled">no</set>
                <!-- The total number of slots on the server  -->
                <set name="total_slots">3</set>
                <!-- The number of slots to keep free -->
                <set name="min_free_slots">1</set>
            </settings>
        </configuration>
    """)
    p = MakeroomPlugin(fakeConsole, conf1)
    p.onLoadConfig()
    p.onStartup()

    def testPlugin1():
        jack = FakeClient(fakeConsole, name="Jack", guid="qsd654sqf", _maxLevel=0)
        jack.connects(0)
        jack.says('!makeroom')
    
    def testPlugin2():
        moderator.connects(0)
        moderator.says('!makeroom')

    def testPlugin3():
        jack = FakeClient(fakeConsole, name="Jack", guid="qsd654sqf", _maxLevel=0)
        jack.connects(1)
        moderator.connects(0)
        moderator.says('!makeroom')

    def testPlugin4():
        jack = FakeClient(fakeConsole, name="Jack", _maxLevel=0)
        jack.connects(1)
        time.sleep(1.1)
        joe = FakeClient(fakeConsole, name="Joe", _maxLevel=0)
        joe.connects(2)
        moderator.connects(0)
        moderator.says('!makeroom')

    def testPlugin5():
        jack = FakeClient(fakeConsole, name="Jack", _maxLevel=0)
        jack.connects(1)
        time.sleep(1.1)
        joe = FakeClient(fakeConsole, name="Joe", _maxLevel=2)
        joe.connects(2)
        moderator.connects(0)
        moderator.says('!makeroom')

    def testMessage1():
        conf = XmlConfigParser()
        conf.loadFromString("""
            <configuration plugin="makeroom">
    
                <settings name="global_settings">
                    <!-- level under which players to kick will be chosen from (default: 2) -->
                    <set name="non_member_level">2</set>
                </settings>
    
                <settings name="commands">
                    <!-- Command to free a slot -->
                    <set name="makeroom-mr">20</set>
                </settings>

            </configuration>
        """)
        p = MakeroomPlugin(fakeConsole, conf)
        p.onStartup()
        jack = FakeClient(fakeConsole, name="Jack", guid="qsd654sqf", _maxLevel=0)
        jack.connects(1)
        moderator.connects(2)
        moderator.says('!makeroom')

    def testMessage2():
        conf = XmlConfigParser()
        conf.loadFromString("""
            <configuration plugin="makeroom">
    
                <settings name="global_settings">
                    <!-- level (inclusive) under which players to kick will be chosen from (default: 2) -->
                    <set name="non_member_level">2</set>
                    <!-- delay in seconds between the time the info_message is shown and the kick happens.
                    If you set this to 0, then no info_message will be shown and kick will happen
                    instantly -->
                    <set name="delay">0</set>
                </settings>
    
                <settings name="commands">
                    <!-- Command to free a slot -->
                    <set name="makeroom-mr">20</set>
                </settings>
    
                <settings name="messages">
                    <!-- You can use the following keywords in your messages :
                        $clientname
                    -->
                    <!-- kick_message will be displayed to all players when a player is kicked to free a slot -->
                    <set name="kick_message">kicking $clientname to make room for a member xxxxxxxxxx</set>
                    <!-- kick_reason will be displayed to the player to be kicked -->
                    <set name="kick_reason">to free a slot ! mlkjmlkj</set>
                </settings>
            </configuration>
        """)
        p = MakeroomPlugin(fakeConsole, conf)
        p.onStartup()
        jack = FakeClient(fakeConsole, name="Jack", guid="qsd654sqf", _maxLevel=0)
        jack.connects(1)
        moderator.connects(2)
        moderator.says('!makeroom')
        
        
    def testAutomation1():
        from b3.fake import superadmin
        superadmin.connects(0)
        superadmin.says('!makeroomauto')
        time.sleep(1)
        superadmin.says('!makeroomauto on')
        superadmin.says('!makeroomauto off')

    def testAutomation2():
        from b3.fake import superadmin, joe
        p._automation_enabled = True
        p._delay = 3
        p._total_slots = 2
        p._min_free_slots = 1
        superadmin.connects(0)
        time.sleep(.3)
        joe.connects(1)
        time.sleep(.3)

    def testAutomation3():
        from b3.fake import superadmin, joe
        p._automation_enabled = True
        p._delay = 3
        p._total_slots = 2
        p._min_free_slots = 1
        joe.connects(1)
        time.sleep(.3)
        superadmin.connects(0)
        time.sleep(.3)

    def testAutomation4():
        from b3.fake import superadmin, joe
        p._automation_enabled = True
        p._delay = 0
        p._total_slots = 3
        p._min_free_slots = 1
        joe.connects(0)
        time.sleep(.3)
        superadmin.connects(1)
        time.sleep(.3)
        jack = FakeClient(fakeConsole, name="Jack", guid="qsd654sqf", _maxLevel=2)
        jack.connects(2)


    #testPlugin3()
    #testPlugin5()
    #testMessage2()
    #testAutomation1()
    #testAutomation2()
    #testAutomation3()
    testAutomation4()
    time.sleep(30)
