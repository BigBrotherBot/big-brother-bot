# coding=UTF-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Courgette
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
import logging
import unittest2 as unittest
from b3.clients import Client
from b3.parser import Parser


class DummyParser(Parser):
    gameName = "dummy"

    def __init__(self):
        pass # skip parent class constructor
        self.log = logging.getLogger("output")


class Test_getMessage(unittest.TestCase):

    def setUp(self):
        self.parser = DummyParser()
        self.parser._messages = {}

    def test_unknown_msg__falls_back_on_default(self):
        self.parser._messages = {}
        self.parser._messages_default = {"f00": "lorem ipsum"}
        self.assertEqual("lorem ipsum", self.parser.getMessage("f00"))

    def test_no_parameter(self):
        self.parser._messages['f00'] = "bar"
        self.assertEqual("bar", self.parser.getMessage('f00'))

    def test_with_parameter(self):
        self.parser._messages['f00'] = "bar %s"
        self.assertEqual("bar joe", self.parser.getMessage('f00', 'joe'))

    def test_with_unexpected_parameter(self):
        self.parser._messages['f00'] = "bar"
        self.assertRaises(TypeError, self.parser.getMessage, 'f00', 'joe')

    def test_with_dict_parameter(self):
        self.parser._messages['f00'] = "bar %(p1)s"
        self.assertEqual("bar joe", self.parser.getMessage('f00', {'p1': 'joe'}))

    def test_with_missing_dict_parameter(self):
        self.parser._messages['f00'] = "bar %(p1)s"
        self.assertRaises(KeyError, self.parser.getMessage, 'f00', {'p2': 'joe'})

    def test_with_unicode_dict_parameter(self):
        self.parser._messages['f00'] = "bar %(p1)s"
        self.assertEqual(u"bar joéÄ", self.parser.getMessage('f00', {'p1': u'joéÄ'}))



class Test_getMessageVariables(unittest.TestCase):

    def setUp(self):
        self.parser = DummyParser()

    def test_with_parameters(self):
        client = Client(name="Jack")
        rv = self.parser.getMessageVariables(client)
        self.assertDictContainsSubset({'name': client.name}, rv, rv)

    def test_with_named_parameters(self):
        client = Client(name="Jack")
        self.assertDictContainsSubset({'clientname': client.name, 'reason': 'this is a good reason'}, self.parser.getMessageVariables(client=client, reason="this is a good reason"))

    def test_with_named_parameters__unicode(self):
        client = Client(name=u"ÄÖé")
        self.assertDictContainsSubset({'clientname':client.name, 'reason': 'this is a good reason'}, self.parser.getMessageVariables(client=client, reason="this is a good reason"))




if __name__ == '__main__':
    unittest.main()