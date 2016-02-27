# coding=utf-8
from textwrap import dedent
from mock import Mock, call

from tests.plugins.spree import SpreeTestCase


class Test_killingspree_messages(SpreeTestCase):

    def setUp(self):
        SpreeTestCase.setUp(self)
        self.p.warning = Mock()

    def test_nominal(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]
            # The # character splits the 'start' spree from the 'end' spree.
            5: %player% is on a killing spree (5 kills in a row) # %player% stopped the spree of %victim%

            [loosingspree_messages]
            7: Keep it up %player%, it will come eventually # You're back in business %player%
        """))
        self.assertListEqual([], self.p.warning.mock_calls)

    def test_no_message(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]

            [loosingspree_messages]
            7: Keep it up %player%, it will come eventually # You're back in business %player%
        """))
        self.assertListEqual([], self.p.warning.mock_calls)

    def test_missing_dash(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]
            # The # character splits the 'start' spree from the 'end' spree.
            5: foo

            [loosingspree_messages]
            7: Keep it up %player%, it will come eventually # You're back in business %player%
        """))
        self.assertListEqual([call("ignoring killingspree message 'foo' due to missing '#'")],
                             self.p.warning.mock_calls)


class Test_loosingspree_messages(SpreeTestCase):

    def setUp(self):
        SpreeTestCase.setUp(self)
        self.p.warning = Mock()

    def test_nominal(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]

            [loosingspree_messages]
            # The # character splits the 'start' spree from the 'end' spree.
            7: Keep it up %player%, it will come eventually # You're back in business %player%
        """))
        self.assertListEqual([], self.p.warning.mock_calls)

    def test_no_message(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]

            [loosingspree_messages]
        """))
        self.assertListEqual([], self.p.warning.mock_calls)

    def test_missing_dash(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]

            [loosingspree_messages]
            # The # character splits the 'start' spree from the 'end' spree.
            7: bar
        """))
        self.assertListEqual([call("ignoring killingspree message 'bar' due to missing '#'")],
                             self.p.warning.mock_calls)
