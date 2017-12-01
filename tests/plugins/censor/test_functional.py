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

from mock import Mock
from tests.plugins.censor import CensorTestCase

class Test_functional(CensorTestCase):
    """
    Test simulated in-game scenarios.
    """
    def test_joe_says_badword(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
                    <set name="max_level">40</set>
                    <!-- ignore bad words that have equal or less characters: -->
                    <set name="ignore_length">3</set>
                </settings>
                <badwords>
                    <penalty type="warning" reasonkeyword="default_reason"/>
                    <badword name="foo" lang="en">
                        <regexp>\bf[o0]{2}\b</regexp>
                    </badword>
                </badwords>
                <badnames>
                    <penalty type="warning" reasonkeyword="badname"/>
                    <badname name="cunt">
                        <word>cunt</word>
                    </badname>
                </badnames>
            </configuration>
        """)
        self.joe.warn = Mock()
        self.joe.connects(0)
        self.joe.says("qsfdl f0o!")
        self.assertEqual(1, self.joe.warn.call_count)

    def test_cunt_connects(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
                    <set name="max_level">40</set>
                    <!-- ignore bad words that have equal or less characters: -->
                    <set name="ignore_length">3</set>
                </settings>
                <badwords>
                    <penalty type="warning" reasonkeyword="default_reason"/>
                    <badword name="foo" lang="en">
                        <regexp>\bf[o0]{2}\b</regexp>
                    </badword>
                </badwords>
                <badnames>
                    <penalty type="warning" reasonkeyword="badname"/>
                    <badname name="cunt">
                        <word>cunt</word>
                    </badname>
                </badnames>
            </configuration>
        """)
        self.joe.name = self.joe.exactName = "cunt"
        self.joe.warn = Mock()
        self.joe.connects(0)
        self.assertEqual(1, self.joe.warn.call_count)

    def test_2_letters_badword_when_ignore_length_is_2(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
                    <set name="max_level">40</set>
                    <!-- ignore bad words that have equal or less characters: -->
                    <set name="ignore_length">2</set>
                </settings>
                <badwords>
                    <penalty type="warning" reasonkeyword="default_reason"/>
                    <badword name="TG" lang="fr">
                        <regexp>\bTG\b</regexp>
                    </badword>
                </badwords>
                <badnames>
                    <penalty type="warning" reasonkeyword="badname"/>
                </badnames>
            </configuration>
        """)

        self.joe.warn = Mock()
        self.joe.warn.reset_mock()
        self.joe.connects(0)
        self.joe.says("tg")
        self.assertEqual(0, self.joe.warn.call_count)

    def test_2_letters_badword_when_ignore_length_is_1(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
                    <set name="max_level">40</set>
                    <!-- ignore bad words that have equal or less characters: -->
                    <set name="ignore_length">1</set>
                </settings>
                <badwords>
                    <penalty type="warning" reasonkeyword="default_reason"/>
                    <badword name="TG" lang="fr">
                        <regexp>\bTG\b</regexp>
                    </badword>
                </badwords>
                <badnames>
                    <penalty type="warning" reasonkeyword="badname"/>
                </badnames>
            </configuration>
        """)

        self.joe.warn = Mock()
        self.joe.warn.reset_mock()
        self.joe.connects(0)
        self.joe.says("tg")
        self.assertEqual(1, self.joe.warn.call_count)

    def test_tempban_penalty_is_applied(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
                    <set name="max_level">40</set>
                    <!-- ignore bad words that have equal or less characters: -->
                    <set name="ignore_length">3</set>
                </settings>
                <badwords>
                    <penalty type="warning" reasonkeyword="default_reason"/>
                    <badword name="anani" lang="en">
                        <penalty type="tempban" reasonkeyword="cuss" duration="7d" />
                        <regexp>\s[a@]n[a@]n[iy!1]</regexp>
                    </badword>
                </badwords>
                <badnames>
                    <penalty type="warning" reasonkeyword="badname"/>
                </badnames>
            </configuration>
        """)
        self.joe.warn = Mock(wraps=lambda *args: sys.stdout.write("warning joe %s" % repr(args)))
        self.joe.tempban = Mock(wraps=lambda *args: sys.stdout.write("tempbanning joe %s" % repr(args)))
        self.joe.warn.reset_mock()
        self.joe.tempban.reset_mock()
        self.joe.connects(0)
        self.joe.says("anani")
        self.assertEqual(0, self.joe.warn.call_count)
        self.assertEqual(1, self.joe.tempban.call_count)