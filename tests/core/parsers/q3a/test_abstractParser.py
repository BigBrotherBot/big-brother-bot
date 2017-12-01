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

from b3.parsers.q3a.abstractParser import AbstractParser
from mock import Mock
import unittest2 as unittest

class Test(unittest.TestCase):


    def test_getCvar(self):
        # prepare mocks
        mock_parser = Mock(spec=AbstractParser)
        mock_parser._reCvarName = AbstractParser._reCvarName
        mock_parser._reCvar = AbstractParser._reCvar
        mock_parser.getCvar = AbstractParser.getCvar
        
        def assertGetCvar(cvar_name, gameserver_response, expected_response):
            mock_parser.write = Mock(return_value=gameserver_response)
            cvar = mock_parser.getCvar(mock_parser, cvar_name)
            if cvar is None:
                self.assertEqual(expected_response, None)
            else:
                self.assertEqual(expected_response, (cvar.name, cvar.value, cvar.default))
        
        assertGetCvar('g_password', '"g_password" is:"^7" default:"scrim^7"', ("g_password", '', "scrim"))
        assertGetCvar('g_password', '"g_password" is:"^7" default:"^7"', ("g_password", '', ""))
        assertGetCvar('g_password', '"g_password" is:"test^7" default:"^7"', ("g_password", 'test', ""))
        assertGetCvar('g_password', 'whatever', None)
        assertGetCvar('g_password', '"g_password" is:"^7"', ("g_password", '', None))
        assertGetCvar('sv_maxclients', '"sv_maxclients" is:"16^7" default:"8^7"', ("sv_maxclients", '16', '8'))
        assertGetCvar('g_maxGameClients', '"g_maxGameClients" is:"0^7", the default', ("g_maxGameClients", '0', '0'))
        assertGetCvar('mapname', '"mapname" is:"ut4_abbey^7"', ("mapname", 'ut4_abbey', None))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()