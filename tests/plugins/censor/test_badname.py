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

from tests.plugins.censor import Detection_TestCase


class Test_Censor_badname(Detection_TestCase):
    """
    Test that bad names are detected.
    """

    def test_regexp(self):

        def my_info(text):
            print("INFO\t%s" % text)
        #self.p.info = my_info

        self.p._badNames = []
        self.assert_name_is_not_penalized('Joe')

        self.p._badNames = []
        self.p._add_bad_name(rulename='ass', regexp=r'\b[a@][s$]{2}\b')
        self.assert_name_is_penalized('ass')
        self.assert_name_is_penalized('a$s')
        self.assert_name_is_penalized(' a$s ')
        self.assert_name_is_penalized('kI$$ my a$s n00b')
        self.assert_name_is_penalized('right in the ass')


    def test_word(self):

        def my_info(text):
            print("INFO\t%s" % text)
        #self.p.info = my_info

        self.p._badNames = []
        self.assert_name_is_not_penalized('Joe')

        self.p._badNames = []
        self.p._add_bad_name(rulename='ass', word='ass')
        self.assert_name_is_penalized('ass')
        self.assert_name_is_penalized('dumb ass!')
        self.assert_name_is_penalized('what an ass')
