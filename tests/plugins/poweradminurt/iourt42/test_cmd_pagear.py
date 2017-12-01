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

import time
from mock import patch, call
from mockito import when
from b3.config import CfgConfigParser
from b3.cvar import Cvar
from b3.plugins.poweradminurt import PoweradminurtPlugin
from tests.plugins.poweradminurt.iourt42 import Iourt42TestCase


G_ALL = "FGHIJKLMNZacefghOQRSTUVWX"
G_NONE = ""
G_BERETTA_92FS = "F"
G_50_DESERT_EAGLE = "G"
G_SPAS_12 = "H"
G_MP5K = "I"
G_UMP45 = "J"
G_HK69 = "K"
G_LR300ML = "L"
G_G36 = "M"
G_PSG1 = "N"
G_SR8 = "Z"
G_AK103 = "a"
G_NEGEV_LMG = "c"
G_COLT_M4 = "e"
G_GLOCK = "f"
G_COLT1911 = "g"
G_MAC11 = "h"
G_HE_GRENADE = "O"
G_SMOKE_GRENADE = "Q"
G_KEVLAR_VEST = "R"
G_GOGGLES = "S"
G_MEDKIT = "T"
G_SILENCER = "U"
G_LASER_SIGHT = "V"
G_HELMET = "W"
G_EXTRA_AMMO = "X"

weapon_codes = (
    ('beretta', G_BERETTA_92FS),
    ('beret', G_BERETTA_92FS),
    ('ber', G_BERETTA_92FS),
    
    ('desert eagle', G_50_DESERT_EAGLE),
    ('desert', G_50_DESERT_EAGLE),
    ('des', G_50_DESERT_EAGLE),
    ('.50', G_50_DESERT_EAGLE),
    ('deagle', G_50_DESERT_EAGLE),
    ('eagle', G_50_DESERT_EAGLE),
    
    ('spas12', G_SPAS_12),
    ('spas', G_SPAS_12),
    
    ('mp5k', G_MP5K),
    ('mp5', G_MP5K),
    ('mp', G_MP5K),

    ('ump45', G_UMP45),
    ('ump', G_UMP45),

    ('hk69', G_HK69),
    ('hk', G_HK69),

    ('lr300ml', G_LR300ML),
    ('lr300', G_LR300ML),
    ('lr', G_LR300ML),

    ('g36', G_G36),

    ('psg1', G_PSG1),
    ('psg', G_PSG1),

    ('sr8', G_SR8),
    ('sr', G_SR8),

    ('ak103', G_AK103),
    ('ak', G_AK103),

    ('negev', G_NEGEV_LMG),
    ('neg', G_NEGEV_LMG),

    ('m4', G_COLT_M4),

    ('glock', G_GLOCK),
    ('gloc', G_GLOCK),
    ('glok', G_GLOCK),
    ('glo', G_GLOCK),

    ('colt1911', G_COLT1911),
    ('1911', G_COLT1911),

    ('mac11', G_MAC11),
    ('mac', G_MAC11),

    ('he grenade', G_HE_GRENADE),
    ('he', G_HE_GRENADE),

    ('smoke grenade', G_SMOKE_GRENADE),
    ('smoke', G_SMOKE_GRENADE),
    ('smo', G_SMOKE_GRENADE),

    ('kevlar vest', G_KEVLAR_VEST),
    ('kevlar', G_KEVLAR_VEST),
    ('kev', G_KEVLAR_VEST),
    ('vest', G_KEVLAR_VEST),

    ('goggles', G_GOGGLES),
    ('gog', G_GOGGLES),
    ('nvg', G_GOGGLES),

    ('medkit', G_MEDKIT),
    ('med', G_MEDKIT),

    ('silencer', G_SILENCER),
    ('sil', G_SILENCER),

    ('laser sight', G_LASER_SIGHT),
    ('laser', G_LASER_SIGHT),
    ('las', G_LASER_SIGHT),

    ('helmet', G_HELMET),
    ('hel', G_HELMET),

    ('extra ammo', G_EXTRA_AMMO),
    ('extra', G_EXTRA_AMMO),
    ('ext', G_EXTRA_AMMO),
    ('ammo', G_EXTRA_AMMO),
    ('amm', G_EXTRA_AMMO),
)


def all_gear_but(*args):
    return "".join(sorted(G_ALL.translate(None, "".join(args))))


