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

from functools import partial
from b3.functions import getStuffSoundingLike
from b3.plugin import Plugin

__version__ = '1.2'
__author__ = 'Courgette'


class CustomcommandsPlugin(Plugin):

    def __init__(self, console, config=None):
        """
        Build the plugin instance
        :param console: The console instance
        :param config: The plugin configuration file instance
        """
        self._adminPlugin = None
        self._re_valid_command_name = re.compile(r"^[a-z][\w]+$", re.IGNORECASE)
        self._re_argument_placeholder = re.compile(r"<ARG(?::(?P<type>[A-Z_]+)(?::(?P<property>.*?))?)?>")
        Plugin.__init__(self, console, config)

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN INTERFACE IMPLEMENTATION                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        This is called after loadConfig().
        Any plugin private variables loaded from the config need to be reset here.
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            raise AttributeError('could not find admin plugin')

        # unregister eventual previously registered commands
        registered_cmd_names = [cmd_name for cmd_name, cmd in self._adminPlugin._commands.items() if cmd.plugin is self]
        for cmd_name in registered_cmd_names:
            self._adminPlugin.unregisterCommand(cmd_name)

        # register our custom commands
        for group_name in ("guest", "user", "regular", "mod", "admin", "fulladmin", "senioradmin", "superadmin"):
            if not self.config.has_section("%s commands" % group_name):
                self.debug("no section [%s commands] found in config file" % group_name)
            else:
                self._load_conf_commands_for_group(group_name)

    def onStartup(self):
        """
        Startup the plugin
        """
        self.registerEvent('EVT_CLIENT_KILL', self.onKill)
        self.registerEvent('EVT_CLIENT_KILL_TEAM', self.onKill)

    def onKill(self, event):
        """
        Handle intercepted events
        """
        killer = event.client
        victim = event.target
        killer.setvar(self, 'LAST_VICTIM', victim)
        victim.setvar(self, 'LAST_KILLER', killer)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def _load_conf_commands_for_group(self, b3_group_name):
        """
        load custom commands defined in the config file for a given b3 group
        """
        self.debug("loading custom commands for group %s" % b3_group_name)
        for command_name in self.config.options("%s commands" % b3_group_name):
            self.debug("loading command %r" % command_name)

            try:
                self._validate_cmd_name(command_name)
                self._validate_cmd_name_not_already_registered(command_name)
            except ValueError, err:
                self.error(str(err))
                continue

            command_template = self.config.get("%s commands" % b3_group_name, command_name)

            try:
                self._validate_cmd_template(command_template)
            except ValueError, err:
                self.error("command template invalid for %r: %s" % (command_name, err))
                continue

            self._create_command(b3_group_name, command_name.lower(), command_template)

    def _validate_cmd_name(self, command_name):
        """
        Makes sure a command name is correct.
        Raise ValueError if invalid.
        """
        assert command_name is not None
        assert command_name.strip() != ''
        if not self._re_valid_command_name.match(command_name):
            raise ValueError("command name %r is invalid: command names must start by a letter, must be at "
                             "least two characters long and have no space in them" % command_name)

    def _validate_cmd_name_not_already_registered(self, command_name):
        """
        Make sure a command has not been already registered by another plugin.
        Raise ValueError if it has been already registered.
        """
        cmd = self._adminPlugin._commands.get(command_name.lower(), None)
        if cmd is not None:
            raise ValueError("a command with name %r is already registered by plugin %s" %
                             (command_name, cmd.plugin.__class__.__name__[:-6]))

    def _validate_cmd_template(self, template):
        """
        Makes sure a command template is correct.
        Raise ValueError if invalid.
        """
        assert template is not None
        if template.strip() == '':
            raise ValueError("command template cannot be blank")
        if template.count("<ARG:") > 1:
            raise ValueError("command template cannot have more than one 'ARG' placeholder")

    def _create_command(self, required_group, command_name, command_template):
        func = partial(self._custom_command_implementation, command_template)
        func.__name__ = command_name
        func.__doc__ = ""
        m = self._re_argument_placeholder.search(command_template)
        if m:
            arg_type = m.group('type')
            if arg_type is None:
                func.__doc__ += "<text>"
            elif arg_type == 'OPT':
                func.__doc__ += "[<text>]"
            elif arg_type == 'FIND_PLAYER':
                func.__doc__ += "<player>"
            elif arg_type == 'FIND_MAP':
                func.__doc__ += "<map>"
        if self.config.has_option('help', command_name):
            func.__doc__ += (" - " + self.config.get('help', command_name))
        else:
            self.verbose("no help found for command %r" % command_name)
        self._adminPlugin.registerCommand(self, command_name, required_group, func)

    def _custom_command_implementation(self, command_template, data, client, cmd):
        """
        render the rcon command given current context and command_template
        :command_template: the template to use to render the rcon command
        :data: the data passed as a parameter of the command
        :client: the Client object representing the player who is issuing the command
        :cmd: the Command object for this command implentation
        """
        try:
            rcon_command = self._render_cmd_template(command_template, data, client)
        except ValueError, err:
            client.message("Error: %s" % err)
        else:
            if rcon_command:
                self.console.write(rcon_command)

    def _render_cmd_template(self, command_template, data, client):
        command = command_template

        # <ARG>
        if "<ARG>" in command:
            if not data:
                raise ValueError("missing parameter")
            command = command.replace("<ARG>", data)

        # <ARG:OPT:{TEXT}>
        _re_arg_opt = re.compile("<ARG:OPT:([^>]*)>")
        m = _re_arg_opt.search(command)
        if m:
            replacement = data or m.group(1)
            command = _re_arg_opt.sub(replacement, command)

        # <ARG:FIND_MAP>
        if "<ARG:FIND_MAP>" in command:
            if not data:
                raise ValueError("missing parameter")
            result = self.getMapsSoundingLike(data)
            if isinstance(result, basestring):
                command = command.replace("<ARG:FIND_MAP>", result)
            elif isinstance(result, list):
                raise ValueError('do you mean : %s ?' % ', '.join(result))
            else:
                raise ValueError('^7cannot find any map like [^4%s^7].' % data)

        # <ARG:FIND_PLAYER:*>
        _re_find_player = re.compile("<ARG:FIND_PLAYER:(PID|PBID|GUID|NAME|EXACTNAME|B3ID)>")
        m = _re_find_player.search(command)
        if m:
            if not data:
                raise ValueError("missing parameter")
            target_client = self._adminPlugin.findClientPrompt(data, client)
            if target_client:
                if m.group(1) == 'PID':
                    replacement = target_client.cid
                elif m.group(1) == 'PBID':
                    replacement = target_client.pbid
                elif m.group(1) == 'GUID':
                    replacement = target_client.guid
                elif m.group(1) == 'NAME':
                    replacement = target_client.name
                elif m.group(1) == 'EXACTNAME':
                    replacement = target_client.exactName
                elif m.group(1) == 'B3ID':
                    replacement = "@%s" % target_client.id
                else:
                    raise AssertionError("unsupported placeholder %r" % m.group(0))
                command = _re_find_player.sub(replacement, command)
            else:
                return

        # <PLAYER:*>
        command = command.replace("<PLAYER:PID>", client.cid)
        command = command.replace("<PLAYER:PBID>", client.pbid)
        command = command.replace("<PLAYER:GUID>", client.guid)
        command = command.replace("<PLAYER:NAME>", client.name)
        command = command.replace("<PLAYER:EXACTNAME>", client.exactName)
        command = command.replace("<PLAYER:B3ID>", "@%s" % client.id)

        # <LAST_KILLER:*>
        _re_last_killer = re.compile("<LAST_KILLER:(PID|PBID|GUID|NAME|EXACTNAME|B3ID)>")
        m = _re_last_killer.search(command)
        if m:
            killer = client.var(self, 'LAST_KILLER', None).value
            if killer is None:
                raise ValueError("your last killer is unknown")
            if m.group(1) == 'PID':
                replacement = killer.cid
            elif m.group(1) == 'PBID':
                replacement = killer.pbid
            elif m.group(1) == 'GUID':
                replacement = killer.guid
            elif m.group(1) == 'NAME':
                replacement = killer.name
            elif m.group(1) == 'EXACTNAME':
                replacement = killer.exactName
            elif m.group(1) == 'B3ID':
                replacement = "@%s" % killer.id
            else:
                raise AssertionError("unsupported placeholder %r" % m.group(0))
            command = _re_last_killer.sub(replacement, command)

        # <LAST_VICTIM:*>
        _re_last_victim = re.compile("<LAST_VICTIM:(PID|PBID|GUID|NAME|EXACTNAME|B3ID)>")
        m = _re_last_victim.search(command)
        if m:
            victim = client.var(self, 'LAST_VICTIM', None).value
            if victim is None:
                raise ValueError("your last victim is unknown")
            if m.group(1) == 'PID':
                replacement = victim.cid
            elif m.group(1) == 'PBID':
                replacement = victim.pbid
            elif m.group(1) == 'GUID':
                replacement = victim.guid
            elif m.group(1) == 'NAME':
                replacement = victim.name
            elif m.group(1) == 'EXACTNAME':
                replacement = victim.exactName
            elif m.group(1) == 'B3ID':
                replacement = "@%s" % victim.id
            else:
                raise AssertionError("unsupported placeholder %r" % m.group(0))
            command = _re_last_victim.sub(replacement, command)

        # <PLAYER:ADMINGROUP_*>
        if "<PLAYER:ADMINGROUP_SHORT>" in command:
            command = command.replace("<PLAYER:ADMINGROUP_SHORT>", client.maxGroup.keyword)
        if "<PLAYER:ADMINGROUP_LONG>" in command:
            command = command.replace("<PLAYER:ADMINGROUP_LONG>", client.maxGroup.name)
        if "<PLAYER:ADMINGROUP_LEVEL>" in command:
            command = command.replace("<PLAYER:ADMINGROUP_LEVEL>", str(client.maxGroup.level))

        return command.strip()

    def getMapsSoundingLike(self, mapname):
        """ return a valid mapname.
        If no exact match is found, then return close candidates as a list
        """
        wanted_map = mapname.lower()
        supportedMaps = [x.lower() for x in self.console.getMaps()]
        if wanted_map in supportedMaps:
            return wanted_map

        matches = [match for match in getStuffSoundingLike(wanted_map, supportedMaps)]
        if len(matches) == 1:
            # one match, get the map id
            return matches[0]
        else:
            # multiple matches, provide suggestions
            return matches