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

import time

from mock import patch, call
from mockito import when, verify
from b3.config import CfgConfigParser
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase


class Test_cmd_punkbuster(Bf3TestCase):

    def setUp(self):
        Bf3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
punkbuster-punk: 20
        """)
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()
        self.superadmin.connects('superadmin')


    def test_pb_inactive(self):
        when(self.console).write(('punkBuster.isActive',)).thenReturn(['false'])
        self.superadmin.clearMessageHistory()
        self.superadmin.says('!punkbuster test')
        self.assertEqual(['Punkbuster is not active'], self.superadmin.message_history)

    def test_pb_active(self):
        when(self.console).write(('punkBuster.isActive',)).thenReturn(['true'])
        self.superadmin.clearMessageHistory()
        self.superadmin.says('!punkbuster test')
        self.assertEqual([], self.superadmin.message_history)
        verify(self.console).write(('punkBuster.pb_sv_command', 'test'))

    def test_pb_active(self):
        when(self.console).write(('punkBuster.isActive',)).thenReturn(['true'])
        self.superadmin.clearMessageHistory()
        self.superadmin.says('!punk test')
        self.assertEqual([], self.superadmin.message_history)
        verify(self.console).write(('punkBuster.pb_sv_command', 'test'))
