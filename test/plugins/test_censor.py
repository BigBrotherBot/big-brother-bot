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
from test import B3TestCase
import unittest

import b3
from b3.plugins.censor import CensorPlugin
from b3.config import XmlConfigParser

 
class Test_Censor(B3TestCase):
    conf = XmlConfigParser()
    
    def test_minimal(self):
        self.conf.setXml("""
            <configuration plugin="censor">
                <settings name="settings">
                    <set name="max_level">40</set>
                    <set name="ignore_length">3</set>
                </settings>
                <badwords>
                    <penalty type="warning" reasonkeyword="racist"/>
                </badwords>
                <badnames>
                    <penalty type="warning" reasonkeyword="badname"/>
                </badnames>
            </configuration>
        """)
        CensorPlugin(b3.console, self.conf)


if __name__ == '__main__':
    unittest.main()