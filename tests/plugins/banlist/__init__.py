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

from unittest import TestCase
from mock import patch


class BanlistTestCase(TestCase):
    """
    TestCase suitable for testing a Banlist class
    """

    def setUp(self):
        # use self.file_content to control the content of the loaded banlist file
        self.file_content = ""

        self.patcher_isfile = patch("os.path.isfile")
        self.patcher_isfile.start()

        self.patcher_open = patch("__builtin__.open")
        self.mock_open = self.patcher_open.start()
        manager = self.mock_open.return_value.__enter__.return_value
        manager.read.side_effect = lambda: self.file_content

        self.patcher_getModifiedTime = patch("b3.plugins.banlist.Banlist.getModifiedTime", return_value=946684800)
        self.patcher_getModifiedTime.start()
        self.patcher_getHumanModifiedTime = patch("b3.plugins.banlist.Banlist.getHumanModifiedTime", return_value="2000-01-01 00:00:00")
        self.patcher_getHumanModifiedTime.start()


    def tearDown(self):
        self.patcher_isfile.stop()
        self.patcher_open.stop()
        self.patcher_getModifiedTime.stop()
        self.patcher_getHumanModifiedTime.stop()

