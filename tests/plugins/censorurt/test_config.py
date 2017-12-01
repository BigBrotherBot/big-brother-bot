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

import b3

from tests.plugins.censorurt import CensorurtTestCase


class Test_urbanterror_mute(CensorurtTestCase):
    def test_missing(self):
        self.init_plugin("""
            <configuration/>
        """)
        self.assertFalse(self.p._mute)

    def test_empty(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="mute"></set>
		        </settings>
            </configuration>
        """)
        self.assertFalse(self.p._mute)

    def test_nominal_yes(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="mute">yes</set>
		        </settings>
            </configuration>
        """)
        self.assertTrue(self.p._mute)

    def test_nominal_no(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="mute">no</set>
		        </settings>
            </configuration>
        """)
        self.assertFalse(self.p._mute)

    def test_nominal_true(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="mute">true</set>
		        </settings>
            </configuration>
        """)
        self.assertTrue(self.p._mute)

    def test_rubbish(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="mute">f00</set>
		        </settings>
            </configuration>
        """)
        self.assertFalse(self.p._mute)
        
        
class Test_urbanterror_slap(CensorurtTestCase):
    def test_missing(self):
        self.init_plugin("""
            <configuration/>
        """)
        self.assertFalse(self.p._slap)

    def test_empty(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="slap"></set>
		        </settings>
            </configuration>
        """)
        self.assertFalse(self.p._slap)

    def test_nominal_yes(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="slap">yes</set>
		        </settings>
            </configuration>
        """)
        self.assertTrue(self.p._slap)

    def test_nominal_no(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="slap">no</set>
		        </settings>
            </configuration>
        """)
        self.assertFalse(self.p._slap)

    def test_nominal_true(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="slap">true</set>
		        </settings>
            </configuration>
        """)
        self.assertTrue(self.p._slap)

    def test_rubbish(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="slap">f00</set>
		        </settings>
            </configuration>
        """)
        self.assertFalse(self.p._slap)
        
        
class Test_urbanterror_muteduration1(CensorurtTestCase):
    def test_missing(self):
        self.init_plugin("""
            <configuration/>
        """)
        self.assertEqual(0, self.p._muteduration1)

    def test_empty(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration1"></set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._muteduration1)

    def test_nominal_0(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration1">0</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._muteduration1)

    def test_nominal_decimal(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration1">0.5</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0.5, self.p._muteduration1)

    def test_nominal_5(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration1">5</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(5.0, self.p._muteduration1)

    def test_rubbish(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration1">f00</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._muteduration1)
        
        
class Test_urbanterror_muteduration2(CensorurtTestCase):
    def test_missing(self):
        self.init_plugin("""
            <configuration/>
        """)
        self.assertEqual(0, self.p._muteduration2)

    def test_empty(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration2"></set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._muteduration2)

    def test_nominal_0(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration2">0</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._muteduration2)

    def test_nominal_decimal(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration2">0.5</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0.5, self.p._muteduration2)

    def test_nominal_5(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration2">5</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(5.0, self.p._muteduration2)

    def test_rubbish(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration2">f00</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._muteduration2)
        
        
class Test_urbanterror_muteduration3(CensorurtTestCase):
    def test_missing(self):
        self.init_plugin("""
            <configuration/>
        """)
        self.assertEqual(0, self.p._muteduration3)

    def test_empty(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration3"></set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._muteduration3)

    def test_nominal_0(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration3">0</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._muteduration3)

    def test_nominal_decimal(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration3">0.5</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0.5, self.p._muteduration3)

    def test_nominal_5(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration3">5</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(5.0, self.p._muteduration3)

    def test_rubbish(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="muteduration3">f00</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._muteduration3)
        
        
class Test_urbanterror_warn_after(CensorurtTestCase):
    def test_missing(self):
        self.init_plugin("""
            <configuration/>
        """)
        self.assertEqual(0, self.p._warnafter)

    def test_empty(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="warn_after"></set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._warnafter)

    def test_nominal_0(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="warn_after">0</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._warnafter)

    def test_decimal(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="warn_after">0.5</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._warnafter)

    def test_nominal_5(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="warn_after">5</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(5, self.p._warnafter)

    def test_rubbish(self):
        self.init_plugin("""
            <configuration>
                <settings name="urbanterror">
		            <set name="warn_after">f00</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._warnafter)


class Test_messages(CensorurtTestCase):
    def setUp(self):
        CensorurtTestCase.setUp(self)
        self.p._messages = {}  # empty message cache

    def getMessage(self):
        return self.p.getMessage('mute_announcement', {
            'playername': 'ThePlayer',
            'duration': '5'
        })

    def test_missing(self):
        self.init_plugin("""
            <configuration/>
        """)
        self.assertEqual("Muting ThePlayer for 5 minutes", self.getMessage())

    def test_empty(self):
        self.init_plugin("""
            <configuration>
                <settings name="messages">
		            <set name="mute_announcement"></set>
		        </settings>
            </configuration>
        """)
        self.assertEqual("", self.getMessage())

    def test_nominal(self):
        self.init_plugin("""
            <configuration>
                <settings name="messages">
		            <set name="mute_announcement">Foo $playername blahblah $duration.</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual("Foo ThePlayer blahblah 5.", self.getMessage())

    def test_missing_duration(self):
        self.init_plugin("""
            <configuration>
                <settings name="messages">
		            <set name="mute_announcement">Foo $playername blahblah.</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual("Foo ThePlayer blahblah.", self.getMessage())

    def test_nominal_playername(self):
        self.init_plugin("""
            <configuration>
                <settings name="messages">
		            <set name="mute_announcement">Foo blahblah $duration.</set>
		        </settings>
            </configuration>
        """)
        self.assertEqual("Foo blahblah 5.", self.getMessage())
