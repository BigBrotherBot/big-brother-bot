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
#

__version__ = '1.8'
__author__ = 'Thomas LÉVEIL'


import time
import threading

from b3.functions import getCmd
from b3.config import ConfigParser
from b3.plugin import Plugin
from ConfigParser import NoOptionError


class MakeroomPlugin(Plugin):
    """
    This plugin provides a command to free a slot kicking the last
    connected player from the lowest B3 group
    """

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def __init__(self, console, config=None):
        Plugin.__init__(self, console, config)
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            raise AttributeError('could not find admin plugin')

        self._non_member_level = None
        """:type: int """
        self._automation_enabled = None  # None if not installed, False if installed but disabled
        """:type: bool """
        self._total_slots = None
        """:type: int """
        self._min_free_slots = None
        """:type: int """
        self._delay = None
        """:type: int """
        self._kick_in_progress = threading.Lock()
        self._retain_free_duration = 0
        """:type: int """
        self._retain_free_slot_info = None
        """:type: dict """

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        try:
            self._non_member_level = self.console.getGroupLevel(self.config.get('global_settings', 'non_member_level'))
        except (NoOptionError, KeyError), err:
            default_non_member_group = 'reg'
            self._non_member_level = self.console.getGroupLevel(default_non_member_group)
            self.warning("using default value %s for 'non_member_level'. %s" % (default_non_member_group, err))

        self.info('non member level : %s' % self._non_member_level)

        try:
            self._retain_free_duration = self.config.getint('global_settings', 'retain_free_duration')
            self.info('global_settings/retain_free_duration: %s' % self._retain_free_duration)
        except (NoOptionError, ValueError), err:
            self.warning("No value or bad value for global_settings/retain_free_duration. %s", err)
        else:
            if self._retain_free_duration < 0:
                self.warning("global_settings/retain_free_duration cannot be less than 0")
                self._retain_free_duration = 0
            if self._retain_free_duration > 30:
                self.warning("global_settings/retain_free_duration cannot be higher than 30s")
                self._retain_free_duration = 30

        try:
            self._delay = self.config.getfloat('global_settings', 'delay')
        except Exception:
            self._delay = 5.0
        self.info('delay before kick: %s seconds' % self._delay)

        if not self.config.has_section('automation'):
            self.uninstall_automation()
        else:
            self.load_config_automation()

    def load_config_automation(self):
        try:
            self._automation_enabled = self.config.getboolean('automation', 'enabled')
        except NoOptionError:
            self._automation_enabled = None
        except ValueError, err:
            self.warning("bad value for setting automation/enabled. Expected 'yes' or 'no'. %s", err)
            self._automation_enabled = None

        self.info('automation enabled: %s' % ('yes' if self._automation_enabled else 'no'))

        try:
            self._total_slots = self.config.getint('automation', 'total_slots')
            self.info('automation/total_slots: %s' % self._total_slots)
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
                self.info('automation/min_free_slots: %s' % self._min_free_slots)
            except (NoOptionError, ValueError), err:
                self.warning("no value or bad value for automation/min_free_slots. %s", err)
                self.uninstall_automation()
            else:
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
        self.warning("could not set up automation")

    def onStartup(self):
        """
        Initialize plugin.
        """
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

        self.registerEvent('EVT_CLIENT_AUTH', self.onClientAuth)

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onClientAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH.
        """
        # as soon as a member connects there is no need to keep kicking non-members during the
        # retain_free_slot_duration
        if event.client.maxLevel > self._non_member_level:
            self._retain_free_slot_info = None

        # as soon as the retain_free_slot_duration is expired there is no need to keep kicking non-members
        if self._retain_free_slot_info and time.time() > self._retain_free_slot_info['until']:
            self._retain_free_slot_info = None

        if self._retain_free_slot_info and time.time() <= self._retain_free_slot_info['until']:
            if event.client.maxLevel <= self._non_member_level \
                    and self._count_players() > self._retain_free_slot_info['max_taken_slots']:
                self._kick(event.client, self._retain_free_slot_info['admin'])

        elif self._automation_enabled:
            self.check_free_slots(event.client)

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_makeroomauto(self, data=None, client=None, cmd=None):
        """
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
        """
        Free a slot
        """
        if self._retain_free_slot_info and time.time() <= self._retain_free_slot_info['until']:
            client.message("There is already a makeroom request in progress. Try again later in %ss" %
                           int(self._retain_free_slot_info['until'] - time.time()))
            return

        if not self._kick_in_progress.acquire(False):
            client.message("There is already a makeroom request in progress. Try again later")
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

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def _free_a_slot(self, admin):
        """
        Free a slot on the game server.
        """
        try:

            clients = self.console.clients.getClientsByLevel(min=0, max=self._non_member_level)
            self.debug("players subject to kick : %r", ["%s(%s)" % (x, x.maxLevel) for x in clients])
            if len(clients) == 0:
                if admin:
                    admin.message('No non-member found to kick !')
            else:
                # sort players by group and connection time
                clients_by_group = sorted(clients, key=lambda _: _.maxLevel)
                #self.debug([(x.name, x.maxLevel) for x in clients_by_group])
                lowest_group = clients_by_group[0].maxLevel
                lowest_clients = [x for x in clients_by_group if x.maxLevel == lowest_group]
                #self.debug([(x.name, x.timeAdd) for x in lowestClients])
                clients_by_time = sorted(lowest_clients, key=lambda x: x.timeAdd, reverse=True)
                #self.debug([(x.name, x.timeAdd) for x in clientsByTime])
                client2kick = clients_by_time[0]
                self._kick(client2kick, admin)
                if self._retain_free_duration == 0:
                    admin.message("%s was kicked to free a slot" % client2kick.name)
                else:
                    self._retain_free_slot_info = {
                        'until': time.time() + self._retain_free_duration,
                        'max_taken_slots': self._count_players(),
                        'admin': admin
                    }
                    admin.message("%s was kicked to free a slot. "
                                  "A member has %ss to join the server" % (client2kick.name, self._retain_free_duration))
        finally:
            self._kick_in_progress.release()

    def check_free_slots(self, last_connected_client):
        """
        Check the amount of free slots
        """
        nb_players = self._count_players()
        nb_free_slots = self._total_slots - nb_players
        self.debug("%s/%s connected players. Free slots : %s. %r", nb_players, self._total_slots, nb_free_slots,
                   ["%s(%s)" % (x, x.maxLevel) for x in self.console.clients.getList()])
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
                    threading.Timer(self._delay, last_connected_client.kick, (),
                                    {'reason': kick_reason, 'keyword': "makeroom", 'silent': True}).start()
            else:
                self.info("someone will be kicked")
                self.cmd_makeroom()

    def _count_players(self):
        return len(self.console.clients.getList())

    def _kick(self, non_member, admin):
        """
        kick a non member to free a slot and display the appropriate messages
        :param non_member: b3.clients.Client
        """
        try:
            kick_message = self.getMessage('kick_message', self.console.getMessageVariables(client=non_member))
        except ConfigParser.NoOptionError:
            kick_message = "kicking %s to free a slot" % non_member.name
        self.console.say(kick_message)
        try:
            kick_reason = self.getMessage('kick_reason', self.console.getMessageVariables(client=non_member))
        except ConfigParser.NoOptionError:
            kick_reason = "to free a slot"
        non_member.kick(reason=kick_reason, keyword="makeroom", silent=True, admin=admin)
