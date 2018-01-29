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

__author__ = 'Walker, ThorN'
__version__ = '1.2.3'

import b3
import b3.events
import b3.plugin

from b3.functions import getCmd

class SpreeStats(object):
    kills = 0
    deaths = 0
    endLoosingSpreeMessage = None
    endKillSpreeMessage = None
    

class SpreePlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _killingspree_messages_dict = {}
    _loosingspree_messages_dict = {}
    _reset_spree_stats = False
    _clientvar_name = 'spree_info'

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize plugin settings
        """
        # get the plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')

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

        # listen for client events
        self.registerEvent('EVT_CLIENT_KILL', self.onClientKill)
        self.registerEvent('EVT_GAME_EXIT', self.onGameExit)

        self.debug('plugin started')

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        self._reset_spree_stats = self.getSetting('settings', 'reset_spree', b3.BOOL, self._reset_spree_stats)
        self.init_spreemessage_list()

    ####################################################################################################################
    #                                                                                                                  #
    #    HANDLE EVENTS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def onClientKill(self, event):
        """
        Handle EVT_CLIENT_KILL
        """
        self.handle_kills(event.client, event.target)

    def onGameExit(self, event):
        """
        Handle EVT_GAME_EXIT
        """
        if self._reset_spree_stats:
            for c in self.console.clients.getList():
               self.init_spree_stats(c)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################
              
    def init_spreemessage_list(self):
        # get the spree messages from the config
        # split the start and end spree messages and save it in the dictionary
        for kills, message in self.config.items('killingspree_messages'):
            if '#' in message:
                start_message, stop_message = message.split('#')
                self._killingspree_messages_dict[int(kills)] = [start_message.strip(), stop_message.strip()]
            else:
                self.warning("ignoring killingspree message %r due to missing '#'" % message)
        for deaths, message in self.config.items('loosingspree_messages'):
            if '#' in message:
                start_message, stop_message = message.split('#')
                self._loosingspree_messages_dict[int(deaths)] = [start_message.strip(), stop_message.strip()]
            else:
                self.warning("ignoring killingspree message %r due to missing '#'" % message)
        self.verbose('spree-messages are loaded in memory')

    def init_spree_stats(self, client):
        # initialize the clients spree stats
        client.setvar(self, self._clientvar_name, SpreeStats())
    
    def get_spree_stats(self, client):
        # get the clients stats
        # pass the plugin reference first
        # the key second
        # the defualt value first
        if not client.isvar(self, self._clientvar_name):
            # initialize the default spree object
            # we don't just use the client.var(...,default) here so we
            # don't create a new SpreeStats object for no reason every call
            client.setvar(self, self._clientvar_name, SpreeStats())
        return client.var(self, self._clientvar_name).value
    
    def handle_kills(self, client=None, victim=None):
        """
        A kill was made. Add 1 to the client and set his deaths to 0.
        Add 1 death to the victim and set his kills to 0.
        """
        # client (attacker)
        if client:
            # we grab our SpreeStats object here
            # any changes to its values will be saved "automagically"
            spreeStats = self.get_spree_stats(client)
            spreeStats.kills += 1
            
            # Check if the client was on a loosing spree. If so then show his end loosing spree msg.
            if spreeStats.endLoosingSpreeMessage:
                self.show_message(client, victim, spreeStats.endLoosingSpreeMessage)
                # reset any possible loosing spree to None
                spreeStats.endLoosingSpreeMessage = None
            # Check if the client is on a killing spree. If so then show it.
            message = self.get_spree_message(spreeStats.kills, 0)
            if message:
                # Save the 'end'spree message in the client. That is used when the spree ends.
                spreeStats.endKillSpreeMessage = message[1]

                # Show the 'start'spree message
                self.show_message(client, victim, message[0])

            # deaths spree is over, reset deaths
            spreeStats.deaths = 0

        # victim
        if victim:
            spreeStats = self.get_spree_stats(victim)
            spreeStats.deaths += 1
            
            # check if the victim had a killing spree and show a end_killing_spree message
            if spreeStats.endKillSpreeMessage:
                self.show_message(client, victim, spreeStats.endKillSpreeMessage)
                # reset any possible end spree to None
                spreeStats.endKillSpreeMessage = None

            # check if the victim is on a 'loosing'spree
            message = self.get_spree_message(0, spreeStats.deaths)
            if message:
                #Save the 'loosing'spree message in the client.
                spreeStats.endLoosingSpreeMessage = message[1]
                
                self.show_message(victim, client, message[0])
                
            # kill spree is over, reset kills
            spreeStats.kills = 0

    def get_spree_message(self, kills, deaths):
        """
        Get the appropriate spree message.
        Return a list in the format (start spree message, end spree message)
        """
        # default is None, there is no message
        message = None
        # killing spree check
        if kills != 0:
            # if there is an entry for this number of kills, grab it, otherwise
            # return None
            message = self._killingspree_messages_dict.get(kills, None)
        # loosing spree check
        elif deaths != 0:
            message = self._loosingspree_messages_dict.get(deaths, None)
        return message

    def show_message(self, client, victim=None, message=None):
        """
        Replace variables and display the message
        """
        if message and not client.hide:
            message = message.replace('%player%', client.name)
            if victim:
                message = message.replace('%victim%', victim.name)
            self.console.say(message)        

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_spree(self, data, client, cmd=None):
        """
        <player> - show a players' winning/loosing spree
        """        
        targm = '^7You have'
        targmns = '^7You are'
        if not data:
            sclient = client
        else:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if not sclient:
                return
            targm = '%s has' % sclient.name
            targmns = '%s is' % sclient.name

        spreeStats = self.get_spree_stats(sclient)

        if spreeStats.kills > 0:
            cmd.sayLoudOrPM(client, '%s ^2%s^7 kills in a row' % (targm, spreeStats.kills))
        elif spreeStats.deaths > 0:
            cmd.sayLoudOrPM(client, '%s ^1%s^7 deaths in a row' % (targm, spreeStats.deaths))
        else:
            cmd.sayLoudOrPM(client, '%s not having a spree right now' % targmns)