def only_gear(*args):
    return "".join(sorted(G_ALL.translate(None, all_gear_but(*args))))


class Test_cmd_pagear(Iourt42TestCase):

    def setUp(self):
        super(Test_cmd_pagear, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
pagear-gear: 20
        """)
        self.p = PoweradminurtPlugin(self.console, self.conf)

        when(self.console).getCvar('timelimit').thenReturn(Cvar('timelimit', value=20))
        when(self.console).getCvar('g_maxGameClients').thenReturn(Cvar('g_maxGameClients', value=16))
        when(self.console).getCvar('sv_maxclients').thenReturn(Cvar('sv_maxclients', value=16))
        when(self.console).getCvar('sv_privateClients').thenReturn(Cvar('sv_privateClients', value=0))
        when(self.console).getCvar('g_allowvote').thenReturn(Cvar('g_allowvote', value=0))
        when(self.console).getCvar('g_modversion').thenReturn(Cvar('g_modversion', value="4.2.018"))
        self.given_forbidden_weapon_are(G_NONE)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.sleep_patcher = patch.object(time, 'sleep')
        self.sleep_patcher.start()
        self.setCvar_patcher = patch.object(self.console, 'setCvar')
        self.setCvar_mock = self.setCvar_patcher.start()

        self.superadmin.connects("2")

    def tearDown(self):
        super(Test_cmd_pagear, self).tearDown()
        self.sleep_patcher.stop()
        self.setCvar_patcher.stop()

    def given_forbidden_weapon_are(self, g_gear_value):
        when(self.console).getCvar('g_gear').thenReturn(Cvar('g_gear', value=str(g_gear_value)))

    def assert_set_gear(self, expected_gear_value, fail_message=None):
        self.assertListEqual([call('g_gear', str(expected_gear_value))], self.setCvar_mock.mock_calls, fail_message)

    def test_no_parameter(self):
        # GIVEN
        self.given_forbidden_weapon_are(G_NONE)
        self.p.onStartup()
        # WHEN
        self.superadmin.message_history = []
        self.superadmin.says("!gear")
        # THEN
        self.assertListEqual(["current gear: med:ON, vest:ON, ak:ON, de:ON, psg:ON, nvg:ON, hk:ON, mac:ON, mp5:ON, las:ON, ber:ON, ump:ON, g36:ON, neg:ON, glo:ON, smo:ON, m4:ON, lr:ON, hel:ON, spas:ON, sr8:ON, he:ON, colt:ON, ammo:ON, sil:ON",
                              "Usage: !pagear [+/-][med|vest|ak|de|psg|nvg|hk|mac|mp5|las|ber|ump|g36|neg|glo|smo|m4|lr|hel|spas|sr8|he|colt|ammo|sil]",
                              "Load weapon groups: !pagear [+/-][all_nades|all_auto|all_pistols|all_snipers]",
                              "Load defaults: !pagear [reset|all|none]"],
                              self.superadmin.message_history)

    def test_reset(self):
        # GIVEN
        self.given_forbidden_weapon_are("1234")
        self.p.onStartup()
        # WHEN
        self.superadmin.says("!gear reset")
        # THEN
        self.assert_set_gear('1234')

    def test_all(self):
        # WHEN
        self.superadmin.says("!gear all")
        # THEN
        self.assert_set_gear(G_NONE)

    def test_none(self):
        # WHEN
        self.superadmin.says("!gear none")
        # THEN
        self.assert_set_gear(G_ALL)

    def test_unknown_weapon(self):
        # WHEN
        self.superadmin.says("!gear +f00")
        # THEN
        self.assertListEqual([], self.setCvar_mock.mock_calls)
        self.assertListEqual([
            "could not recognize weapon/item 'f00'",
            "gear not changed"
        ], self.superadmin.message_history)

    def test_disallow_negev(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_NONE)
        # WHEN
        self.superadmin.says("!gear -neg")
        # THEN
        self.assert_set_gear(G_NEGEV_LMG)

    def test_allow_negev_short(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear +neg")
        # THEN
        self.assert_set_gear(all_gear_but(G_NEGEV_LMG))

    def test_allow_negev_long(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear +negev")
        # THEN
        self.assert_set_gear(all_gear_but(G_NEGEV_LMG))

    def test_allow_negev_long_spaced(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear + negev")
        # THEN
        self.assert_set_gear(all_gear_but(G_NEGEV_LMG))

    def test_disallow(self):
        for weapon_name, weapon_code in weapon_codes:
            # GIVEN
            self.setCvar_mock.reset_mock()
            self.given_forbidden_weapon_are(G_NONE)
            # WHEN
            self.superadmin.says("!gear -%s" % weapon_name)
            # THEN
            self.assert_set_gear(weapon_code, weapon_name)

    def test_allow(self):
        for weapon_name, weapon_code in weapon_codes:
            # GIVEN
            self.setCvar_mock.reset_mock()
            self.given_forbidden_weapon_are(G_ALL)
            # WHEN
            self.superadmin.says("!gear +%s" % weapon_name)
            # THEN
            self.assert_set_gear(all_gear_but(weapon_code), weapon_name)

    def test_allow_group_nades(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear +all_nades")
        # THEN
        self.assert_set_gear(all_gear_but(G_SMOKE_GRENADE, G_HE_GRENADE))

    def test_disallow_group_nades(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_NONE)
        # WHEN
        self.superadmin.says("!gear -all_nades")
        # THEN
        self.assert_set_gear(only_gear(G_SMOKE_GRENADE, G_HE_GRENADE))

    def test_disallow_group_nades_spaced(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_NONE)
        # WHEN
        self.superadmin.says("!gear - all_nades")
        # THEN
        self.assert_set_gear(only_gear(G_SMOKE_GRENADE, G_HE_GRENADE))

    def test_allow_all_snipers(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear +all_snipers")
        # THEN
        self.assert_set_gear(all_gear_but(G_SR8, G_PSG1))

    def test_disallow_all_snipers(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_NONE)
        # WHEN
        self.superadmin.says("!gear -all_snipers")
        # THEN
        self.assert_set_gear(only_gear(G_SR8, G_PSG1))

    def test_allow_all_pistols(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear +all_pistols")
        # THEN
        self.assert_set_gear(all_gear_but(G_BERETTA_92FS, G_50_DESERT_EAGLE, G_GLOCK, G_COLT1911))

    def test_disallow_all_pistols(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_NONE)
        # WHEN
        self.superadmin.says("!gear -all_pistols")
        # THEN
        self.assert_set_gear(only_gear(G_BERETTA_92FS, G_50_DESERT_EAGLE, G_GLOCK, G_COLT1911))

    def test_allow_all_auto(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear +all_auto")
        # THEN
        self.assert_set_gear(all_gear_but(G_MP5K, G_LR300ML, G_COLT_M4, G_MAC11, G_UMP45, G_G36, G_AK103, G_NEGEV_LMG))

    def test_disallow_all_auto(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_NONE)
        # WHEN
        self.superadmin.says("!gear -all_auto")
        # THEN
        self.assert_set_gear(only_gear(G_MP5K, G_LR300ML, G_COLT_M4, G_MAC11, G_UMP45, G_G36, G_AK103, G_NEGEV_LMG))

    def test_disallow_all_auto_and_no_smoke(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear all -all_auto -smoke")
        # THEN
        self.assert_set_gear(only_gear(G_MP5K, G_LR300ML, G_COLT_M4, G_MAC11, G_UMP45, G_G36, G_AK103, G_NEGEV_LMG, G_SMOKE_GRENADE))

    def test_disallow_all_auto_and_no_smoke_spaced(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear all - all_auto - smoke")
        # THEN
        self.assert_set_gear(only_gear(G_MP5K, G_LR300ML, G_COLT_M4, G_MAC11, G_UMP45, G_G36, G_AK103, G_NEGEV_LMG, G_SMOKE_GRENADE))

    def test_disallow_all_auto_but_lr300(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear all -all_auto +lr")
        # THEN
        self.assert_set_gear(only_gear(G_MP5K, G_COLT_M4, G_MAC11, G_UMP45, G_G36, G_AK103, G_NEGEV_LMG))

    def test_disallow_all_auto_but_lr300_spaced(self):
       # GIVEN
        self.given_forbidden_weapon_are(G_ALL)
        # WHEN
        self.superadmin.says("!gear all - all_auto + lr")
        # THEN
        self.assert_set_gear(only_gear(G_MP5K, G_COLT_M4, G_MAC11, G_UMP45, G_G36, G_AK103, G_NEGEV_LMG))