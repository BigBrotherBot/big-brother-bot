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

import unittest
from mock import Mock # http://www.voidspace.org.uk/python/mock/mock.html
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin


class Test_issue_17_load_server_config(unittest.TestCase):

    def setUp(self):
        self.console = Mock()
        self.p = Poweradminbf3Plugin(self.console)

    def test_write_cvars_no_result(self):
        self.console.write.return_value = []
        self.p = self.p
        client = Mock()
        self.p.load_server_config(client, "theConfName", (
            "## some comment line",
            "",
            ' vars.serverMessage "Welcome to our Server Play as a team" ',
            "   ",
        ))
        self.assertEqual(1,self.console.write.call_count)
        self.console.write.assert_any_call(('vars.serverMessage', '"Welcome to our Server Play as a team"'))


if __name__ == '__main__':
    unittest.main(verbosity=2)