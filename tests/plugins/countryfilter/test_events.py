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

from mock import Mock, call
from tests.plugins.countryfilter import CountryFilterTestCase
from textwrap import dedent


class Test_events(CountryFilterTestCase):

    def test_allow_from_italy(self):
        # GIVEN
        self.init(dedent(r"""
            [settings]
            cf_order: deny,allow
            cf_deny_from: all
            cf_allow_from: IT
        """))
        # GIVEN
        self.console.say = Mock()
        self.bill.kick = Mock()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=self.bill))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=self.mike))
        # THEN
        self.console.say.assert_has_calls([call('^7Bill ^1(country: United States)^7 was rejected by B3'), call('^7Mike ^2(country: Italy)^7 is accepted by B3')])
        self.bill.kick.assert_called_with(silent=True)

    def test_deny_from_united_states(self):
        # GIVEN
        self.init(dedent(r"""
            [settings]
            cf_order: allow,deny
            cf_allow_from: all
            cf_deny_from: US
        """))
        # GIVEN
        self.console.say = Mock()
        self.bill.kick = Mock()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=self.bill))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=self.mike))
        # THEN
        self.console.say.assert_has_calls([call('^7Bill ^1(country: United States)^7 was rejected by B3'), call('^7Mike ^2(country: Italy)^7 is accepted by B3')])
        self.bill.kick.assert_called_with(silent=True)

    def test_deny_from_united_states_with_ignore_name(self):
        # GIVEN
        self.init(dedent(r"""
            [settings]
            cf_order: allow,deny
            cf_allow_from: all
            cf_deny_from: US

            [ignore]
            names: Bill
        """))
        # GIVEN
        self.console.say = Mock()
        self.bill.connects('1')
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=self.bill))
        # THEN
        self.console.say.assert_called_with('^7Bill ^2(country: United States)^7 is accepted by B3')

    def test_deny_from_united_states_with_ignore_ip(self):
        # GIVEN
        self.init(dedent(r"""
            [settings]
            cf_order: allow,deny
            cf_allow_from: all
            cf_deny_from: US

            [ignore]
            ips: 2.3.4.5
        """))
        # GIVEN
        self.console.say = Mock()
        self.bill.connects('1')
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=self.bill))
        # THEN
        self.console.say.assert_called_with('^7Bill ^2(country: United States)^7 is accepted by B3')

    def test_deny_from_italy_by_ip(self):
        # GIVEN
        self.init(dedent(r"""
            [settings]
            cf_order: allow,deny
            cf_allow_from: all
            cf_deny_from: US

            [block]
            ips: 1.2.3.4
        """))
        # GIVEN
        self.console.say = Mock()
        self.mike.kick = Mock()
        self.mike.connects('1')
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=self.mike))
        # THEN
        self.console.say.assert_called_with('^7Mike ^1(country: Italy)^7 was rejected by B3')
        self.mike.kick.assert_called_with(silent=True)