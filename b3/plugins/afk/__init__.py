# -*- encoding: utf-8 -*-
#
# AFK Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2015 Thomas LEVEIL <thomasleveil@gmail.com>
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

__author__ = "Thomas LEVEIL"
__version__ = "1.10"


from threading import Timer
from time import time
from b3 import TEAM_SPEC
from b3.config import NoOptionError
from b3.plugin import Plugin
from weakref import WeakKeyDictionary


class AfkPlugin(Plugin):

    loadAfterPlugins = ['urtposition']

    def __init__(self, console, config=None):
        """
        Build the plugin object.
        """
        Plugin.__init__(self, console, config)

        self.min_ingame_humans = 1
        """:type : int"""

        self.consecutive_deaths_threshold = 3
        """:type : int"""

        self.inactivity_threshold_second = 50
        """:type : int"""

        self.last_chance_delay = None
        """:type : int"""
        
        self.kick_reason = None
        """:type : str"""

        self.are_you_afk = None
        """:type : str"""

        self.suspicion_announcement = None
        """:type : str"""

        self.immunity_level = 100
        """:type : Timer"""

        self.check_timer = None
        """:type : int"""

        self.kick_timers = WeakKeyDictionary()
        """:type : dict[Client, threading.Timer]"""

        self.last_global_check_time = time()
        """:type : int"""

    def onStartup(self):
        """
        Initialize plugin.
        """
        self.registerEvent(self.console.getEventID('EVT_CLIENT_KILL'), self.on_kill)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_SUICIDE'), self.on_kill)

        self.registerEvent(self.console.getEventID('EVT_CLIENT_DISCONNECT'), self.on_client_disconnect)

        self.registerEvent(self.console.getEventID('EVT_GAME_ROUND_START'), self.on_game_break)
        self.registerEvent(self.console.getEventID('EVT_GAME_ROUND_END'), self.on_game_break)
        self.registerEvent(self.console.getEventID('EVT_GAME_WARMUP'), self.on_game_break)
        self.registerEvent(self.console.getEventID('EVT_GAME_MAP_CHANGE'), self.on_game_break)

        self.registerEvent(self.console.getEventID('EVT_CLIENT_SAY'), self.on_say)

        # for UrT 4.2 modified, requires plugin `urtposition`
        event_id = self.console.getEventID('EVT_CLIENT_STANDING')
        if event_id is not None:
            self.registerEvent(event_id, self.on_client_standing)

        activity_events = {
            'EVT_CLIENT_CONNECT',
            'EVT_CLIENT_AUTH',
            'EVT_CLIENT_JOIN',
            'EVT_CLIENT_TEAM_CHANGE',
            'EVT_CLIENT_TEAM_CHANGE2',
            'EVT_CLIENT_SAY',
            'EVT_CLIENT_TEAM_SAY',
            'EVT_CLIENT_SQUAD_SAY',
            'EVT_CLIENT_PRIVATE_SAY',
            'EVT_CLIENT_GIB',
            'EVT_CLIENT_GIB_TEAM',
            'EVT_CLIENT_GIB_SELF',
            'EVT_CLIENT_KILL_TEAM',
            'EVT_CLIENT_DAMAGE',
            'EVT_CLIENT_DAMAGE_SELF',
            'EVT_CLIENT_DAMAGE_TEAM',
            'EVT_CLIENT_ITEM_PICKUP',
            'EVT_CLIENT_ACTION',
            # UrT 4.1 & 4.2
            'EVT_CLIENT_GEAR_CHANGE',
            # UrT 4.2
            'EVT_CLIENT_RADIO',
            'EVT_CLIENT_CALLVOTE',
            'EVT_CLIENT_VOTE',
            'EVT_CLIENT_JUMP_RUN_START',
            'EVT_CLIENT_JUMP_RUN_STOP',
            'EVT_CLIENT_JUMP_RUN_CANCEL',
            'EVT_CLIENT_POS_SAVE',
            'EVT_CLIENT_POS_LOAD',
            'EVT_CLIENT_GOTO',
            # UrT 4.2 modified, requires plugin `urtposition`
            'EVT_CLIENT_MOVE',
            # BF4, BFH
            'EVT_CLIENT_COMROSE',
            # Frostbite engine
            'EVT_CLIENT_SQUAD_CHANGE',
        }

        for event_key in activity_events:
            event_id = self.console.getEventID(event_key)
            if event_id is not None:
                self.registerEvent(event_id, self.on_client_activity)

    def onDisable(self):
        """
        Executed when the plugin is disabled.
        """
        self.info("stopping timers")
        self.stop_kick_timers()

    ####################################################################################################################
    #                                                                                                                  #
    #   CONFIG                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        self.load_conf_min_ingame_humans()
        self.load_conf_consecutive_deaths_threshold()
        self.load_conf_inactivity_threshold()
        self.load_conf_last_chance_delay(default=20, min_value=15, max_value=60)
        self.load_conf_kick_reason()
        self.load_conf_are_you_afk()
        self.load_conf_suspicion_announcement(
            default="{name} suspected of being AFK, kicking in {last_chance_delay}s if no answer")
        self.load_conf_immunity_level()
        self.stop_kick_timers()

    def load_conf_min_ingame_humans(self):
        try:
            self.min_ingame_humans = self.config.getint('settings', 'min_ingame_humans')
        except (NoOptionError, ValueError), err:
            self.warning("no value or bad value for settings/min_ingame_humans. %s", err)
        else:
            if self.min_ingame_humans < 0:
                self.warning("settings/min_ingame_humans cannot be less than 0")
                self.min_ingame_humans = 0
        self.info('settings/min_ingame_humans: %s ' % self.min_ingame_humans)

    def load_conf_consecutive_deaths_threshold(self):
        try:
            self.consecutive_deaths_threshold = self.config.getint('settings', 'consecutive_deaths_threshold')
        except (NoOptionError, ValueError), err:
            self.warning("no value or bad value for settings/consecutive_deaths_threshold. %s", err)
        else:
            if self.consecutive_deaths_threshold < 0:
                self.warning("settings/consecutive_deaths_threshold cannot be less than 0")
                self.consecutive_deaths_threshold = 0
        self.info('settings/consecutive_deaths_threshold: %s ' % self.consecutive_deaths_threshold)

    def load_conf_inactivity_threshold(self):
        try:
            self.inactivity_threshold_second = int(60 * self.config.getDuration('settings', 'inactivity_threshold'))
        except (NoOptionError, ValueError), err:
            self.warning("no value or bad value for settings/inactivity_threshold. %s", err)
        else:
            if self.inactivity_threshold_second < 30:
                self.warning("settings/inactivity_threshold cannot be less than 30 sec")
                self.inactivity_threshold_second = 30
        self.info('settings/inactivity_threshold: %s sec' % self.inactivity_threshold_second)

    def load_conf_last_chance_delay(self, default, min_value, max_value):
        try:
            self.last_chance_delay = self.config.getint('settings', 'last_chance_delay')
        except (NoOptionError, ValueError), err:
            self.warning("no value or bad value for settings/last_chance_delay. %s", err)
            self.last_chance_delay = default
        else:
            if self.last_chance_delay < min_value:
                self.warning("settings/last_chance_delay cannot be less than %s sec" % min_value)
                self.last_chance_delay = min_value
            elif self.last_chance_delay > max_value:
                self.warning("settings/last_chance_delay cannot be higher than %s sec" % max_value)
                self.last_chance_delay = max_value
        self.info('settings/last_chance_delay: %s sec' % self.last_chance_delay)

    def load_conf_kick_reason(self):
        try:
            self.kick_reason = self.config.get('settings', 'kick_reason')
            if len(self.kick_reason.strip()) == 0:
                raise ValueError()
            self.info('settings/kick_reason: %s sec' % self.kick_reason)
        except (NoOptionError, ValueError), err:
            self.warning("no value or bad value for settings/kick_reason. %s", err)
            self.kick_reason = "AFK for too long on this server"

    def load_conf_are_you_afk(self):
        try:
            self.are_you_afk = self.config.get('settings', 'are_you_afk')
            if len(self.are_you_afk.strip()) == 0:
                raise ValueError()
            self.info('settings/are_you_afk: %s sec' % self.are_you_afk)
        except (NoOptionError, ValueError), err:
            self.warning("no value or bad value for settings/are_you_afk. %s", err)
            self.are_you_afk = "Are you AFK?"

    def load_conf_suspicion_announcement(self, default):
        try:
            self.suspicion_announcement = self.config.get('settings', 'suspicion_announcement')
            if len(self.suspicion_announcement.strip()) == 0:
                raise ValueError()
            if "{name}" not in self.suspicion_announcement:
                raise ValueError("missing placeholder {name}")
            if "{last_chance_delay}" not in self.suspicion_announcement:
                raise ValueError("missing placeholder {last_chance_delay}")
        except (NoOptionError, ValueError), err:
            self.warning("no value or bad value for settings/suspicion_announcement. %s", err)
            self.suspicion_announcement = default
        self.info('settings/suspicion_announcement: %s' % self.suspicion_announcement)

    def load_conf_immunity_level(self):
        try:
            self.immunity_level = self.config.getint('settings', 'immunity_level')
        except NoOptionError:
            self.info('no value for settings/immunity_level. Using default value : %s' % self.immunity_level)
        except ValueError, err:
            self.debug(err)
            self.warning('bad value for settings/immunity_level. Using default value : %s' % self.immunity_level)
        except Exception, err:
            self.error(err)
        self.info('immunity_level is %s' % self.immunity_level)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def on_client_disconnect(self, event):
        """
        make sure to clean eventual timers when a client disconnects

        :param event: b3.events.Event
        """
        self.clear_kick_timer_for_client(event.client)
        if hasattr(event.client, 'last_activity_time'):
            del event.client.last_activity_time

    def count_ingame_humans(self):
        """
        :return: int the number of humans who are not spectator
        """
        return len([x for x in self.console.clients.getList() if not x.bot and x.team != TEAM_SPEC])

    def on_kill(self, event):
        """
        Executed when EVT_CLIENT_KILL is received.
        """
        self.on_client_activity(event)
        if event.target and event.target == event.client:
            self.verbose2("suicide: not considered as a death as player is active")
            return
        if not hasattr(event.target, "afk_death_count"):
            event.target.afk_death_count = 0
        event.target.afk_death_count += 1
        ingame_humans = self.count_ingame_humans()
        self.verbose2("%r.afk_death_count: %s, last activity: %.1fs ago, in-game humans: %s" % (
            event.target,
            event.target.afk_death_count,
            (time() - getattr(event.target, 'last_activity_time', time())),
            ingame_humans
        ))
        if event.target.afk_death_count >= self.consecutive_deaths_threshold and \
           ingame_humans > self.min_ingame_humans:
            self.check_client(event.target)

    def on_client_activity(self, event, now=None):
        """
        Acknowledge client activity
        :param event: b3.events.Event
        :param now: int (optional) the time the activity happened. If None, current time is used.
        """
        if not event.client:
            return
        if now is None:
            now = time()
        if event.client in self.kick_timers:
            event.client.message("OK, you are not AFK")
        event.client.last_activity_time = now
        event.client.afk_death_count = 0
        self.clear_kick_timer_for_client(event.client)

    def on_client_standing(self, event):
        """
        Happens when we are notified a client is standing still.
        Requires UrT 4.2 modified + urtposition B3 plugin
        :param event: b3.events.Event
        """
        if not event.client:
            return
        self.check_client(event.client)

    def on_game_break(self, _):
        """
        Clear all last activity records so no one can be kick before he has time to join the game.
        This is to prevent player with slow computer to get kicked while loading the map at round start.
        """
        self.info("game break, clearing afk timers")
        self.stop_kick_timers()
        for client in [x for x in self.console.clients.getList() if hasattr(x, 'last_activity_time')]:
            del client.last_activity_time
            del client.afk_death_count

    def on_say(self, event):
        if "afk" in event.data.lower():
            self.check_all_clients()

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHERS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def check_all_clients(self, now=None):
        """
        If last check was older than 15s ago, check all clients for inactivity
        :param now: int (optional) the time the activity happened. If None, current time is used.
        """
        if now is None:
            now = time()
        last_check_ago = now - self.last_global_check_time

        if last_check_ago > 15:
            list_of_players = [x for x in self.console.clients.getList()
                               if x.team != TEAM_SPEC and not getattr(x, 'bot', False)]
            self.info("looking for afk players...")
            self.last_global_check_time = now
            for client in list_of_players:
                self.check_client(client)

    def check_client(self, client):
        """
        Check if client is afk
        :param client: b3.clients.Client
        """
        if self.is_client_inactive(client):
            self.ask_client(client)

    def is_client_inactive(self, client):
        """
        Check whether a client is inactive.
        :return:
        """
        if getattr(client, 'bot', False):
            self.verbose2("%s is a bot" % client.name)
            return False
        if client.maxLevel >= self.immunity_level:
            self.verbose2("%s is in group %s -> immune" % (client.name, client.maxGroup))
            return False
        if client.team in (TEAM_SPEC,):
            self.verbose2("%s is in %s team" % (client.name, client.team))
            return False
        if not hasattr(client, 'last_activity_time'):
            self.verbose2("%s has no last activity time recorded, cannot check" % client.name)
            return False
        inactivity_duration = time() - client.last_activity_time
        if inactivity_duration > self.inactivity_threshold_second:
            self.verbose2("last activity {:5.1f} ago for {!r}".format(inactivity_duration, client))
            return True
        return False

    def ask_client(self, client):
        """
        Ask a player if he is afk.
        :param client : b3.clients.Client
        """
        if client in self.kick_timers:
            self.verbose("%s is already in kick_timers" % client)
            return
        self.info("%r suspected of being AFK" % client)
        client.message(self.are_you_afk)
        self.console.say(self.suspicion_announcement.format(name=client.name, last_chance_delay=self.last_chance_delay))
        t = Timer(self.last_chance_delay, self.kick_client, (client, ))
        t.start()
        self.kick_timers[client] = t

    def kick_client(self, client):
        """
        Kick a player if conditions are met
        :param client: the player to kick
        """
        self.clear_kick_timer_for_client(client)
        if self.count_ingame_humans() <= self.min_ingame_humans:
            self.info("not kicking %s after all since they are too few humans left on the server" % client)
            return
        if self.is_client_inactive(client):
            self.info("kicking %r" % client)
            client.kick(reason=self.kick_reason)

    def stop_kick_timers(self):
        if self.kick_timers:
            for client in list(self.kick_timers.keys()):
                timer = self.kick_timers.pop(client)
                if timer:
                    timer.cancel()

    def clear_kick_timer_for_client(self, client):
        if self.kick_timers:
            if client in self.kick_timers:
                self.kick_timers.pop(client).cancel()

    def verbose2(self, msg, *args, **kwargs):
        """
        Log a VERBOSE2 message to the main log. More "chatty" than a VERBOSE message.
        """
        self.console.verbose2('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)
