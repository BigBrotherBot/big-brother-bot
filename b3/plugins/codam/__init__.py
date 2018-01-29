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

__author__  = 'ThorN'
__version__ = '0.0.2'

import b3, re
import b3.plugin


class CodamPlugin(b3.plugin.Plugin):

    _adminPlugin = None

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def startup(self):
        """
        Plugin startup.
        """
        self._adminPlugin = self.console.getPlugin('admin')
        if self._adminPlugin:
            if 'commands' in self.config.sections():
                for cmd in self.config.options('commands'):
                    if cmd == 'codam':
                        level = self.config.get('commands', 'codam')
                        self._adminPlugin.registerCommand(self, 'codam', level, self.cmd_codam)
                    else:
                        level = self.config.get('commands', cmd)
                        self._adminPlugin.registerCommand(self, 'c' + cmd, level, self.cmd_command)

            if 'user_commands' in self.config.sections():
                for cmd in self.config.options('user_commands'):
                    level = self.config.get('user_commands', cmd)
                    self._adminPlugin.registerCommand(self, 'c' + cmd, level, self.cmd_user_command)

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_codam(self, data, client, cmd=None):
        """
        <command> - CoDAM command
        """
        if not data:
            client.message('^7Missing data, try !help codam')
            return
        self.console.write('command "%s"' % data)

    def cmd_user_command(self, data, client, cmd=None):
        """
        <client> [<data>] - CoDAM user command
        """
        m = re.match('^([^ ]{2,}|[0-9]+) ?(.*)$', data)
        if not m:
            client.message('^7Invalid parameters')
            return

        cid = m.group(1)
        parm = m.group(2)

        sclient = self._adminPlugin.findClientPrompt(cid, client)
        if sclient:
            self.cmd_codam('%s %s %s' % (cmd.command[1:], parm, sclient.cid), client)

    def cmd_command(self, data, client, cmd=None):
        """
        - CoDAM command
        """
        self.cmd_codam('%s %s' % (cmd.command, data), client)