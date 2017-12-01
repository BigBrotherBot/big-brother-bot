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
from mock import Mock
from tests.plugins.censor import Detection_TestCase


class Test_Censor_badword_default_config(Detection_TestCase):
    """ test that bad words from the default config are detected """

    def setUp(self):
        super(Test_Censor_badword_default_config, self).setUp()

        self.p.debug = Mock()

        def my_info(text):
            print("INFO\t%s" % text)
        #self.p.info = my_info

        def my_warning(text):
            print("WARNING\t%s" % text)
        #self.p.warning = my_warning

        self.p.config.load(b3.getAbsolutePath('@b3/conf/plugin_censor.xml'))
        self.p.onLoadConfig()
        self.assertEqual(68, len(self.p._badWords))

    def test_default_penalty(self):
        self.assertEqual("warning", self.p._defaultBadWordPenalty.type)
        self.assertEqual(0, self.p._defaultBadWordPenalty.duration)
        self.assertEqual("cuss", self.p._defaultBadWordPenalty.keyword)
        self.assertIsNone(self.p._defaultBadWordPenalty.reason)

    def test_fuck_has_custom_penalty(self):
        badword_objects = [x for x in self.p._badWords if x.name == 'fuck']
        self.assertEqual(1, len(badword_objects))
        badword_object = badword_objects[0]
        self.assertEqual('tempban', badword_object.penalty.type)
        self.assertEqual(2, badword_object.penalty.duration)
        self.assertIsNone(badword_object.penalty.reason)
        self.assertEquals("cuss", badword_object.penalty.keyword)

    def test_shit_has_custom_penalty(self):
        badword_objects = [x for x in self.p._badWords if x.name == 'shit']
        self.assertEqual(1, len(badword_objects))
        badword_object = badword_objects[0]
        self.assertEqual('warning', badword_object.penalty.type)
        self.assertEqual(60*24, badword_object.penalty.duration)
        self.assertEquals("^7Please don't use profanity", badword_object.penalty.reason)
        self.assertIsNone(badword_object.penalty.keyword)

    def test_asshole_has_default_penalty(self):
        badword_objects = [x for x in self.p._badWords if x.name == 'asshole']
        self.assertEqual(1, len(badword_objects))
        badword_object = badword_objects[0]
        self.assertEqual(self.p._defaultBadWordPenalty.type, badword_object.penalty.type)
        self.assertEqual(self.p._defaultBadWordPenalty.keyword, badword_object.penalty.keyword)
        self.assertEqual(self.p._defaultBadWordPenalty.reason, badword_object.penalty.reason)
        self.assertEqual(self.p._defaultBadWordPenalty.duration, badword_object.penalty.duration)

    def test_shit(self):
        self.assert_chat_is_penalized('shit')
        self.assert_chat_is_penalized('x shit x')
        self.assert_chat_is_penalized('sh!t')
        self.assert_chat_is_penalized('sh*t')
        self.assert_chat_is_penalized('sh1t')
        self.assert_chat_is_penalized('$h1t')
        self.assert_chat_is_penalized('$hit')
        self.assert_chat_is_penalized('$hiiiiit')
        self.assert_chat_is_penalized('$hiiii*t')
        self.assert_chat_is_penalized('$h!t')
        self.assert_chat_is_penalized('xc $h!t. x ')

    def test_ass(self):
        self.assert_chat_is_penalized('ass')
        self.assert_chat_is_penalized('x ass x ')

    def test_asshole(self):
        self.assert_chat_is_penalized('asshole')
        self.assert_chat_is_penalized('x asshole x')
        self.assert_chat_is_penalized('assh0le')
        self.assert_chat_is_penalized('as$h0le')
        self.assert_chat_is_penalized('@sshole')
        self.assert_chat_is_penalized('stupid@sshole!')

    def test_fuck(self):
        self.assert_chat_is_penalized('fuck')
        self.assert_chat_is_penalized('x fuck x')
        self.assert_chat_is_penalized('fock')
        self.assert_chat_is_penalized('f*ck')
        self.assert_chat_is_penalized('f0ck')
        self.assert_chat_is_penalized('fucking')
        self.assert_chat_is_penalized('x fucking x')
        self.assert_chat_is_penalized('focking')
        self.assert_chat_is_penalized('f*cking')
        self.assert_chat_is_penalized('f0cking')
        self.assert_chat_is_penalized('fu0ouuuck')

    def test_fuc(self):
        self.assert_chat_is_penalized('fuc')
        self.assertTrue(self.p.debug.call_args[0][0].startswith('badword rule [fuc]'))
        self.assert_chat_is_penalized('foc')
        self.assert_chat_is_penalized('f0c')
        self.assert_chat_is_penalized('x fuc x')
        self.assert_chat_is_penalized('fuk ')
        self.assertTrue(self.p.debug.call_args[0][0].startswith('badword rule [fuc]'))
        self.assert_chat_is_penalized('x fuk x')

    def test_cunt(self):
        self.assert_chat_is_penalized('cunt')
        self.assert_chat_is_penalized('x cunt x')
        self.assert_chat_is_not_penalized('xcuntx')

    def test_cock(self):
        self.assert_chat_is_penalized('cock')
        self.assert_chat_is_penalized('c0ck')
        self.assert_chat_is_not_penalized('xxc0ckxx')
        self.assert_chat_is_penalized('x cock x')

    def test_dick(self):
        self.assert_chat_is_penalized('dick')
        self.assert_chat_is_not_penalized('dickhead')
        self.assert_chat_is_penalized('d1ck')
        self.assert_chat_is_penalized('d!ck')
        self.assert_chat_is_penalized('d*ck')
        self.assert_chat_is_penalized('x dick x')

    def test_bitch(self):
        self.assert_chat_is_penalized('bitch')
        self.assert_chat_is_penalized('x bitch x')

    def test_biatch(self):
        self.assert_chat_is_penalized('biatch')
        self.assert_chat_is_penalized('x biatch x')

    def test_fag(self):
        self.assert_chat_is_penalized('fag')
        self.assert_chat_is_penalized('x fag x')

    def test_nigger(self):
        self.assert_chat_is_penalized('nigger')
        self.assert_chat_is_penalized('x nigger x')

    def test_pussy(self):
        self.assert_chat_is_penalized('pussy')
        self.assert_chat_is_penalized('x pussy x')

    def test_lul(self):
        self.assert_chat_is_penalized('lul')

    def test_flikker(self):
        self.assert_chat_is_penalized('flikker')
        self.assert_chat_is_penalized('x flikker x')

    def test_homo(self):
        self.assert_chat_is_penalized('homo')
        self.assert_chat_is_penalized('x homo x')

    def test_kanker(self):
        self.assert_chat_is_penalized('kanker')
        self.assert_chat_is_penalized('x kanker x')

    def test_teringlijer(self):
        self.assert_chat_is_penalized('teringlijer')
        self.assert_chat_is_penalized('x teringlijer x')

    def test_kut(self):
        self.assert_chat_is_penalized('kut')
        self.assert_chat_is_penalized('x kut x')

    def test_hoer(self):
        self.assert_chat_is_penalized('hoer')
        self.assert_chat_is_penalized('x hoer x')

    def test_neuk(self):
        self.assert_chat_is_penalized('neuk')
        self.assert_chat_is_penalized('x neuk x')

    def test_vittu(self):
        self.assert_chat_is_penalized('vittu')
        self.assert_chat_is_penalized('x vittu x')

    def test_paskiainen(self):
        self.assert_chat_is_penalized('paskiainen')
        self.assert_chat_is_penalized('x paskiainen x')

    def test_kusipaeae(self):
        self.assert_chat_is_penalized('kusipaeae')
        self.assert_chat_is_penalized('x kusipaeae x')

    def test_fitte(self):
        self.assert_chat_is_penalized('fitte')
        self.assert_chat_is_penalized('x fitte x')

    def test_pikk(self):
        self.assert_chat_is_penalized('pikk')
        self.assert_chat_is_penalized('xs pikk x')

    def test_hore(self):
        self.assert_chat_is_penalized('hore')
        self.assert_chat_is_penalized('x hore x')

    def test_fitta(self):
        self.assert_chat_is_penalized('fitta')
        self.assert_chat_is_penalized('x fitta x')

    def test_knullare(self):
        self.assert_chat_is_penalized('knullare')
        self.assert_chat_is_penalized('x knullare x')

    def test_kuksugare(self):
        self.assert_chat_is_penalized('kuksugare')
        self.assert_chat_is_penalized('x kuksugare x')

    def test_huora(self):
        self.assert_chat_is_penalized('huora')
        self.assert_chat_is_penalized('x huora x')

    def test_spica(self):
        self.assert_chat_is_penalized('spica')
        self.assert_chat_is_penalized('x spica x')

    def test_piroca(self):
        self.assert_chat_is_penalized('piroca')
        self.assert_chat_is_penalized('x piroca x')

    def test_caralho(self):
        self.assert_chat_is_penalized('caralho')
        self.assert_chat_is_penalized('x caralho x')

    def test_puta(self):
        self.assert_chat_is_penalized('puta')
        self.assert_chat_is_penalized('x puta x')

    def test_cabra(self):
        self.assert_chat_is_penalized('cabra')
        self.assert_chat_is_penalized('x cabra x')

    def test_maricon(self):
        self.assert_chat_is_penalized('maricon')
        self.assert_chat_is_penalized('x maricon x')

    def test_pinche(self):
        self.assert_chat_is_penalized('pinche')
        self.assert_chat_is_penalized('x pinche x')

    def test_batard(self):
        self.assert_chat_is_penalized('batard')
        self.assert_chat_is_penalized('x batard x')

    def test_encule(self):
        self.assert_chat_is_penalized('encule')
        self.assert_chat_is_penalized('x encule x')

    def test_merde(self):
        self.assert_chat_is_penalized('merde')
        self.assert_chat_is_penalized('x merde x')

    def test_putain(self):
        self.assert_chat_is_penalized('putain')
        self.assert_chat_is_penalized('x putain x')

    def test_salaud(self):
        self.assert_chat_is_penalized('salaud')
        self.assert_chat_is_penalized('x salaud x')

    def test_connard(self):
        self.assert_chat_is_penalized('connard')
        self.assert_chat_is_penalized('x connard x')

    def test_salopard(self):
        self.assert_chat_is_penalized('salopard')
        self.assert_chat_is_penalized('x salopard x')

    def test_salope(self):
        self.assert_chat_is_penalized('salope')
        self.assert_chat_is_penalized('x salope x')

    def test_scheisse(self):
        self.assert_chat_is_penalized('scheisse')
        self.assert_chat_is_penalized('x scheisse x')

    def test_arsch(self):
        self.assert_chat_is_penalized('arsch')
        self.assert_chat_is_penalized('x arsch x')

    def test_huendin(self):
        self.assert_chat_is_penalized('huendin')
        self.assert_chat_is_penalized('x huendin x')

    def test_kopulieren(self):
        self.assert_chat_is_penalized('kopulieren')
        self.assert_chat_is_penalized('x kopulieren x')

    def test_fick(self):
        self.assert_chat_is_penalized('fick')
        self.assert_chat_is_penalized('x fick x')

    def test_chuj(self):
        self.assert_chat_is_penalized('chuj')
        self.assert_chat_is_penalized('x chuj x')

    def test_kutas(self):
        self.assert_chat_is_penalized('kutas')
        self.assert_chat_is_penalized('x kutas x')

    def test_fiut(self):
        self.assert_chat_is_penalized('fiut')
        self.assert_chat_is_penalized('x fiut x')

    def test_pedal(self):
        self.assert_chat_is_penalized('pedal')
        self.assert_chat_is_penalized('x pedal x')

    def test_cipa(self):
        self.assert_chat_is_penalized('cipa')
        self.assert_chat_is_penalized('x cipa x')

    def test_pizda(self):
        self.assert_chat_is_penalized('pizda')
        self.assert_chat_is_penalized(' x pizda x')

    def test_ciota(self):
        self.assert_chat_is_penalized('ciota')
        self.assert_chat_is_penalized('x ciota x')

    def test_dupek(self):
        self.assert_chat_is_penalized('dupek')
        self.assert_chat_is_penalized('x dupek x')

    def test_kurwa(self):
        self.assert_chat_is_penalized('kurwa')
        self.assert_chat_is_penalized('x kurwa x')

    def test_skurwysyn(self):
        self.assert_chat_is_penalized('skurwysyn')
        self.assert_chat_is_penalized('  x skurwysyn  x')

    def test_zajebac(self):
        self.assert_chat_is_penalized('zajebac')
        self.assert_chat_is_penalized('x zajebac x')

    def test_pojebac(self):
        self.assert_chat_is_penalized('pojebac')
        self.assert_chat_is_penalized(' x pojebac x')

    def test_wyjebac(self):
        self.assert_chat_is_penalized('wyjebac')
        self.assert_chat_is_penalized('x wyjebac x')

    def test_pierdolic(self):
        self.assert_chat_is_penalized('pierdolic')
        self.assert_chat_is_penalized('x pierdolic x')

    def test_rozpierdalac(self):
        self.assert_chat_is_penalized('rozpierdalaj')
        self.assert_chat_is_penalized(' x rozpierdalaj x')
        self.assert_chat_is_penalized('rozpierdol')
        self.assert_chat_is_penalized('rozpierdola')
        self.assert_chat_is_penalized('rozpierdolic')

    def test_popierdolony(self):
        self.assert_chat_is_penalized('popierdolony')
        self.assert_chat_is_penalized('x popierdolony x')

    def test_wypierdalac(self):
        self.assert_chat_is_penalized('wypierdalac')
        self.assert_chat_is_penalized('x wypierdalac x')






