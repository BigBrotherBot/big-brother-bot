#
# PowerAdmin Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Thomas LEVEIL <courgette@bigbrotherbot.net)
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

import re
import b3.plugin
import ConfigParser

from b3.plugins.poweradminurt.iourt41 import Poweradminurt41Plugin


class Poweradminurt42Plugin(Poweradminurt41Plugin):

    requiresParsers = ['iourt42']

    _gears = dict(none='FGHIJKLMNZacefghOQRSTUVWX', all='', reset='')
    _weapons = dict(ber='F', de='G', glo='f', colt='g', spas='H', mp5='I', ump='J', mac='h', hk='K',
                    lr='L', g36='M', psg='N', sr8='Z', ak='a', neg='c', m4='e', he='O', smo='Q',
                    vest='R', hel='W', sil='U', las='V', med='T', nvg='S', ammo='X')

    # less likely weapon names to check if we fail
    # to recognize a weapon with the _weapon lists
    _weapon_aliases = {
        ".50": "de",
        "eag": "de",
        "mp": "mp5",
        "sr": "sr8",
        "1911": "colt",
        "kev": "vest",
        "gog": "nvg",
        "ext": "ammo",
        "amm": "ammo",
    }

    _weapon_groups = {
        'all_nades': 'OQ',
        'all_snipers': 'NZ',
        'all_pistols': 'FGfg',
        'all_auto': 'IJLMaceh',
    }

    # radio spam protection
    _rsp_enable = False
    _rsp_mute_duration = 2
    _rsp_falloffRate = 2  # spam points will fall off by 1 point every 4 seconds
    _rsp_maxSpamins = 10

    def onStartup(self):
        """
        Initialize plugin settings
        """
        Poweradminurt41Plugin.onStartup(self)
        self._gears['reset'] = self.console.getCvar('g_gear').getString()

    def registerEvents(self):
        """
        Register events needed
        """
        Poweradminurt41Plugin.registerEvents(self)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_RADIO'))

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        Poweradminurt41Plugin.onLoadConfig(self)
        self.loadRadioSpamProtection()

    def onEvent(self, event):
        """
        Handle intercepted events
        """
        if event.type == self.console.getEventID('EVT_CLIENT_RADIO'):
            self.onRadio(event)
        else:
            Poweradminurt41Plugin.onEvent(self, event)

    ####################################################################################################################
    #                                                                                                                  #
    #    CONFIG LOADERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def loadRadioSpamProtection(self):
        """
        Setup the radio spam protection
        """
        try:
            self._rsp_enable = self.config.getboolean('radio_spam_protection', 'enable')
        except ConfigParser.NoOptionError:
            self.warning('Could not find radio_spam_protection/enable in config file, using default: %s' %
                         self._rsp_enable)
        except ValueError, e:
            self.error('Could not load radio_spam_protection/enable config value: %s' % e)
            self.debug('Using default value (%s) for radio_spam_protection/enable' % self._rsp_enable)

        try:

            self._rsp_mute_duration = self.config.getint('radio_spam_protection', 'mute_duration')
            if self._rsp_mute_duration < 1:
                raise ValueError('radio_spam_protection/mute_duration cannot be lower than 1')

        except ConfigParser.NoOptionError:
            self.warning('Could not find radio_spam_protection/mute_duration in config file, using default: %s' %
                         self._rsp_mute_duration)
        except ValueError, e:
            self._rsp_mute_duration = 2  # set again because it might have been overwritten
            self.error('Could not load radio_spam_protection/mute_duration config value: %s' % e)
            self.debug('Using default value (%s) for radio_spam_protection/mute_duration' % self._rsp_mute_duration)

        self.debug('Radio spam protection enable: %s' % self._rsp_enable)
        self.debug('Radio spam protection mute duration: %s' % self._rsp_mute_duration)

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENT HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def onRadio(self, event):
        """
        Handle radio events
        """
        if not self._rsp_enable:
            return

        # event.data : {'msg_group': '7', 'msg_id': '2', 'location': 'New Alley', 'text': "I'm going for the flag" }

        client = event.client
        if client.var(self, 'radio_ignore_till', self.getTime()).value > self.getTime():
            self.debug("ignoring radio event")
            return

        points = 0
        data = repr(event.data)
        last_message_data = client.var(self, 'last_radio_data').value

        now = self.getTime()
        last_radio_time = client.var(self, 'last_radio_time', None).value
        gap = None
        if last_radio_time is not None:
            gap = now - last_radio_time
            if gap < 20:
                points += 1
            if gap < 2:
                points += 1
                if data == last_message_data:
                    points += 3
            if gap < 1:
                points += 3

        spamins = client.var(self, 'radio_spamins', 0).value + points

        # apply natural points decrease due to time
        if gap is not None:
            spamins -= int(gap / self._rsp_falloffRate)

        if spamins < 1:
            spamins = 0

        # set new values
        self.verbose("radio_spamins for %s : %s" % (client.name, spamins))
        client.setvar(self, 'radio_spamins', spamins)
        client.setvar(self, 'last_radio_time', now)
        client.setvar(self, 'last_radio_data', data)

        # should we warn ?
        if spamins >= self._rsp_maxSpamins:
            self.console.writelines(["mute %s %s" % (client.cid, self._rsp_mute_duration)])
            client.setvar(self, 'radio_spamins', int(self._rsp_maxSpamins / 2.0))
            client.setvar(self, 'radio_ignore_till', int(self.getTime() + self._rsp_mute_duration - 1))

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_pakill(self, data, client, cmd=None):
        """
        <player> - kill a player.
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data:
            client.message('^7Invalid data, try !help pakill')
            return

        sclient = self._adminPlugin.findClientPrompt(data, client)
        if not sclient:
            # a player matchin the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        self.console.write('smite %s' % sclient.cid)

    def cmd_palms(self, data, client, cmd=None):
        """
        Change game type to Last Man Standing
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '1')
        if client:
            client.message('^7game type changed to ^4Last Man Standing')

        self.set_configmode('lms')

    def cmd_pajump(self, data, client, cmd=None):
        """
        Change game type to Jump
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '9')
        if client:
            client.message('^7game type changed to ^4Jump')

        self.set_configmode('jump')

    def cmd_pafreeze(self, data, client, cmd=None):
        """
        Change game type to Freeze Tag
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '10')
        if client:
            client.message('^7game type changed to ^4Freeze Tag')

        self.set_configmode('freeze')

    def cmd_paskins(self, data, client, cmd=None):
        """
        Set the use of client skins <on/off>
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help paskins')
            return

        if data == 'on':
            self.console.setCvar('g_skins', '1')
            self.console.say('^7Client skins: ^2ON')
        elif data == 'off':
            self.console.setCvar('g_skins', '0')
            self.console.say('^7Client skins: ^1OFF')

    def cmd_pafunstuff(self, data, client, cmd=None):
        """
        Set the use of funstuff <on/off>
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help pafunstuff')
            return

        if data == 'on':
            self.console.setCvar('g_funstuff', 1)
            self.console.say('^7Funstuff: ^2ON')
        elif data == 'off':
            self.console.setCvar('g_funstuff', 0)
            self.console.say('^7Funstuff: ^1OFF')

    def cmd_pagoto(self, data, client, cmd=None):
        """
        Set the goto <on/off>
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help pagoto')
            return

        if data == 'on':
            self.console.setCvar('g_allowgoto', 1)
            self.console.say('^7Goto: ^2ON')
        elif data == 'off':
            self.console.setCvar('g_allowgoto', 0)
            self.console.say('^7Goto: ^1OFF')

    def cmd_pastamina(self, data, client, cmd=None):
        """
        Set the stamina behavior <default/regain/infinite>
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('default', 'regain', 'infinite'):
            client.message('^7Invalid or missing data, try !help pastamina')
            return

        if data == 'default':
            self.console.setCvar('g_stamina', 0)
            self.console.say('^7Stamina mode: ^3DEFAULT')
        elif data == 'regain':
            self.console.setCvar('g_stamina', 1)
            self.console.say('^7Stamina mode: ^3REGAIN')
        elif data == 'infinite':
            self.console.setCvar('g_stamina', 2)
            self.console.say('^7Stamina mode: ^3INFINITE')

    def cmd_paident(self, data, client=None, cmd=None):
        """
        <name> - show the ip and guid and authname of a player
        (You can safely use the command without the 'pa' at the beginning)
        """
        args = self._adminPlugin.parseUserCmd(data)
        if not args:
            cmd.sayLoudOrPM(client, 'Your id is ^2@%s' % client.id)
            return

        # args[0] is the player id
        sclient = self._adminPlugin.findClientPrompt(args[0], client)
        if not sclient:
            # a player matching the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        if client.maxLevel < self._full_ident_level:
            cmd.sayLoudOrPM(client, '%s ^4@%s ^2%s' % (self.console.formatTime(self.console.time()),
                                                       sclient.id, sclient.exactName))
        else:
            cmd.sayLoudOrPM(client, '%s ^4@%s ^2%s ^2%s ^7[^2%s^7] since ^2%s' % (
                self.console.formatTime(self.console.time()), sclient.id, sclient.exactName, sclient.ip, sclient.pbid,
                self.console.formatTime(sclient.timeAdd)))

    def cmd_pagear(self, data, client=None, cmd=None):
        """
        [<gear>] - set the allowed gear on the server
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data:
            self.printgear(client=client, cmd=cmd)
            # display help text
            client.message('^7Usage: ^3!^7pagear [+/-][%s]' % '|'.join(self._weapons.keys()))
            client.message('^7Load weapon groups: ^3!^7pagear [+/-][%s]' % '|'.join(self._weapon_groups.keys()))
            client.message('^7Load defaults: ^3!^7pagear [%s]' % '|'.join(self._gears.keys()))
            return

        def update_gear(gear_set, param_data):
            """
            update gear_set given the param_data

            @param gear_set: set of letters representing the g_gear cvar value
            @param param_data: !pagear command parameter representing a weapon/item name/preset/group
            """
            cleaned_data = re.sub(r'\s', "", param_data)

            # set a predefined gear
            if cleaned_data in self._gears.keys():
                gear_set.clear()
                gear_set.add(self._gears[cleaned_data])
                return

            # add a specific weapon to the current gear string
            if cleaned_data[:1] in ('+', '-'):
                opt = cleaned_data[:1]
                weapon_codes = self.get_weapon_code(cleaned_data[1:])

                if not weapon_codes:
                    client.message("could not recognize weapon/item %r" % cleaned_data[1:])
                    return

                for weapon_code in weapon_codes:
                    if opt == '+':
                        gear_set.discard(weapon_code)
                    if opt == '-':
                        gear_set.add(weapon_code)

        current_gear_set = set(self.console.getCvar('g_gear').getString())
        new_gear_set = set(current_gear_set)
        for m in re.finditer(r"(all|none|reset|[+-]\s*[\w.]+)", data.strip().lower()):
            update_gear(new_gear_set, m.group())

        if current_gear_set == new_gear_set:
            client.message('^7gear ^1not ^7changed')
            return

        new_gear_cvar = "".join(sorted(new_gear_set))
        self.console.setCvar('g_gear', new_gear_cvar)
        self.printgear(client=client, cmd=cmd, gearstr=new_gear_cvar)

    ####
    ## override iourt41 command since Urban Terror 4.2 now provides a /rcon swap command
    def cmd_paswap(self, data, client, cmd=None):
        """
        <player1> [player2] - Swap two teams for 2 clients. If player2 is not specified, the admin
        using the command is swapped with player1. Doesn't work with spectators (exception for calling admin).
        """
        # check the input
        args = self._adminPlugin.parseUserCmd(data)
        # check for input. If none, exist with a message.
        if args:
            # check if the first player exists. If none, exit.
            client1 = self._adminPlugin.findClientPrompt(args[0], client)
            if not client1:
                return
        else:
            client.message("Invalid parameters, try !help paswap")
            return

        # if the specified player doesn't exist, exit.
        if args[1] is not None:
            client2 = self._adminPlugin.findClientPrompt(args[1], client)
            if not client2:
                return
        else:
            client2 = client

        if client1.team == b3.TEAM_SPEC:
            client.message("%s is a spectator! - Can't be swapped" % client1.name)
            return

        if client2.team == b3.TEAM_SPEC:
            client.message("%s is a spectator! - Can't be swapped" % client2.name)
            return

        if client1.team == client2.team:
            client.message("%s and %s are on the same team! - Swapped them anyway :p" % (client1.name, client2.name))
            return

        # /rcon swap <clientA> <clientB>
        self.console.write('swap %s %s' % (client1.cid, client2.cid))

        # No need to send the message twice to the switching admin :-)

        if client1 != client:
            client1.message("^4You were swapped with %s by the admin" % client2.name)

        if client2 != client:
            client2.message("^4You were swapped with %s by the admin" % client1.name)

        client.message("^3Successfully swapped %s and %s" % (client1.name, client2.name))

    def cmd_pacaptain(self, data, client, cmd=None):
        """
        [<player>] - Set the given client as the captain for its team
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not self._matchmode:
            client.message("!pacaptain command is available only in match mode")
            return

        if not data:
            sclient = client
        else:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if not sclient:
                return

        if sclient.team == b3.TEAM_SPEC:
            client.message("%s is a spectator! - Can't set captain status" % sclient.name)
            return

        self.console.write("forcecaptain %s" % sclient.cid)

        # only give  notice if the client is not the admin who issued the command:
        # urban terror already display a server message when the captain flag is changed
        if sclient != client:
            team = "^1RED" if sclient.team == b3.TEAM_RED else "^4BLUE"
            sclient.message("^7You were set as captain for the %s ^7team by the Admin" % team)

    def cmd_pasub(self, data, client, cmd=None):
        """
        [<player>] - set the given client as a substitute for its team
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not self._matchmode:
            client.message("!pasub command is available only in match mode")
            return

        if not data:
            sclient = client
        else:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if not sclient:
                return

        if sclient.team == b3.TEAM_SPEC:
            client.message("%s is a spectator! - Can't set substitute status" % sclient.name)
            return

        self.console.write("forcesub %s" % sclient.cid)

        # only give  notice if the client is not the admin who issued the command:
        # urban terror already display a server message when the substitute flag is changed
        if sclient != client:
            team = "^1RED" if sclient.team == b3.TEAM_RED else "^4BLUE"
            sclient.message("^7You were set as substitute for the %s ^7team by the Admin" % team)

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def printgear(self, client, cmd, gearstr=None):
        """
        Print the current gear in the game chat
        """
        if not gearstr:
            # if not explicitly passed get it form the server
            gearstr = self.console.getCvar('g_gear').getString()

        lines = []
        for key in self._weapons.keys():
            lines.append('%s:%s' % (key, '^2ON' if self._weapons[key] not in gearstr else '^1OFF'))

        cmd.sayLoudOrPM(client, '^3current gear: ^7%s' % '^7, '.join(lines))

    def getTime(self):
        """ just to ease automated tests """
        return self.console.time()
    
    def get_weapon_code(self, name):
        """
        try its best to guess the weapon code given a name.
        If name is a group name, then return multiple weapon codes as a string
        """
        if name in self._weapon_groups.keys():
            return self._weapon_groups[name]
        name_tries = [name[:length] for length in (5, 4, 3, 2)]
        for _name in name_tries:
            if _name in self._weapons.keys():
                return self._weapons[_name]
        for _name in name_tries:
            if _name in self._weapon_aliases.keys():
                key = self._weapon_aliases[_name]
                return self._weapons[key]