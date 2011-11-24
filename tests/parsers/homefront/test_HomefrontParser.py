#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette
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
from b3.parsers.homefront import HomefrontParser
from mock import Mock, sentinel
import b3
import unittest

 
class Test_HomefrontParser(unittest.TestCase):

    def test_onServerKill(self):
        # prepare mocks
        mock_parser = Mock(spec=HomefrontParser)
        mock_parser._reSteamId64 = HomefrontParser._reSteamId64
        mock_parser.onServerKill = HomefrontParser.onServerKill
        
        courgette = Mock(spec=b3.clients.Client, name="courgette")
        freelander = Mock(spec=b3.clients.Client, name="freelander")
        
        def getClient(name):
            if name == 'courgette': return courgette
            elif name == 'Freelander': return freelander
            else: return Mock(spec=b3.clients.Client)
        mock_parser.getClient = getClient

        def getByGUID(guid):
            if guid == '12311111111111111': return courgette
            elif guid == '12300000000000000': return freelander
            else: return Mock(spec=b3.clients.Client)
        mock_parser.clients.getByGUID = getByGUID


        # test unmeaningful data
        self.assertIsNone(mock_parser.onServerKill(mock_parser, "qsdf"))
        
        
        # test teamkill with names
        mock_parser.reset_mock()
        courgette.team = freelander.team = sentinel.DEFAULT
        mock_parser.onServerKill(mock_parser, "courgette EXP_Frag Freelander")
        del courgette.team, freelander.team
        self.assertTrue(mock_parser.getEvent.called)
        getEvent_args = mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_KILL_TEAM', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(courgette, getEvent_args[2])
        self.assertEqual(freelander, getEvent_args[3])
        
        # test teamkill with steamid
        mock_parser.reset_mock()
        courgette.team = freelander.team = sentinel.DEFAULT
        mock_parser.onServerKill(mock_parser, "12311111111111111 EXP_Frag 12300000000000000")
        del courgette.team, freelander.team
        self.assertTrue(mock_parser.getEvent.called)
        getEvent_args = mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_KILL_TEAM', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(courgette, getEvent_args[2])
        self.assertEqual(freelander, getEvent_args[3])
        
        
        # test kill with names
        mock_parser.reset_mock()
        mock_parser.onServerKill(mock_parser, "courgette EXP_Frag Freelander")
        self.assertTrue(mock_parser.getEvent.called)
        getEvent_args = mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_KILL', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(courgette, getEvent_args[2])
        self.assertEqual(freelander, getEvent_args[3])
        
        # test kill with steamid
        mock_parser.reset_mock()
        mock_parser.onServerKill(mock_parser, "12311111111111111 EXP_Frag 12300000000000000")
        self.assertTrue(mock_parser.getEvent.called)
        getEvent_args = mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_KILL', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(courgette, getEvent_args[2])
        self.assertEqual(freelander, getEvent_args[3])
        
        
        # test suicide with names
        mock_parser.reset_mock()
        mock_parser.onServerKill(mock_parser, "courgette EXP_Frag courgette")
        self.assertTrue(mock_parser.getEvent.called)
        getEvent_args = mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_SUICIDE', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(courgette, getEvent_args[2])
        self.assertEqual(courgette, getEvent_args[3])
        
        # test suicide with steamid
        mock_parser.reset_mock()
        mock_parser.onServerKill(mock_parser, "12311111111111111 EXP_Frag 12311111111111111")
        self.assertTrue(mock_parser.getEvent.called)
        getEvent_args = mock_parser.getEvent.call_args[0]
        self.assertEqual('EVT_CLIENT_SUICIDE', getEvent_args[0])
        self.assertEqual('EXP_Frag', getEvent_args[1][1])
        self.assertEqual(courgette, getEvent_args[2])
        self.assertEqual(courgette, getEvent_args[3])
        
        

if __name__ == '__main__':
    unittest.main()