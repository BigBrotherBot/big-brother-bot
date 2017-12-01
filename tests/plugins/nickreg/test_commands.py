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

from tests.plugins.nickreg import NickregTestCase


class Test_commands(NickregTestCase):

    def test_cmd_regnick_no_sufficient_level(self):
        # WHEN
        self.guest.clearMessageHistory()
        self.guest.says('!registernick')
        # THEN
        self.assertListEqual(['You need to be in group Moderator to use !registernick'], self.guest.message_history)

    def test_cmd_regnick_ok(self):
        # WHEN
        self.admin.clearMessageHistory()
        self.admin.says('!registernick')
        # THEN
        self.assertListEqual(['Your nick is now registered'], self.admin.message_history)

    def test_cmd_regnick_max_reached(self):
        # WHEN
        self.admin.says('!registernick')
        self.admin.name = 'Admin1'
        self.admin.says('!registernick')
        self.admin.name = 'Admin2'
        self.admin.says('!registernick')
        self.admin.name = 'Admin3'
        self.admin.clearMessageHistory()
        self.admin.says('!registernick')
        # THEN
        self.assertListEqual(['You already have 3 registered nicknames'], self.admin.message_history)

    def test_cmd_regnick_already_registered(self):
        # WHEN
        self.admin.says('!registernick')
        self.admin.clearMessageHistory()
        self.admin.says('!registernick')
        # THEN
        self.assertListEqual(['Nick Admin is already registered'], self.admin.message_history)

    def test_cmd_listnick_empty_set(self):
        # WHEN
        self.admin.clearMessageHistory()
        self.admin.says('!listnick')
        # THEN
        self.assertListEqual(['Admin has no registered nickname'], self.admin.message_history)

    def test_cmd_listnick_empty_set_with_param(self):
        # WHEN
        self.admin.clearMessageHistory()
        self.admin.says('!listnick guest')
        # THEN
        self.assertListEqual(['Guest has no registered nickname'], self.admin.message_history)

    def test_cmd_list_nick_with_3_entries(self):
        # WHEN
        self.admin.says('!registernick')
        self.admin.name = 'Admin1'
        self.admin.says('!registernick')
        self.admin.name = 'Admin2'
        self.admin.says('!registernick')
        self.admin.name = 'Admin'
        self.admin.clearMessageHistory()
        self.admin.says('!listnick')
        # THEN
        self.assertListEqual(['Admin has registered nickname(s): [1] admin, [2] admin1, [3] admin2'], self.admin.message_history)

    def test_cmd_delnick_no_param(self):
        # WHEN
        self.admin.clearMessageHistory()
        self.admin.says('!deletenick')
        # THEN
        self.assertListEqual(['Missing data, try !help deletenick'], self.admin.message_history)

    def test_cmd_delnick_invalid_param(self):
        # WHEN
        self.admin.clearMessageHistory()
        self.admin.says('!deletenick afagsdgdasg')
        # THEN
        self.assertListEqual(['Invalid data, try !help deletenick'], self.admin.message_history)

    def test_cmd_delnick_invalid_nick_id(self):
        # WHEN
        self.admin.clearMessageHistory()
        self.admin.says('!deletenick 123')
        # THEN
        self.assertListEqual(['Invalid nick id supplied: 123'], self.admin.message_history)

    def test_cmd_delnick_ok(self):
        # WHEN
        self.admin.says('!registernick')
        self.admin.clearMessageHistory()
        self.admin.says('!deletenick 1')
        # THEN
        self.assertListEqual(['Deleted nick: admin'], self.admin.message_history)

    def test_cmd_delnick_denied(self):
        # WHEN
        self.senioradmin.says("!registernick")
        self.admin.clearMessageHistory()
        self.admin.says('!deletenick 1')
        # THEN
        self.assertListEqual(['You can\'t delete SeniorAdmin registered nicknames!'], self.admin.message_history)