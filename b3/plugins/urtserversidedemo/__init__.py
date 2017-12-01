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

import re

from threading import Timer
from threading import Thread
from threading import Event as TEvent
from b3.plugin import Plugin
from b3.functions import minutesStr
from b3.functions import getCmd

__version__ = '2.2'
__author__ = 'Courgette'

class UrtserversidedemoPlugin(Plugin):

    requiresParsers = ['iourt41', 'iourt42', 'iourt43']
    loadAfterPlugins = ['follow', 'haxbusterurt']
    demo_manager = None

    def __init__(self, console, config=None):
        """
        Initialize plugin object
        """
        self._re_startserverdemo_success = re.compile(r"""^startserverdemo: recording (?P<name>.+) to (?P<file>.+\.(?:dm_68|urtdemo))$""")
        self._adminPlugin = None
        self._haxbusterurt_demo_duration = 0 # if the haxbusterurt plugin is present, how long should last demo of cheaters
        self._follow_demo_duration = 0 # if the follow plugin is present, how long should last demo of cheaters
        self._recording_all_players = False # if True, then connecting players will be recorded
        Plugin.__init__(self, console, config)

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN INTERFACE IMPLEMENTATION                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        self._load_config_haxbusterurt()
        self._load_config_follow()

    def onStartup(self):
        """
        Startup the plugin
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')

        if not self.has_startserverdemo_cmd():
            self.error("this plugin can only work with ioUrTded server with server-side demo recording capabilities: "
                       "see http://www.urbanterror.info/forums/topic/28657-server-side-demo-recording/")
            self.disable()
            return
        else:
            self.debug("server has startserverdemo command")

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

        self.demo_manager = DemoManager(self)

        self.registerEvent('EVT_CLIENT_DISCONNECT', self.onDisconnect)
        self.registerEvent('EVT_CLIENT_JOIN', self.onJoin)

        # http://forum.bigbrotherbot.net/plugins-by-courgette/hax-buster-%28urt%29/
        if self.console.getPlugin('haxbusterurt'):
            self.info("HaxBusterUrt plugin found - we will auto record demos for suspected hackers")
            self.registerEvent('EVT_BAD_GUID', self.onHaxBusterUrTEvent)
            self.registerEvent('EVT_1337_PORT', self.onHaxBusterUrTEvent)
        else:
            self.info("HaxBusterUrt plugin not found")

        # http://forum.bigbrotherbot.net/releases/follow-users-plugin/
        if self.console.getPlugin('follow'):
            self.info("Follow plugin found - we will auto record demos for followed players")
            self.registerEvent('EVT_FOLLOW_CONNECTED', self.onFollowConnectedEvent)
        else:
            self.info("Follow plugin not found")

    ####################################################################################################################
    #                                                                                                                  #
    #   HANDLE EVENTS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def onExit(self, event):
        """
        Handle EVT_EXIT
        """
        self.onStop(event)

    def onStop(self, event):
        """
        Handle EVT_STOP
        """
        self.stop_recording_all_players()
        self.demo_manager.shutdown()

    def onDisconnect(self, event):
        """
        Handle EVT_CLIENT_DISCONNECT
        """
        self.demo_manager.on_player_disconnect(event.client)

    def onJoin(self, event):
        """
        Handle EVT_CLIENT_JOIN
        """
        client = event.client
        self.demo_manager.on_player_join(client)
        if self._recording_all_players:
            self.info("auto recording joining player %s on slot %s %s" % (client.name, client.cid, client.guid))
            self.demo_manager.take_demo(client)

    def onHaxBusterUrTEvent(self, event):
        """
        Handle events produced by the HaxBusterUrt plugin
        """
        client = event.client
        if self._recording_all_players:
            self.info("[haxbusterurt] all players are currently being recorded, nothing to do")
        else:
            self.info("[haxbusterurt] auto recording for %s min player %s on slot %s %s %s" % (
                self._haxbusterurt_demo_duration, client.name, client.cid, client.guid, client.ip))
            self.demo_manager.take_demo(client, duration=self._haxbusterurt_demo_duration * 60)

    def onFollowConnectedEvent(self, event):
        """
        Handle events producted by the follow plugin
        """
        client = event.client
        if self._recording_all_players:
            self.info("[Follow] all players are currently being recorded, nothing to do")
        else:
            self.info("[Follow] auto recording for %s min player %s on slot %s %s %s" % (
                self._follow_demo_duration, client.name, client.cid, client.guid, client.ip))
            self.demo_manager.take_demo(client, duration=self._follow_demo_duration * 60)

    def onDisable(self):
        """
        Actions to take when the plugin is disabled
        """
        was_recording_all_players = self._recording_all_players
        self.stop_recording_all_players()
        if was_recording_all_players:
            # persist the value so demo can restart when plugin is re-enabled
            self._recording_all_players = True

    def onEnable(self):
        """
        Actions to take when the plugin is enabled
        """
        if self._recording_all_players:
            self.start_recording_all_players()

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS IMPLEMENTATIONS                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_startserverdemo(self, data, client, cmd=None):
        """
        <player> - starts recording a demo for the given player. Use 'all' for all players.
        """
        if not data:
            client.message("specify a player name or 'all'")
            return

        if data == 'all':
            self.start_recording_all_players(admin=client)
            return

        targetted_player = self._adminPlugin.findClientPrompt(data, client)
        if not targetted_player:
            # a player matching the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        self.demo_manager.take_demo(targetted_player, admin=client)

    def cmd_stopserverdemo(self, data, client, cmd=None):
        """
        <player> - stops recording a demo for the given player. Use 'all' for all players.
        """
        if not data:
            client.message("specify a player name or 'all'")
            return

        if data.split(' ')[0] == 'all':
            self.stop_recording_all_players(admin=client)
            return

        targetted_player = self._adminPlugin.findClientPrompt(data, client)
        if not targetted_player:
            # a player matching the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        self.demo_manager.stop_demo(targetted_player, admin=client)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def has_startserverdemo_cmd(self):
        rv = self.console.write('cmdlist startserverdemo')
        return 'startserverdemo' in rv

    def _load_config_haxbusterurt(self):
        try:
            self._haxbusterurt_demo_duration = self.config.getint('haxbusterurt', 'demo_duration')
        except Exception, err:
            self.warning(err)
        self.info('haxbusterurt demo_duration: %s minutes' % self._haxbusterurt_demo_duration)

    def _load_config_follow(self):
        try:
            self._follow_demo_duration = self.config.getint('follow', 'demo_duration')
        except Exception, err:
            self.warning(err)
        self.info('follow demo_duration: %s minutes' % self._follow_demo_duration)

    def start_recording_all_players(self, admin=None):
        self._recording_all_players = True
        rv = self.console.write("startserverdemo all")
        if admin:
            if rv:
                admin.message(rv)
            else:
                admin.message("start recording all players")

    def stop_recording_all_players(self, admin=None):
        self._recording_all_players = False
        rv = self.console.write("stopserverdemo all")
        if admin:
            if rv:
                admin.message(rv)
            else:
                admin.message("stop recording all players")

    def start_recording_player(self, client, admin=None):
        msg_prefix = "" if not admin else "[%s] " % admin.name
        rv = self.console.write("startserverdemo %s" % client.cid)
        match = self._re_startserverdemo_success.match(rv)
        if match:
            self.info("%sstart recording player \"%s\" %s %s : %s" % (msg_prefix, client.name, client.guid, client.ip, match.group('file')))
        else:
            self.warning("%sstart recording player \"%s\" %s %s : %s" % (msg_prefix, client.name, client.guid, client.ip, rv))
        return rv

    def stop_recording_player(self, client, admin=None):
        msg_prefix = "" if not admin else "[%s] " % admin.name
        rv = self.console.write("stopserverdemo %s" % client.cid)
        self.info("%sstop recording player \"%s\" %s %s : %s" % (msg_prefix, client.name, client.guid, client.ip, rv))
        if admin:
            admin.message(rv)


class DemoManager(object):
    """
    Class that remembers which demo is being taken, or waiting to be taken
    """
    
    def __init__(self, plugin):
        self.plugin = plugin
        self._demo_starters = {} # dict<guid, DemoStarter>
        self._auto_stop_timers = {} # dict<guid, Timer object for the auto-stopping demos>

    #--------------------------------------------------------------------------------------------
    #   PUBLIC API
    #--------------------------------------------------------------------------------------------

    def take_demo(self, player, admin=None, duration=None):
        """
        Starts a demo for player (and given duration).
        If the player is not in a playing team, wait for player to join or leave the server.
        """
        if player.guid in self._demo_starters:
            # we already have a DemoStarter for that player
            starter = self._demo_starters[player.guid]
            if starter.is_alive():
                starter.cancel()

        if player.guid in self._auto_stop_timers:
            stopper = self._auto_stop_timers[player.guid]
            stopper.cancel()
            del self._auto_stop_timers[player.guid]

        self._demo_starters[player.guid] = DemoStarter(self, player, admin, duration)
        self._demo_starters[player.guid].start()

    def stop_demo(self, player, admin=None):
        if player.guid in self._demo_starters:
            # we already have a DemoStarter for that player
            starter = self._demo_starters[player.guid]
            if starter.is_alive():
                starter.cancel()
        self.plugin.stop_recording_player(player, admin)

    def shutdown(self):
        """
        Cancel all DemoStarter objects and stopper timers that would be waiting
        """
        for guid, starter in self._demo_starters.items():
            starter.cancel()
        for guid, stopper in self._auto_stop_timers:
            stopper.cancel()

    def on_player_disconnect(self, player):
        """
        Called when a player leaves the game server
        """
        stopper = self._auto_stop_timers.get(player.guid, None)
        if stopper:
            stopper.cancel()
            del self._auto_stop_timers[player.guid]

        starter = self._demo_starters.get(player.guid, None)
        if starter:
            starter.cancel()

    def on_player_join(self, player):
        """
        Called when a player joins a team
        """
        stopper = self._auto_stop_timers.get(player.guid, None)
        if stopper:
            stopper.cancel()
            del self._auto_stop_timers[player.guid]

        starter = self._demo_starters.get(player.guid, None)
        if starter:
            starter.tick()

    #--------------------------------------------------------------------------------------------
    #   API for DemoStarters only
    #--------------------------------------------------------------------------------------------

    def _done_callback(self, player_guid):
        """
        callback used by DemoStarter objects to notify the manager they are done with their task
        """
        if player_guid in self._demo_starters:
            del self._demo_starters[player_guid]

    def _start_autostop_timer(self, client, duration, admin=None):
        str_duration = minutesStr(duration/60.0)
        self.plugin.info("starting auto-stop demo timer for %s and %s" % (client.name, str_duration))
        t = self._auto_stop_timers.get(client.guid, None)
        if t:
            # stop eventually existing auto-stop timer for that player
            t.cancel()
        t = self._auto_stop_timers[client.guid] = Timer(duration, self._autostop_recording_player, [client])
        t.start()
        if admin:
           admin.message("demo for %s will stop in %s" % (client.name, str_duration))

    #--------------------------------------------------------------------------------------------
    #   OTHER METHODS
    #--------------------------------------------------------------------------------------------

    def _autostop_recording_player(self, client):
        self.plugin.debug("auto-stopping demo for %s" % client.name)
        self.plugin.stop_recording_player(client)
        del self._auto_stop_timers[client.guid]


class DemoStarter(Thread):
    """
    class that will start a server side demo for a given player right away if the player is in a recordable team,
    or as soon as the player join a recordable team (hence will wait until).
    Waiting will be cancelled if the player leaves the server.
    If a duration is provided, will make sure to end the demo after the given duration elapsed.
    """
    STATE_PLAYER_NOT_ACTIVE = 1
    STATE_DEMO_STARTED = 2
    STATE_DEMO_ALREADY_STARTED = 3
    STATE_DEMO_CANNOT_BE_STARTED = 4

    def __init__(self, demo_manager, client, admin=None, duration=None):
        """
        Starts an agent that will start a server-side demo for the given client.
        :param demo_manager: DemoManager object asking for the demo
        :param client: Client object for the player to take the demo of
        :param admin: optional Client object for the admin who ordered the demo
        :param duration: optional duration in second the demo must last (ignored if a demo was already recording that player)
        :return: None
        """
        self.demo_manager = demo_manager
        self.plugin = demo_manager.plugin
        self.client = client
        self.admin = admin
        self.duration = duration
        self._cancel_event = TEvent() # will be used to give up trying
        self._try_event = TEvent() # will be used to trigger another try
        Thread.__init__(self, name="DemoStarter(%s)" % client.name)

    #--------------------------------------------------------------------------------------------
    #   API
    #--------------------------------------------------------------------------------------------

    def run(self):
        while True:
            if self._is_cancelled():
                break
            if not self.plugin.working:
                break
            if not self.client.connected:
                self.plugin.debug("%s: client disconnected" % self.name)
                break

            state, rv = self._try_to_start_demo()
            if state == self.STATE_DEMO_STARTED:
                if self.admin:
                    self.admin.message(rv)
                if self.duration:
                    self.demo_manager._start_autostop_timer(self.client, self.duration, self.admin)
                break
            elif state == self.STATE_PLAYER_NOT_ACTIVE:
                if self.admin:
                    self.admin.message("player %s has not joined the game yet, will retry in a while" % self.client.name)
                self._try_event.wait() # for player to join a team / disconnect or bot to stop
            elif state in (self.STATE_DEMO_ALREADY_STARTED, self.STATE_DEMO_CANNOT_BE_STARTED):
                if self.admin:
                    self.admin.message(rv)
                break
            else:
                raise AssertionError("unexpected state : %s" % state)

        self.demo_manager._done_callback(self.client.guid)
        self.plugin.debug("%s: end" % self.name)

    def tick(self):
        """
        try again to start the demo
        """
        self._try_event.set()
        self._try_event.clear()

    def cancel(self):
        """
        if waiting to try, cancel and stop
        """
        self._cancel_event.set()
        self.tick()

    #--------------------------------------------------------------------------------------------
    #   PRIVATE
    #--------------------------------------------------------------------------------------------

    def _try_to_start_demo(self):
        rv = self.plugin.start_recording_player(self.client, self.admin)
        if rv.startswith("startserverdemo: recording "):
            return self.STATE_DEMO_STARTED, rv
        elif rv.endswith("is already being recorded"):
            return self.STATE_DEMO_ALREADY_STARTED, rv
        elif rv.endswith(" is not active"):
            return self.STATE_PLAYER_NOT_ACTIVE, rv
        elif rv.startswith("No player"):
            return self.STATE_DEMO_CANNOT_BE_STARTED, rv
        else:
            raise AssertionError("unexpected response: %r" % rv)

    def _is_cancelled(self):
        return self._cancel_event.is_set()