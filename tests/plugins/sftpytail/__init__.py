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

from b3.config import CfgConfigParser
from mockito import unstub
from tests import B3TestCase

try:
    import paramiko
except ImportError:
    raise unittest.SkipTest("paramiko module required")

from b3.plugins.sftpytail import SftpytailPlugin


class Test_Sftpytail_plugin(B3TestCase):

    def setUp(self):
        super(Test_Sftpytail_plugin, self).setUp()
        self.conf = CfgConfigParser()
        self.p = SftpytailPlugin(self.console, self.conf)

    def tearDown(self):
        B3TestCase.tearDown(self)
        unstub()