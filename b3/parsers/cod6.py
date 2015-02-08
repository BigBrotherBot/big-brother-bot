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
# CHANGELOG
#
# 04/08/2014 - 0.7   - Fenix          - syntax cleanup
#                                     - fixed client retrieval in OnA()
# 30/07/2014 - 0.6.2 - Fenix          - fixes for the new getWrap implementation
# 10/05/2013 - 0.6.1 - 82ndab.Bravo17 - do not apply cod4 alterations to admin plugin
# 25/04/2011 - 0.6   - xlr8or         - action logging - get client by name
# 24/04/2011 - 0.5   - xlr8or         - disable action logging - game engine bug
# 18/03/2011 - 0.4   - Freelander     - fixed a typo causing permanent bans fail
# 24/01/2010 - 0.3   - xlr8or         - replaced _commands dict to fix broken ban command
# 09/10/2010 - 0.2   - jerbob92       - set sv_hostname at statup
# 02/10/2010 - 0.1   - NTAuthority    - parser created

__author__ = 'NTAuthority'
__version__ = '0.7'

import b3.parsers.cod4
import re


class Cod6Parser(b3.parsers.cod4.Cod4Parser):

    gameName = 'cod6'

    _guidLength = 16

    _commands = {
        'message': 'tell %(cid)s %(message)s',
        'say': 'say %(message)s',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'clientkick %(cid)s',
        'ban': 'clientkick %(cid)s',
        'unban': 'unbanuser %(name)s',
        'tempban': 'clientkick %(cid)s'
    }

    _regPlayer = re.compile(r'(?P<slot>[0-9]+)\s+'
                            r'(?P<score>[0-9-]+)\s+'
                            r'(?P<ping>[0-9]+)\s+'
                            r'(?P<guid>[a-z0-9]+)\s+'
                            r'(?P<name>.*?)\s+'
                            r'(?P<last>[0-9]+)\s+'
                            r'(?P<ip>[0-9.]+):'
                            r'(?P<port>[0-9-]+)', re.IGNORECASE)

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def startup(self):
        """
        Called after the parser is created before run().
        """
        b3.parsers.cod4.Cod4Parser.startup(self)
        try:
            self.game.sv_hostname = self.getCvar('sv_hostname').getString().rstrip('/')
            self.debug('sv_hostname: %s' % self.game.sv_hostname)
        except:
            self.game.sv_hostname = None
            self.warning('Could not query server for sv_hostname')

    def pluginsStarted(self):
        """
        Called after the parser loaded and started all plugins.
        """
        self.debug('Admin plugin not patched')
        
    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def OnA(self, action, data, match=None):
        client = self.clients.getByName(data)
        if not client:
            return None
        actiontype = match.group('type')
        self.verbose('on action: %s: %s' % (client.name, actiontype))
        return self.getEvent('EVT_CLIENT_ACTION', data=actiontype, client=client)