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
from tests import B3TestCase
import unittest

import b3
from b3.plugins.admin import AdminPlugin
from b3.config import XmlConfigParser

 
class Test_parseUserCmd(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
            <configuration plugin="admin">
            </configuration>
        """)
        self.p = AdminPlugin(b3.console, self.conf)


    @unittest.expectedFailure
    def test_clientinfo_bad_arg(self):
        self.assertIsNone(self.p.parseUserCmd(None))

    def test_clientinfo_empty_arg(self):
        self.assertIsNone(self.p.parseUserCmd(''))

    def test_clientinfo_only_1_arg(self):
        self.assertEqual(('someone', None), self.p.parseUserCmd('someone'))
        # see https://github.com/xlr8or/big-brother-bot/issues/54
        self.assertIsNone(self.p.parseUserCmd('someone', req=True))

    def test_clientinfo_2_args(self):
        self.assertEqual(('someone', 'param1'), self.p.parseUserCmd('someone param1'))
        self.assertEqual(('someone', 'param1'), self.p.parseUserCmd('someone param1', req=True))

    def test_clientinfo_3_args(self):
        self.assertEqual(('someone', 'param1 param2'), self.p.parseUserCmd('someone param1 param2'))
        self.assertEqual(('someone', 'param1 param2'), self.p.parseUserCmd('someone param1 param2', req=True))


if __name__ == '__main__':
    unittest.main()