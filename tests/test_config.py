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
import unittest
import sys
from b3.config import XmlConfigParser
from tests import B3TestCase
import b3

@unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
class Test_XmlConfigParser_windows(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
            <configuration plugin="test">
                <settings name="settings">
                    <set name="output_file">@conf/status.xml</set>
                </settings>
            </configuration>
        """)

    def test_getpath(self):
        b3.console.config.fileName = r"c:\some\where\conf\b3.xml"
        self.assertEqual(r"c:\some\where\conf\status.xml", self.conf.getpath('settings', 'output_file'))

    def test_issue_xlr8or_18(self):
        b3.console.config.fileName = r"b3.xml"
        self.assertEqual(r"status.xml", self.conf.getpath('settings', 'output_file'))


if __name__ == '__main__':
    unittest.main()