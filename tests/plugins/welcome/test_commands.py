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

from tests.plugins.welcome import Welcome_functional_test

class Test_cmd_greeting(Welcome_functional_test):

    def setUp(self):

        Welcome_functional_test.setUp(self)
        self.load_config()
        # disabled event handling (spawns threads and is of no use for that test)
        self.p.onEvent = lambda *args, **kwargs: None
        self.superadmin.connects("0")
        self.superadmin._connections = 3

    def test_no_parameter(self):
        # GIVEN
        self.superadmin.greeting = ''
        self.superadmin.clearMessageHistory()
        # WHEN
        self.superadmin.says('!greeting')
        # THEN
        self.assertListEqual(['You have no greeting set'], self.superadmin.message_history)

        # GIVEN
        self.superadmin.greeting = 'hi f00'
        self.superadmin.clearMessageHistory()
        # WHEN
        self.superadmin.says('!greeting')
        # THEN
        self.assertListEqual(['Your greeting is hi f00'], self.superadmin.message_history)

    def test_set_new_greeting_none(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting none')
        # THEN
        self.assertListEqual(['Greeting cleared'], self.superadmin.message_history)
        self.assertEqual('', self.superadmin.greeting)

    def test_set_new_greeting_nominal(self):
        # GIVEN
        self.superadmin.greeting = ''
        # WHEN
        self.superadmin.says('!greeting f00')
        # THEN
        self.assertListEqual(['Greeting Test: f00', 'Greeting changed to: f00'], self.superadmin.message_history)
        self.assertEqual('f00', self.superadmin.greeting)

    def test_set_new_greeting_too_long(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting %s' % ('x' * 256))
        # THEN
        self.assertListEqual(['Your greeting is too long'], self.superadmin.message_history)
        self.assertEqual('f00', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_name(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$name|')
        # THEN
        self.assertListEqual(['Greeting Test: |SuperAdmin|', 'Greeting changed to: |$name|'],
                             self.superadmin.message_history)
        self.assertEqual('|%(name)s|', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_greeting(self):
        """
        make sure that '$greeting' cannot be taken as a placeholder or we would allow recursive greeting.
        """
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$greeting|')
        # THEN
        self.assertListEqual(['Greeting Test: |$greeting|', 'Greeting changed to: |$greeting|'],
                             self.superadmin.message_history)
        self.assertEqual('|$greeting|', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_maxLevel(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$maxLevel|')
        # THEN
        self.assertListEqual(['Greeting Test: |100|', 'Greeting changed to: |$maxLevel|'],
                             self.superadmin.message_history)
        self.assertEqual('|%(maxLevel)s|', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_group(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$group|')
        # THEN
        self.assertListEqual(['Greeting Test: |Super Admin|', 'Greeting changed to: |$group|'],
                             self.superadmin.message_history)
        self.assertEqual('|%(group)s|', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_connections(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$connections|')
        # THEN
        self.assertListEqual(['Greeting Test: |3|', 'Greeting changed to: |$connections|'],
                             self.superadmin.message_history)
        self.assertEqual('|%(connections)s|', self.superadmin.greeting)