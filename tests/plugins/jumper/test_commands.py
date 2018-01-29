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

from mockito import when
from b3 import TEAM_FREE
from b3.plugins.jumper import JumperPlugin
from tests import logging_disabled
from tests.plugins.jumper import JumperTestCase


class Test_commands(JumperTestCase):

    def setUp(self):
        JumperTestCase.setUp(self)
        with logging_disabled():
            from b3.fake import FakeClient

        # create some clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", team=TEAM_FREE, groupBits=128)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", team=TEAM_FREE, groupBits=1)
        self.mark = FakeClient(console=self.console, name="Mark", guid="markguid", team=TEAM_FREE, groupBits=1)
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")

        self.console.game.mapName = 'ut42_bstjumps_u2'
        self.console.parseLine('''ClientJumpRunStarted: 1 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 1 - way: 1 - time: 537000''')
        self.console.parseLine('''ClientJumpRunStarted: 2 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 2 - way: 1 - time: 349000''')
        self.console.parseLine('''ClientJumpRunStarted: 3 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 3 - way: 1 - time: 122000''')
        self.console.parseLine('''ClientJumpRunStarted: 1 - way: 2''')
        self.console.parseLine('''ClientJumpRunStopped: 1 - way: 2 - time: 84000''')
        self.console.parseLine('''ClientJumpRunStarted: 2 - way: 2''')
        self.console.parseLine('''ClientJumpRunStopped: 2 - way: 2 - time: 91000''')
        self.console.parseLine('''ClientJumpRunStarted: 3 - way: 2''')
        self.console.parseLine('''ClientJumpRunStopped: 3 - way: 2 - time: 177000''')

        self.console.game.mapName = 'ut42_jupiter'
        self.console.parseLine('''ClientJumpRunStarted: 1 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 1 - way: 1 - time: 123000''')
        self.console.parseLine('''ClientJumpRunStarted: 2 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 2 - way: 1 - time: 543000''')
        self.console.parseLine('''ClientJumpRunStarted: 1 - way: 2''')
        self.console.parseLine('''ClientJumpRunStopped: 1 - way: 2 - time: 79000''')

        when(self.console).getMaps().thenReturn(['ut4_abbey', 'ut4_abbeyctf', 'ut4_algiers', 'ut4_ambush',
            'ut4_austria', 'ut42_bstjumps_u2', 'ut4_bohemia', 'ut4_casa', 'ut4_cascade', 'ut4_commune',
            'ut4_company', 'ut4_crossing', 'ut4_docks', 'ut4_dressingroom', 'ut4_eagle', 'ut4_elgin',
            'ut4_firingrange', 'ut4_ghosttown_rc4', 'ut4_harbortown', 'ut4_herring', 'ut4_horror', 'ut42_jupiter',
            'ut4_kingdom', 'ut4_kingpin', 'ut4_mandolin', 'ut4_mars_b1', 'ut4_maya', 'ut4_oildepot', 'ut4_prague',
            'ut4_prague_v2', 'ut4_raiders', 'ut4_ramelle', 'ut4_ricochet', 'ut4_riyadh', 'ut4_sanc', 'ut4_snoppis',
            'ut4_suburbs', 'ut4_subway', 'ut4_swim', 'ut4_thingley', 'ut4_tombs', 'ut4_toxic',
            'ut4_tunis', 'ut4_turnpike', 'ut4_uptown'])

    def tearDown(self):
        self.mike.disconnects()
        self.bill.disconnects()
        self.mark.disconnects()
        JumperTestCase.tearDown(self)

    ####################################################################################################################
    #                                                                                                                  #
    #   CLIENT RECORD COMMAND                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_client_record_no_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!record')
        # THEN
        self.assertListEqual(['listing records for Mike (@%s) on ut42_bstjumps_u2:' % self.mike.id,
                              '[1] 0:08:57.000 since %s' % JumperPlugin.getDateString(self.console.time()),
                              '[2] 0:01:24.000 since %s' % JumperPlugin.getDateString(self.console.time())], self.mike.message_history)

    def test_cmd_client_record_single_argument(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!record bill')
        # THEN
        self.assertListEqual(['listing records for Bill (@%s) on ut42_bstjumps_u2:' % self.bill.id,
                              '[1] 0:05:49.000 since %s' % JumperPlugin.getDateString(self.console.time()),
                              '[2] 0:01:31.000 since %s' % JumperPlugin.getDateString(self.console.time())], self.mike.message_history)

    def test_cmd_client_record_double_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!record bill jupiter')
        # THEN
        self.assertListEqual(['[1] 0:09:03.000 since %s' % JumperPlugin.getDateString(self.console.time())], self.mike.message_history)

    def test_cmd_client_record_double_arguments_no_record(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!record mark jupiter')
        # THEN
        self.assertListEqual(['no record found for Mark (@%s) on ut42_jupiter' % self.mark.id], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   MAP RECORD COMMAND                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_maprecord_no_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!maprecord')
        # THEN
        self.assertListEqual(['listing map records on ut42_bstjumps_u2:',
                              '[1] Mark (@%s) with 0:02:02.000' % self.mark.id,
                              '[2] Mike (@%s) with 0:01:24.000' % self.mike.id], self.mike.message_history)

    def test_cmd_maprecord_with_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!maprecord jupiter')
        # THEN
        self.assertListEqual(['listing map records on ut42_jupiter:',
                              '[1] Mike (@%s) with 0:02:03.000' % self.mike.id,
                              '[2] Mike (@%s) with 0:01:19.000' % self.mike.id], self.mike.message_history)

    def test_cmd_maprecord_with_arguments_no_record(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!maprecord mars')
        # THEN
        self.assertListEqual(['no record found on ut4_mars_b1'], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   TOPRUNS COMMAND                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_topruns_no_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!topruns')
        # THEN
        self.assertListEqual(['listing top runs on ut42_bstjumps_u2:',
                              '[1] #1 Mark (@%s) with 0:02:02.000' % self.mark.id,
                              '[1] #2 Bill (@%s) with 0:05:49.000' % self.bill.id,
                              '[1] #3 Mike (@%s) with 0:08:57.000' % self.mike.id,
                              '[2] #1 Mike (@%s) with 0:01:24.000' % self.mike.id,
                              '[2] #2 Bill (@%s) with 0:01:31.000' % self.bill.id,
                              '[2] #3 Mark (@%s) with 0:02:57.000' % self.mark.id], self.mike.message_history)

    def test_cmd_topruns_with_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!topruns jupiter')
        # THEN
        self.assertListEqual(['listing top runs on ut42_jupiter:',
                              '[1] #1 Mike (@%s) with 0:02:03.000' % self.mike.id,
                              '[1] #2 Bill (@%s) with 0:09:03.000' % self.bill.id,
                              '[2] #1 Mike (@%s) with 0:01:19.000' % self.mike.id], self.mike.message_history)

    def test_cmd_topruns_with_arguments_no_record(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!topruns mars')
        # THEN
        self.assertListEqual(['no record found on ut4_mars_b1'], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   DELRECORD COMMAND                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_delrecord_no_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!delrecord')
        # THEN
        self.assertListEqual(['removed 2 records for Mike (@%s) on ut42_bstjumps_u2' % self.mike.id], self.mike.message_history)
        self.assertListEqual([], self.p.getClientRecords(self.mike, 'ut42_bstjumps_u2'))

    def test_cmd_delrecord_with_one_argument(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!delrecord bill')
        # THEN
        self.assertListEqual(['removed 2 records for Bill (@%s) on ut42_bstjumps_u2' % self.bill.id], self.mike.message_history)
        self.assertListEqual([], self.p.getClientRecords(self.bill, 'ut42_bstjumps_u2'))

    def test_cmd_delrecord_with_two_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!delrecord bill jupiter')
        # THEN
        self.assertListEqual(['removed 1 record for Bill (@%s) on ut42_jupiter' % self.bill.id], self.mike.message_history)
        self.assertListEqual([], self.p.getClientRecords(self.bill, 'ut42_jupiter'))

    def test_cmd_delrecord_with_two_arguments_no_record(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!delrecord mark jupiter')
        # THEN
        self.assertListEqual(['no record found for Mark (@%s) on ut42_jupiter' % self.mark.id], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                #
    #   MAPINFO COMMAND                                                                                              #
    #                                                                                                                #
    ####################################################################################################################

    # def test_cmd_mapinfo_no_arguments(self):
    #     # GIVEN
    #     self.console.game.mapName = 'ut4_uranus_beta1a'
    #     # WHEN
    #     self.mike.clearMessageHistory()
    #     self.mike.says('!mapinfo')
    #     # THEN
    #     self.assertListEqual([u'''Uranus has been created by Levant''',
    #                           u'''it has been released on Tue, 15 Jan 2013''',
    #                           u'''it's composed of 22 jumps and 1 way''',
    #                           u'''level: 50/100'''], self.mike.message_history)

    # def test_cmd_mapinfo_with_arguments(self):
    #     # GIVEN
    #     self.console.game.mapName = 'ut4_uranus_beta1a'
    #     # WHEN
    #     self.mike.clearMessageHistory()
    #     self.mike.says('!mapinfo crouch')
    #     # THEN
    #     self.assertListEqual([u'''Crouch Training has been created by spidercochon''',
    #                           u'''it has been released on Thu, 30 Dec 2010''',
    #                           u'''it's composed of 11 jumps and 1 way''',
    #                           u'''level: 79/100'''], self.mike.message_history)

    # def test_cmd_mapinfo_no_result(self):
    #     # GIVEN
    #     self.console.game.mapName = 'ut4_turnpike'
    #     # WHEN
    #     self.mike.clearMessageHistory()
    #     self.mike.says('!mapinfo')
    #     # THEN
    #     self.assertListEqual(['could not find info for map ut4_turnpike'], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   SETWAY COMMAND                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_setway(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!setway 1 Rookie')
        self.mike.says('!setway 2 Explorer')
        self.mike.clearMessageHistory()
        self.mike.says('!maprecord')
        # THEN
        self.assertListEqual(['listing map records on ut42_bstjumps_u2:',
                              '[Rookie] Mark (@%s) with 0:02:02.000' % self.mark.id,
                              '[Explorer] Mike (@%s) with 0:01:24.000' % self.mike.id], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER COMMANDS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_maps(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!maps')
        # THEN
        self.assertListEqual(['map rotation: ut42_bstjumps_u2, ut42_jupiter, ut4_mars_b1'], self.mike.message_history)

    def test_cmd_map_valid_name(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!map jup')
        # THEN
        self.assertListEqual(['changing map to ut42_jupiter'], self.mike.message_history)

    def test_cmd_map_invalid_name(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!map f00')
        # THEN
        self.assertListEqual(['do you mean: ut42_bstjumps_u2, ut4_mars_b1, ut42_jupiter?'], self.mike.message_history)