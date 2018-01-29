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