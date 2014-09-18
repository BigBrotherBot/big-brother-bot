#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# CHANGELOG:
#
# 02/05/2014 - 1.0 - Fenix - committed first built-in release
# 30/08/2014 - 1.1 - Fenix - syntax cleanup
# 18/09/2014 - 1.2 - Fenix - added command !cmdgrant: allow the execution of a command to a specific client
#                          - added command !cmdrevoke: revoke a previously given command grant
#                          - updated !cmdlevel and !cmdalias to use command.canUse() method to check if a given
#                            client has access to the command

__author__ = 'Fenix'
__version__ = '1.2'

import b3
import b3.plugin
import b3.plugins.admin
import b3.events
import new
import re
import os

from ConfigParser import ConfigParser
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError
from b3.config import XmlConfigParser
from b3.functions import getCmd
from xml.dom import minidom


class CmdmanagerPlugin(b3.plugin.Plugin):

    _adminPlugin = None

    _settings = {
        'update_config_file': True
    }

    _sql = {
        'mysql': {
            'upsert': """REPLACE INTO cmdgrants (id, commands) VALUES (?, ?);""",
            'select': """SELECT id, commands FROM cmdgrants WHERE id = ?""",
            'schema': """CREATE TABLE IF NOT EXISTS cmdgrants (
                             id int(11) NOT NULL,
                             commands blob NOT NULL,
                             PRIMARY KEY (id)
                         ) ENGINE=MyISAM DEFAULT CHARSET=utf8;""",
        },
        'sqlite': {
            'upsert': """INSERT OR REPLACE INTO cmdgrants (id, commands) VALUES (?, ?);""",
            'select': """SELECT id, commands FROM cmdgrants WHERE id = ?""",
            'schema': """CREATE TABLE IF NOT EXISTS cmdgrants (
                             id INTEGER PRIMARY KEY,
                             commands BLOB NOT NULL);""",
        }
    }

    ####################################################################################################################
    ##                                                                                                                ##
    ##   STARTUP                                                                                                      ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load the configuration file
        """
        try:
            self._settings['update_config_file'] = self.config.getboolean('settings', 'update_config_file')
            self.debug('loaded settings/update_config_file setting: %s' % self._settings['update_config_file'])
        except NoOptionError:
            self.warning('could not find settings/update_config_file in config file, '
                         'using default: %s' % self._settings['update_config_file'])
        except ValueError, e:
            self.error('could not load settings/update_config_file config value: %s' % e)
            self.debug('using default value (%s) for settings/update_config_file' %
                       self._settings['update_config_file'])

    def onStartup(self):
        """
        Initialize plugin settings
        """
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            self.error('could not start without admin plugin')
            return False

        # patch the admin module
        patch_admin_module(self._adminPlugin)

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

        # create database tables if needed
        tables = self.console.storage.getTables()
        if not 'cmdgrants' in tables:
            self.debug('creating database tables...')
            protocol = self.console.storage.dsnDict['protocol']
            self.console.storage.query(self._sql[protocol]['schema'])

        # register the events needed
        self.registerEvent(self.console.getEventID('EVT_CLIENT_CONNECT'), self.onConnect)

        # notice plugin started
        self.debug('plugin started')

    ####################################################################################################################
    ##                                                                                                                ##
    ##   HANDLE EVENTS                                                                                                ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onConnect(self, event):
        """
        Handle EVT_CLIENT_CONNECT events
        :param event: The Event to be handled
        """
        client = event.client
        self.debug('checking command grants for client @%s...' % client.id)
        cursor = self.console.storage.query(self._sql[self.console.storage.dsnDict['protocol']]['select'], (client.id,))
        if not cursor or cursor.EOF:
            self.debug('no command grant found for client @%s' % client.id)
            return

        r = cursor.getRow()
        cmdgrant_set = eval(r['commands'])
        setattr(client, 'cmdgrant_set', cmdgrant_set)
        self.debug('retrieved command grants for client @%s from the storage: %r' % (client.id, cmdgrant_set))

    ####################################################################################################################
    ##                                                                                                                ##
    ##   OTHER METHODS                                                                                                ##
    ##                                                                                                                ##
    ####################################################################################################################

    def command_name_sanitize(self, name):
        """
        Sanitize the name of a command.
        :param name: The command name to sanitize
        """
        name = name.lower().strip()
        name = name.replace(self._adminPlugin.cmdPrefix, '')
        name = name.replace(self._adminPlugin.cmdPrefixLoud, '')
        name = name.replace(self._adminPlugin.cmdPrefixBig, '')
        name = name.replace(self._adminPlugin.cmdPrefixPrivate, '')
        return name

    @staticmethod
    def _prettyxml(xml):
        """
        Return a correctly formatted XML document
        """
        return '\n'.join([x for x in xml.toprettyxml(encoding='UTF-8', indent='    ').split('\n') if x.strip()])

    @staticmethod
    def get_plugin_name(plugin):
        """
        Return a readable plugin name given it's class
        """
        name = plugin.__class__.__name__.lower()
        return name.replace('plugin', '')

    def get_command(self, name):
        """
        Return a Command object given its name
        :param name: The command name
        """
        try:
            # try to get the command from the dict
            return self._adminPlugin._commands[name]
        except KeyError:
            # return none if the command doesn't exists
            return None

    def get_command_level_string(self, command):
        """
        Return a string representation of the given command level
        :param command: The command object instance
        """
        mingroup = self.console.getGroup(command.level[0])
        message = '^2%s' % mingroup.keyword

        # exclude superadmin level
        if command.level[0] != command.level[1] < 100:
            maxgroup = self.console.getGroup(command.level[1])
            message = '%s^3-^2%s' % (message, maxgroup.keyword)

        return message

    def write_ini_config_file(self, command, data, client):
        """
        Write the new command configuration in the plugin configuration file
        """
        try:

            # read the config file
            config = ConfigParser()
            config.read(command.plugin.config.fileName)

            # if there is no commands section
            if not config.has_section('commands'):
                raise NoSectionError('could not find <commands> section in '
                                     'plugin <%s> config file' % data['plugin_name'])

            # remove the old entry
            found = False
            for temp in config.options('commands'):
                search = temp.split('-')[0]
                if search == command.command:
                    config.remove_option('commands', temp)
                    found = True

            # set the new command option value
            config.set('commands', data['command_name'], data['command_level'])
            self.debug('%s command <%s> in plugin <%s> config file' % ('updated' if found else 'created new entry for',
                                                                       command.command, data['plugin_name']))

            # write the updated configuration file
            with open(command.plugin.config.fileName, 'wb') as configfile:
                config.write(configfile)

        except (IOError, NoSectionError), e:
            self.warning('could not change plugin <%s> config file: %s' % (data['plugin_name'], e))
            client.message('^7could not change plugin ^1%s ^7config file' % data['plugin_name'])

    def write_xml_config_file(self, command, data, client):
        """
        Write the new command configuration in the plugin configuration file
        """
        try:

            document = minidom.parse(command.plugin.config.fileName)
            settings = document.getElementsByTagName('settings')

            changed = False
            for setting in settings:
                if setting.getAttribute('name') == 'commands':
                    sets = setting.getElementsByTagName('set')
                    for node in sets:
                        search = node.getAttribute('name').split('-')[0]
                        if search == command.command:
                            for v in node.childNodes:
                                if v.nodeType == v.TEXT_NODE:
                                    v.data = data['command_level']
                                    node.setAttribute('name', data['command_name'])
                                    self.debug('updated command <%s> in plugin <%s> config '
                                               'file' % (command.command, data['plugin_name']))
                                    changed = True
                                    break

                            if changed:
                                break

                    if not changed:
                        # there is no configuration value for the given command
                        # so create a new node in the command section
                        child = document.createElement('set')
                        child.setAttribute('name', data['command_name'])
                        child.appendChild(document.createTextNode(data['command_level']))
                        setting.appendChild(child)
                        self.debug('created new entry for command <%s> in <%s> plugin config '
                                   'file' % (data['command_name'], data['plugin_name']))
                        changed = True
                        break

            if not changed:
                raise NoSectionError('could not find <commands> section in '
                                     'plugin <%s> config file' % data['plugin_name'])

            # update the configuration file
            with open(command.plugin.config.fileName, 'w') as f:
                f.write(self._prettyxml(document))

        except (AttributeError, TypeError, IOError, NoSectionError), e:
            self.warning('could not change plugin <%s> configuration file: %s' % (data['plugin_name'], e))
            client.message('^7could not change ^1%s ^7plugin config file' % data['plugin_name'])

    def write_config_file(self, command, client):
        """
        Helper function which demands the config file writing
        to other methods according to the config file format
        """
        plugin = command.plugin
        plugin_name = self.get_plugin_name(plugin)
        if not plugin.requiresConfigFile:
            self.debug('could not change %s plugin configuration file: no configuration file specified' % plugin_name)
            return

        if not plugin.config.fileName or not os.path.isfile(plugin.config.fileName):
            client.message('^7could not open plugin ^1%s ^7config file' % plugin_name)
            self.warning('could not open %s plugin configuration file: %s' % (plugin_name, plugin.config.fileName))
            return

        # the command name
        command_name = command.command
        if command.alias and command.alias != command.command:
            command_name = '%s-%s' % (command.command, command.alias)

        # the command level
        mingroup = self.console.getGroup(command.level[0])
        command_level = '%s' % mingroup.keyword
        if command.level[1] < 100:
            maxgroup = self.console.getGroup(command.level[1])
            command_level = '%s-%s' % (mingroup.keyword, maxgroup.keyword)

        # group necessary data
        data = {
            'command_name': command_name,
            'command_level': command_level,
            'plugin_name': plugin_name
        }

        # write in the plugin specific configuration file
        func = getattr(self, 'write_%s_config_file' % ('xml' if isinstance(plugin.config, XmlConfigParser) else 'ini'))
        func(command, data, client)

    def set_command_level(self, command, level, client, cmd):
        """
        Set the level of a command.
        :param command: The command object
        :param level: The new level for the command
        :param client: The client who executed the command
        :param cmd: The instance of the launched command
        """
        # check that the format given matches our constraint
        r = re.compile(r'''^(?P<minlevel>\w+)-*(?P<maxlevel>\w*)$''')
        m = r.match(level)
        if not m:
            client.message('^7invalid level format specified: ^1%s' % level)
            return

        # get the minlevel
        minlevel = m.group('minlevel')

        try:
            # get the group corresponsing to minlevel
            mingroup = self.console.getGroup(minlevel)
        except KeyError:
            client.message('^7invalid level specified: ^1%s' % minlevel)
            return

        # get the maxiumum required level
        maxlevel = m.group('maxlevel')
        if len(maxlevel):

            try:
                # check given maxlevel to be valid. since this value is optional we'll put checks
                # here below, so only when the value we are checking has been entered by the user
                maxgroup = self.console.getGroup(maxlevel)
            except KeyError:
                client.message('^7invalid level specified: ^1%s' % maxlevel)
                return

            if mingroup.level > maxgroup.level:
                client.message('^7invalid level: ^1%s ^7is greater than ^1%s' % (mingroup.keyword, maxgroup.keyword))
                return
        else:
            # maxlevel not specified => fallback to superadmin
            maxgroup = self.console.getGroup('superadmin')

        # change the command inside the commands dict()
        command.level = (mingroup.level, maxgroup.level)
        self.debug('command <%s> level changed to <%s-%s>' % (command.command, mingroup.keyword, maxgroup.keyword))
        cmd.sayLoudOrPM(client, '^7command ^3%s^4%s ^7level changed: %s' % (self._adminPlugin.cmdPrefix,
                                                                            command.command,
                                                                            self.get_command_level_string(command)))
        # change the plugin configuration file
        if self._settings['update_config_file']:
            self.write_config_file(command, client)

    def set_command_alias(self, command, alias, client, cmd):
        """
        Set the alias of a command.
        :param command: The command object
        :param alias: The new alias for the command
        :param client: The client who executed the command
        :param cmd: The instance of the launched command
        """
        # check that the format given matches our constraint
        alias = self.command_name_sanitize(alias)
        if not alias:
            client.message('^7invalid alias specified')
            return

        # check if the given alias is not
        # already an alias of another command
        tempcommand = self.get_command(alias)
        if tempcommand:
            client.message('^7command ^3%s^1%s ^7is already in use' % (self._adminPlugin.cmdPrefix, alias))
            return

        found = False
        if command.alias:
            found = True

        # change the alias
        command.alias = alias
        self._adminPlugin._commands[alias] = command
        self.debug('%s alias <%s> for command <%s>' % ('added' if not found else 'updated', alias, command.command))
        cmd.sayLoudOrPM(client, '^7%s alias for command ^3%s^4%s^7: ^3%s^4%s' % ('added' if not found else 'updated',
                                                                                 self._adminPlugin.cmdPrefix,
                                                                                 command.command,
                                                                                 self._adminPlugin.cmdPrefix,
                                                                                 command.alias))
        # change the plugin configuration file
        if self._settings['update_config_file']:
            self.write_config_file(command, client)

    def save_command_grants(self, client):
        """
        Save client grants in the storage
        :param client: The client whose command grants needs to be stored
        """
        if not hasattr(client, 'cmdgrant_set'):
            self.debug('not storing command grants for client @%s: no command grant found in client object' % client.id)
            return

        try:
            cmdgrant_set = getattr(client, 'cmdgrant_set')
            protocol = self.console.storage.dsnDict['protocol']
            self.console.storage.query(self._sql[protocol]['upsert'], (client.id, repr(cmdgrant_set)))
            self.debug('stored command grants for client @%s' % client.id)
        except Exception, e:
            self.error('could not store command grants for client @%s: %s' % (client.id, e))

    ####################################################################################################################
    ##                                                                                                                ##
    ##   COMMANDS                                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    def cmd_cmdlevel(self, data, client, cmd=None):
        """
        <command> [<level>] - get/set the level of a command
        """
        r = re.compile(r'''^(?P<command>[!]?\w+)\s*(?P<level>.*)$''')
        m = r.match(data)
        if not m:
            client.message('invalid data, try ^3!^7help cmdlevel')
            return

        # get the command
        px = self._adminPlugin.cmdPrefix
        name = self.command_name_sanitize(m.group('command'))
        command = self.get_command(name)
        if not command:
            client.message('^7could not find command ^3%s^1%s' % (px, name))
            return

        # checking if the guy can access the command
        if not command.canUse(client):
            client.message('^7no sufficient access to ^3%s^1%s ^7command' % (px, name))
            return

        # if no new level given
        if not m.group('level'):
            # if no new level is specified display the current one
            commandlevel = self.get_command_level_string(command)
            cmd.sayLoudOrPM(client, '^7command ^3%s^4%s ^7level: %s' % (px, name, commandlevel))
            return

        # change the command level with the new given value
        self.set_command_level(command, m.group('level'), client, cmd)

    def cmd_cmdalias(self, data, client, cmd=None):
        """
        <command> [<alias>] - get/set the alias of a command
        """
        r = re.compile(r'''^(?P<command>[!]?\w+)\s*(?P<alias>[!]?\w*)$''')
        m = r.match(data)
        if not m:
            client.message('invalid data, try ^3!^7help cmdalias')
            return

        # get the command
        px = self._adminPlugin.cmdPrefix
        name = self.command_name_sanitize(m.group('command'))
        command = self.get_command(name)
        if not command:
            client.message('^7could not find command ^3%s^1%s' % (px, name))
            return

        # checking if the guy can access the command
        if not command.canUse(client):
            client.message('^7no sufficient access to ^3%s^1%s ^7command' % (px, name))
            return

        # if no new level is given
        if not m.group('alias'):
            if not command.alias:
                # inform that no alias is set for this command
                cmd.sayLoudOrPM(client, '^7command ^3%s^1%s ^7has not alias set' % (px, name))
                return

            # print the command alias
            cmd.sayLoudOrPM(client, '^7command ^3%s^4%s ^7alias: ^3%s^4%s' % (px, name, px, command.alias))
            return

        # change the command level with the new given value
        self.set_command_alias(command, m.group('alias'), client, cmd)

    def cmd_cmdgrant(self, data, client, cmd=None):
        """
        <client> <command> - grant the usage of a command to a specific client
        """
        r = re.compile(r'''^(?P<client>[!]?\w+)\s*(?P<command>\w+)$''')
        m = r.match(data)
        if not m:
            client.message('invalid data, try ^3!^7help cmdgrant')
            return

        # get the client
        sclient = self._adminPlugin.findClientPrompt(m.group('client'), client)
        if not sclient:
            return

        # get the command
        px = self._adminPlugin.cmdPrefix
        name = self.command_name_sanitize(m.group('command'))
        command = self.get_command(name)
        if not command:
            client.message('^7could not find command ^3%s^1%s' % (px, name))
            return

        # checking if the guy can access the command
        if client.maxLevel < command.level[0]:
            client.message('^7no sufficient access to ^3%s^1%s ^7command' % (px, name))
            return

        if command.canUse(sclient):
            client.message('^7%s can already use command ^3%s^7%s' % (sclient.name, px, command.command))
            return

        # get the commands this client has a grant for: this will create the set if necessary
        cmdgrant_set = getattr(sclient, 'cmdgrant_set', set())
        cmdgrant_set.add(command.command)
        setattr(sclient, 'cmdgrant_set', cmdgrant_set)

        # save changes in the storage
        self.save_command_grants(sclient)

        # inform the client that the grant has been set
        cmd.sayLoudOrPM(client, '^7%s ^7has now a ^2grant ^7for command %s%s' % (sclient.name, px, command.command))

    def cmd_cmdrevoke(self, data, client, cmd=None):
        """
        <client> <command> - revoke a previously given grant for the given command
        """
        r = re.compile(r'''^(?P<client>[!]?\w+)\s*(?P<command>\w+)$''')
        m = r.match(data)
        if not m:
            client.message('invalid data, try ^3!^7help cmdrevoke')
            return

        # get the client
        sclient = self._adminPlugin.findClientPrompt(m.group('client'), client)
        if not sclient:
            return

        # get the command
        px = self._adminPlugin.cmdPrefix
        name = self.command_name_sanitize(m.group('command'))
        command = self.get_command(name)
        if not command:
            client.message('^7could not find command ^3%s^1%s' % (px, name))
            return

        # checking if the guy can access the command
        if client.maxLevel < command.level[0]:
            client.message('^7no sufficient access to ^3%s^1%s ^7command' % (px, name))
            return

        if not command.canUse(sclient):
            client.message('^7%s is already not able to use ^3%s^7%s' % (sclient.name, px, command.command))
            return

        try:

            # get the commands this client has a grant for: this will create the set if necessary
            cmdgrant_set = getattr(sclient, 'cmdgrant_set', set())
            cmdgrant_set.remove(command.command)
            setattr(sclient, 'cmdgrant_set', cmdgrant_set)

            # save changes in the storage
            self.save_command_grants(sclient)

            # inform the client that the grant has been removed
            cmd.sayLoudOrPM(client, '^7%s\'s ^1grant ^7for command %s%s ^7has been removed' % (sclient.name, px, command.command))
            if command.canUse(sclient):
                cmd.sayLoudOrPM(client, '^7but his group level is high enough to access the command')

        except KeyError:
            # there was no grant after all
            cmd.sayLoudOrPM(client, '^7%s has no grant for command %s%s' % (sclient.name, px, command.command))

########################################################################################################################
##                                                                                                                    ##
##   APPLY PATCHES                                                                                                    ##
##                                                                                                                    ##
########################################################################################################################

def patch_admin_module(adminPlugin):
    """
    Apply patches to the admin module.
    :param adminPlugin: The admin plugin object instance
    """
    def new_canUse(self, client):
        """
        Check whether a client can use such command
        :param client: The client on who to perform the check
        """
        if self.level is None:
            # command level is not set so don't execute
            return False
        elif self.level[0] <= int(client.maxLevel) <= self.level[1]:
            # check whether the client has the necessary level
            return True
        else:
            # check for a specific grant for this command
            return self.command in getattr(client, 'cmdgrant_set', set())

    # patch the Command class for future object instances
    b3.plugins.admin.Command.canUse = new_canUse

    # patch all the Command objects already instantiated
    for key in adminPlugin._commands:
        adminPlugin._commands[key].canUse = new.instancemethod(new_canUse, adminPlugin._commands[key])