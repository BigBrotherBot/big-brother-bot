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


from mockito import when
from b3.config import CfgConfigParser
from b3.plugins.translator import TranslatorPlugin
from tests import logging_disabled
from tests.plugins.translator import TranslatorTestCase
from textwrap import dedent


class Test_commands(TranslatorTestCase):

    def setUp(self):

        TranslatorTestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent(r"""
            [settings]
            default_source_language: it
            default_target_language: en
            display_translator_name: no
            translator_name: ^7[^1T^7]
            min_sentence_length: 6
            microsoft_client_id: fakeclientid
            microsoft_client_secret: fakeclientsecret

            [commands]
            translate: reg
            translast: reg
            transauto: reg
            translang: reg
        """))

        self.p = TranslatorPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        with logging_disabled():
            from b3.fake import FakeClient

        # create 2 fake clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", groupBits=2)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", groupBits=2)

        # connect the clients
        self.mike.connects("1")
        self.bill.connects("2")

        # define some translations for !translate command
        when(self.p).translate('it', 'en', 'Messaggio di prova').thenReturn('Test message')
        when(self.p).translate('en', 'fr', 'Test message').thenReturn('Message de test')
        when(self.p).translate('de', 'es', 'Test Meldungs').thenReturn('Mensaje de prueba')
        when(self.p).translate('nl', 'de', 'Test Bericht').thenReturn('Test Meldungs')
        when(self.p).translate('fr', 'en', 'Message de test').thenReturn('Test message')
        when(self.p).translate('it', 'es', 'Messaggio di prova').thenReturn('Mensaje de prueba')

        # define some translations for !transauto and !translast command
        when(self.p).translate('', 'en', 'Messaggio di prova').thenReturn('Test message')
        when(self.p).translate('', 'fr', 'Messaggio di prova').thenReturn('Message de test')

    ####################################################################################################################
    #                                                                                                                  #
    #   TEST CMD TRANSLATE                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_translate_no_source_and_target(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!translate Messaggio di prova")
        # THEN
        self.assertListEqual(['Test message'], self.mike.message_history)

    def test_cmd_translate_with_source_and_target(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!translate en*fr Test message")
        # THEN
        self.assertListEqual(['Message de test'], self.mike.message_history)

    def test_cmd_translate_with_source_only(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!translate fr* Message de test")
        # THEN
        self.assertListEqual(['Test message'], self.mike.message_history)

    def test_cmd_translate_with_target_only(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!translate *es Messaggio di prova")
        # THEN
        self.assertListEqual(['Mensaje de prueba'], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   TEST CMD TRANSLAST                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_translast(self):
        # WHEN
        self.bill.says('Messaggio di prova')
        self.mike.clearMessageHistory()
        self.mike.says("!translast")
        # THEN
        self.assertListEqual(['Test message'], self.mike.message_history)

    def test_cmd_translast_with_target(self):
        # WHEN
        self.bill.says('Messaggio di prova')
        self.mike.clearMessageHistory()
        self.mike.says("!translast fr")
        # THEN
        self.assertListEqual(['Message de test'], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   TEST CMD TRANSAUTO                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_transauto(self):
        # GIVEN
        self.mike.says('!transauto on')
        self.mike.clearMessageHistory()
        # WHEN
        self.bill.says('Messaggio di prova')
        # THEN
        self.assertListEqual(['Test message'], self.mike.message_history)
