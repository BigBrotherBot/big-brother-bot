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

import b3
import b3.clients
import unittest2 as unittest

from b3.parsers.homefront import HomefrontParser
from mock import Mock, sentinel

 
class Test_HomefrontParser(unittest.TestCase):

    def setUp(self):
        # prepare mocks
        self.mock_parser = Mock(spec=HomefrontParser)
        self.mock_parser._reSteamId64 = HomefrontParser._reSteamId64
        self.mock_parser.onServerKill = HomefrontParser.onServerKill

        self.courgette = Mock(spec=b3.clients.Client, name="courgette")
        self.freelander = Mock(spec=b3.clients.Client, name="freelander")
        
        def getClient(name):
            if name == 'courgette': return self.courgette
            elif name == 'Freelander': return self.freelander
            else: return Mock(spec=b3.clients.Client)
        self.mock_parser.getClient = getClient

        def getByGUID(guid):
            if guid == '12311111111111111': return self.courgette
            elif guid == '12300000000000000': return self.freelander
            else: return Mock(spec=b3.clients.Client)
        self.mock_parser.clients.getByGUID = getByGUID


    def tearDown(self):
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False


    def test_unmeaningful_data(self):
        self.assertIsNone(self.mock_parser.onServerKill(self.mock_parser, "qsdf"))


    def test_teamkill_with_names(self):
        self.mock_parser.reset_mock()
        self.courgette.team = self.freelander.team = sentinel.DEFAULT
        self.mock_parser.onServerKill(self.mock_parser, "courgette EXP_Frag Freelander")
        self.assertTrue(self.mock_parser.getEvent.called)
        getEvent_args = self.mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_KILL_TEAM', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(self.courgette, getEvent_args[2])
        self.assertEqual(self.freelander, getEvent_args[3])

    def test_teamkill_with_steamid(self):
        self.mock_parser.reset_mock()
        self.courgette.team = self.freelander.team = sentinel.DEFAULT
        self.mock_parser.onServerKill(self.mock_parser, "12311111111111111 EXP_Frag 12300000000000000")
        self.assertTrue(self.mock_parser.getEvent.called)
        getEvent_args = self.mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_KILL_TEAM', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(self.courgette, getEvent_args[2])
        self.assertEqual(self.freelander, getEvent_args[3])


    def test_kill_with_names(self):
        self.mock_parser.reset_mock()
        self.mock_parser.onServerKill(self.mock_parser, "courgette EXP_Frag Freelander")
        self.assertTrue(self.mock_parser.getEvent.called)
        getEvent_args = self.mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_KILL', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(self.courgette, getEvent_args[2])
        self.assertEqual(self.freelander, getEvent_args[3])

    def test_kill_with_steamid(self):
        self.mock_parser.reset_mock()
        self.mock_parser.onServerKill(self.mock_parser, "12311111111111111 EXP_Frag 12300000000000000")
        self.assertTrue(self.mock_parser.getEvent.called)
        getEvent_args = self.mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_KILL', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(self.courgette, getEvent_args[2])
        self.assertEqual(self.freelander, getEvent_args[3])


    def test_suicide_with_names(self):
        self.mock_parser.reset_mock()
        self.mock_parser.onServerKill(self.mock_parser, "courgette EXP_Frag courgette")
        self.assertTrue(self.mock_parser.getEvent.called)
        getEvent_args = self.mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_SUICIDE', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(self.courgette, getEvent_args[2])
        self.assertEqual(self.courgette, getEvent_args[3])

    def test_suicide_with_steamid(self):
        self.mock_parser.reset_mock()
        self.mock_parser.onServerKill(self.mock_parser, "12311111111111111 EXP_Frag 12311111111111111")
        self.assertTrue(self.mock_parser.getEvent.called)
        getEvent_args = self.mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_SUICIDE', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(self.courgette, getEvent_args[2])
        self.assertEqual(self.courgette, getEvent_args[3])
        
        

if __name__ == '__main__':
    unittest.main()