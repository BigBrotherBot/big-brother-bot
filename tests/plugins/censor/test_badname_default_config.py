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
from tests.plugins.censor import Detection_TestCase


class Test_Censor_badname_default_config(Detection_TestCase):
    """
    Test that bad names from the default config are detected
    """

    def setUp(self):
        super(Test_Censor_badname_default_config, self).setUp()

        def my_info(text):
            print("INFO\t%s" % text)
        #self.p.info = my_info

        def my_warning(text):
            print("WARNING\t%s" % text)
        #self.p.warning = my_warning

        self.p.config.load(b3.getAbsolutePath('@b3/conf/plugin_censor.xml'))
        self.p.onLoadConfig()
        self.assertEqual(17, len(self.p._badNames))

    def test_default_penalty(self):
        self.assertEqual("warning", self.p._defaultBadNamePenalty.type)
        self.assertEqual(0, self.p._defaultBadNamePenalty.duration)
        self.assertEqual("badname", self.p._defaultBadNamePenalty.keyword)
        self.assertIsNone(self.p._defaultBadNamePenalty.reason)

    def test_nigger_has_custom_penalty(self):
        badname_objects = [x for x in self.p._badNames if x.name == 'nigger']
        self.assertEqual(1, len(badname_objects))
        badname_object = badname_objects[0]
        self.assertEqual('ban', badname_object.penalty.type)
        self.assertEqual('racism', badname_object.penalty.keyword)

    def test_shit_has_default_penalty(self):
        badname_objects = [x for x in self.p._badNames if x.name == 'shit']
        self.assertEqual(1, len(badname_objects))
        badname_object = badname_objects[0]
        self.assertEqual(self.p._defaultBadNamePenalty.type, badname_object.penalty.type)
        self.assertEqual(self.p._defaultBadNamePenalty.keyword, badname_object.penalty.keyword)
        self.assertEqual(self.p._defaultBadNamePenalty.reason, badname_object.penalty.reason)
        self.assertEqual(self.p._defaultBadNamePenalty.duration, badname_object.penalty.duration)

    def test_doublecolor(self):
        self.assert_name_is_penalized('j^^33oe')

    def test_ass(self):
        self.assert_name_is_not_penalized('jassica')
        self.assert_name_is_penalized('ass')
        self.assert_name_is_penalized('a$s')
        self.assert_name_is_penalized('big a$s joe')
        self.assert_name_is_penalized('big ass joe')

    def test_fuck(self):
        self.assert_name_is_penalized('fuck')
        self.assert_name_is_penalized(' fuck ')
        self.assert_name_is_penalized('what the fuck!')
        self.assert_name_is_penalized('fUck')
        self.assert_name_is_penalized('f*ck')
        self.assert_name_is_penalized('f.ck')
        self.assert_name_is_penalized('f.uck')
        self.assert_name_is_penalized('fuuuuck')
        self.assert_name_is_penalized('fuckkkkk')
        self.assert_name_is_penalized('watdafuck?')

    def test_shit(self):
        self.assert_name_is_penalized('shit')
        self.assert_name_is_penalized(' shit ')
        self.assert_name_is_penalized('this is shit!')
        self.assert_name_is_penalized('shIt')
        self.assert_name_is_penalized('sh!t')
        self.assert_name_is_penalized('sh.t')

    def test_bitch(self):
        self.assert_name_is_penalized('bitch')
        self.assert_name_is_penalized('son of a bitch!')
        self.assert_name_is_penalized('b*tch')
        self.assert_name_is_penalized('b!tch')
        self.assert_name_is_penalized('b.tch')
        self.assert_name_is_penalized('daBiTch')

    def test_pussy(self):
        self.assert_name_is_penalized('pussy')
        self.assert_name_is_penalized('qsdf pussy qsdf')
        self.assert_name_is_penalized('pu$sy')
        self.assert_name_is_penalized('pus$y')
        self.assert_name_is_penalized('pu$$y')
        self.assert_name_is_penalized('DaPussyKat')

    def test_nigger(self):
        self.assert_name_is_penalized('nigger')
        self.assert_name_is_penalized('qsfd nigger qsdf ')
        self.assert_name_is_penalized('n1gger')
        self.assert_name_is_penalized('n.gger')
        self.assert_name_is_penalized('n!gger')
        penalty = self.p.penalizeClientBadname.call_args[0][0]
        self.assertEqual('ban', penalty.type)
        self.assertEqual('racism', penalty.keyword)

    def test_cunt(self):
        self.assert_name_is_penalized('cunt')
        self.assert_name_is_penalized('stupid cunt')
        self.assert_name_is_penalized('cunt on this')

    def test_nazi(self):
        self.assert_name_is_penalized('nazi')
        self.assert_name_is_penalized('naz!')
        self.assert_name_is_penalized('n@z!')
        self.assert_name_is_penalized('n@zi')

    def test_jihad(self):
        self.assert_name_is_penalized("jihad")
        self.assert_name_is_penalized("jih@d")
        self.assert_name_is_penalized("j!h@d")
        self.assert_name_is_penalized("j!had")
        self.assert_name_is_penalized("j1had")

    def test_admin(self):
        self.assert_name_is_penalized("admin")
        self.assert_name_is_penalized("@dmin")
        self.assert_name_is_penalized("@dm1n")
        self.assert_name_is_penalized("adm1n")
        self.assert_name_is_penalized("adm!n")

    def test_hitler(self):
        self.assert_name_is_penalized("hitler")
        self.assert_name_is_penalized("hitl3r")
        self.assert_name_is_penalized("hitl.r")
        self.assert_name_is_penalized("h!tler")
        self.assert_name_is_penalized("h1tler")
        self.assert_name_is_penalized("hit1er")

    def test_asshole(self):
        self.assert_name_is_penalized("asshole")
        self.assert_name_is_penalized("asshOle")
        self.assert_name_is_penalized("asshO1e")
        self.assert_name_is_penalized("a$$hO1e")
        self.assert_name_is_penalized("@$$hO1e")

    def test_kut(self):
        self.assert_name_is_penalized("kut")

    def test_hoer(self):
        self.assert_name_is_penalized("hoer")
        self.assert_name_is_penalized("h0er")
        self.assert_name_is_penalized("h0err")

    def test_huora(self):
        self.assert_name_is_penalized("huora")
        self.assert_name_is_penalized("hu0ra")
        self.assert_name_is_penalized("hu0r@")

    def test_puta(self):
        self.assert_name_is_penalized("puta")
        self.assert_name_is_penalized("put@")