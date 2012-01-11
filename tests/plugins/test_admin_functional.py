#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette
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

from mock import Mock, patch
import unittest

import b3

from b3.fake import FakeConsole, FakeClient
from b3.config import XmlConfigParser
from b3.plugins.admin import AdminPlugin

from tests import B3TestCase

class Admin_functional_test(B3TestCase):

    @classmethod
    def setUpClass(cls):

        cls.fakeConsole = FakeConsole('@b3/conf/b3.distribution.xml')
        cls.conf = XmlConfigParser()
        cls.conf.setXml(r"""
            <configuration plugin="admin">
                <settings name="commands">
                    <set name="enable">100</set>
                    <set name="disable">100</set>
                    <set name="die">100</set>
                    <set name="reconfig">100</set>
                    <set name="restart">100</set>
                    <set name="mask">100</set>
                    <set name="unmask">100</set>
                    <set name="runas-su">100</set>

                    <set name="pause">90</set>
                    <set name="rebuild">90</set>
                    <set name="clientinfo">90</set>
                    <set name="putgroup">90</set>
                    <set name="ungroup">90</set>

                    <set name="permban-pb">80</set>
                    <set name="map">80</set>
                    <set name="maprotate">80</set>
                    <set name="warnclear-wc">80</set>
                    <set name="clear-kiss">80</set>
                    <set name="lookup-l">80</set>
                    <set name="makereg-mr">80</set>
                    <set name="spankall-sall">80</set>
                    <set name="banall-ball">80</set>
                    <set name="kickall-kall">80</set>
                    <set name="pbss">80</set>

                    <set name="ban-b">60</set>
                    <set name="unban">60</set>
                    <set name="spank-sp">60</set>

                    <set name="tempban-tb">40</set>
                    <set name="baninfo-bi">40</set>
                    <set name="kick-k">40</set>
                    <set name="admintest">40</set>
                    <set name="scream">40</set>
                    <set name="notice">40</set>

                    <set name="find">20</set>
                    <set name="aliases-alias">20</set>
                    <set name="warns">20</set>
                    <set name="warninfo-wi">20</set>
                    <set name="warnremove-wr">20</set>
                    <set name="warn-w">20</set>
                    <set name="warntest-wt">20</set>
                    <set name="spams">20</set>
                    <set name="spam-s">20</set>
                    <set name="list">20</set>
                    <set name="admins">20</set>
                    <set name="say">20</set>
                    <set name="status">20</set>
                    <set name="leveltest-lt">20</set>
                    <set name="poke">20</set>

                    <set name="b3">9</set>

                    <set name="seen">2</set>
                    <set name="maps">2</set>
                    <set name="nextmap">2</set>

                    <set name="regtest">1</set>
                    <set name="time">1</set>

                    <set name="help-h">0</set>
                    <set name="register">0</set>
                    <set name="rules-r">0</set>
                </settings>
                <settings name="settings">
                <!-- noreason_level : admin from this level are not required to specify a reason when giving penalties to players -->
                    <set name="noreason_level">100</set>
                    <!-- hidecmd_level : level required to be able to use hidden commands. On quake3 based games, a hidden command can be issued by
                    telling to command to oneself -->
                    <set name="hidecmd_level">60</set>
                    <!-- long_tempban_level : admin level required to be able to issue bans longer than long_tempban_max_duration -->
                    <set name="long_tempban_level">80</set>
                    <!-- long_tempban_max_duration : maximum ban duration that can be inflicted by admin of level below long_tempban_level -->
                    <set name="long_tempban_max_duration">3h</set>
                    <!-- command_prefix : the prefix that should be put before b3 commands -->
                    <set name="command_prefix">!</set>
                    <!-- comamnd_prefix_loud : some commands can have their result broadcasted to the whole player crowed instead of only to
                    the player issuing the command. To have such a behavior, use this command prefix instead -->
                    <set name="command_prefix_loud">@</set>
                    <!-- command_prefix_big : some commands can have their result broadcasted to the whole player crowed as a bigtext.
                    To have such a behavior, use this command prefix instead -->
                    <set name="command_prefix_big"><![CDATA[&]]></set>
                    <!-- admins_level : minimum level for groups to consider as admins -->
                    <set name="admins_level">20</set>
                    <!-- ban_duration : tempban duration to apply to the !ban and !banall commands -->
                    <set name="ban_duration">14d</set>
                </settings>
                <settings name="messages">
                    <set name="ban_denied">^7Hey %s^7, you're no Elvis, can't ban %s</set>
                    <set name="help_available">^7Available commands: %s</set>
                    <set name="temp_ban_self">^7%s ^7Can't ban yourself newb</set>
                    <set name="groups_in">^7%s^7 is in groups %s</set>
                    <set name="say">^7%s^7: %s</set>
                    <set name="player_id">^7%s [^2%s^7]</set>
                    <set name="seen">^7%s ^7was last seen on %s</set>
                    <set name="help_no_command">^7Command not found %s</set>
                    <set name="lookup_found">^7[^2@%s^7] %s^7 [^3%s^7]</set>
                    <set name="kick_self">^7%s ^7Can't kick yourself newb!</set>
                    <set name="groups_welcome">^7You are now a %s</set>
                    <set name="warn_denied">%s^7, %s^7 owns you, can't warn</set>
                    <set name="groups_already_in">^7%s^7 is already in group %s</set>
                    <set name="temp_ban_denied">^7Hey %s^7, you're no ^1Red ^7Elvis, can't temp ban %s</set>
                    <set name="players_matched">^7Players matching %s %s</set>
                    <set name="ban_self">^7%s ^7Can't ban yourself newb!</set>
                    <set name="regme_annouce">^7%s ^7put in group %s</set>
                    <set name="kick_denied">^7%s^7 gets 1 point, %s^7 gets none, %s^7 wins, can't kick</set>
                    <set name="no_players">^7No players found matching %s</set>
                    <set name="spanked_reason">%s ^7was ^1SPANKED^7 by %s ^7for %s</set>
                    <set name="groups_added">^7%s ^7added to group %s</set>
                    <set name="groups_put">^7%s ^7put in group %s</set>
                    <set name="groups_none">^7%s^7 is not in any groups</set>
                    <set name="help_command">^2%s%s ^7%s</set>
                    <set name="warn_self">^7%s ^7Can't warn yourself newb!</set>
                    <set name="regme_regged">^7You are now a %s</set>
                    <set name="help_none">^7You have no available commands</set>
                    <set name="spanked">%s ^7was ^1SPANKED^7 by %s</set>
                    <set name="admins">^7Admins online: %s</set>
                    <set name="time">At the sound of the beep it will be ^3%s^7...(beeeep)</set>
                    <set name="unknown_command">^7Unrecognized command %s</set>
                    <set name="leveltest">^7%s ^7[^3@%s^7] is a ^3%s ^7[^2%s^7] since %s</set>
                    <set name="leveltest_nogroups">^7%s ^7[^3@%s^7] is not in any groups</set>
                    <set name="aliases">^7%s^7 aliases: %s</set>
                <set name="cmd_plugin_disabled">^7cannot execute command. Plugin disabled</set>
                </settings>
                <settings name="warn">
                    <!-- pm_global determines whether the warning is sent to the the whole server, or just the player and admin, to reduce chatbox spam.
            0 is whole server, 1 is private.
            -->
                    <set name="pm_global">0</set>
                    <!-- alert_kick_num : if a player reach this number of active warnings he will be notified by with message then tempbanned -->
                    <set name="alert_kick_num">3</set>
                    <!-- alert_kick_num : if a player reach this number of active warnings he will be tempbanned right away -->
                    <set name="instant_kick_num">5</set>
                    <!-- tempban_num : when the number of warnings goes over this limit, the player is tempban for tempban_duration -->
                    <set name="tempban_num">6</set>
                    <!-- tempban_duration : for how long to tempban a players whose number of warning exceeded tempban_num -->
                    <set name="tempban_duration">1d</set>
                    <!-- max_duration : when the bot decides to tempban (warning exceeding alert_kick_num) the ban duration is
                    computed from the duration of each of the active warnings but will never exceed max_duration -->
                    <set name="max_duration">1d</set>
                    <!-- message : template for building warning messages -->
                    <set name="message">^1WARNING^7 [^3$warnings^7]: $reason</set>
                    <!-- warn_delay : an given player cannot only be given one warning every warn_delay seconds -->
                    <set name="warn_delay">15</set>
                    <!-- reason : template for building warning message when a player exceeds the tolerated number of warnings -->
                    <set name="reason">^7too many warnings: $reason</set>
                    <!-- duration_divider : tempbanned duration is computed from the sum of all active warnings durations divided by duration_divider -->
                    <set name="duration_divider">30</set>
                    <!-- alert : when a player receives his last warning tolerated warning, this message is broadcasted so an admin can decide to clear it and
                    this teaches other players too -->
                    <set name="alert">^1ALERT^7: $name^7 auto-kick from warnings if not cleared [^3$warnings^7] $reason</set>
                <!-- warn_command_abusers will make the bot warn players who try to use command they don't have suffisent rights to use or warn
                players who try invalid commands  -->
                <set name="warn_command_abusers">yes</set>
                </settings>
                <settings name="spamages">
                <!-- You can define shortcuts to messages that can be used with the !spam command. Note if the message shortcut is of
                the form 'rule#' where # is a number between 1 and 20, they will be used for the !rules command. -->
                    <set name="vent">^3Ventrilo voice chat: ^269.93.232.106:3803 ^3password ^2nffoov^3, www.ventrilo.org</set>
                    <set name="join">^3Join Austin Server by signing up on the forums at www.austinserver.com</set>
                    <set name="forum">^3Visit the Austin Server forums at www.austinserver.com</set>
                    <set name="rtfm">^3RTFM! www.austinservers.com</set>
                    <set name="stack">^7No clan stacking, members must split evenly between the teams, go spectator and wait if you have to</set>

                    <set name="rule1">^3Rule #1: No racism of any kind</set>
                    <set name="rule2">^3Rule #2: No clan stacking, members must split evenly between the teams</set>
                    <set name="rule3">^3Rule #3: No arguing with admins (listen and learn or leave)</set>
                    <set name="rule4">^3Rule #4: No abusive language or behavior towards admins or other players</set>
                    <set name="rule5">^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names</set>
                    <set name="rule6">^3Rule #6: No recruiting for your clan, your server, or anything else</set>
                    <set name="rule7">^3Rule #7: No advertising or spamming of websites or servers</set>
                    <set name="rule8">^3Rule #8: No profanity or offensive language (in any language)</set>
                    <set name="rule9">^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning</set>
                    <set name="rule10">^3Rule #10: Offense players must play for the objective and support their team</set>
                </settings>
                <settings name="warn_reasons">
                  <!-- Define here shorcuts for warning reasons. Those shortcuts can be used with the !kick, !tempban, !ban, and !permban commands.
                  The format of warning reasons can be of the form "<duration>, <message>". The duration defines how long such a warning will
                  last before expiring. The message is what will be sent to the player.
                  NOTE : in the message, you can make reference to an existing spammage shortcut by using the form '/spam#<spammage keyword>'
                  NOTE2 : you can define warning shortcuts aliases if you don't use duration and the message is of the form '/<warn shortcut>'-->
                    <set name="generic">1h, ^7</set>
                    <set name="default">1h, ^7behave yourself</set>

                    <set name="rule1">10d, /spam#rule1</set>
                    <set name="rule2">1d, /spam#rule2</set>
                    <set name="rule3">1d, /spam#rule3</set>
                    <set name="rule4">1d, /spam#rule4</set>
                    <set name="rule5">1h, /spam#rule5</set>
                    <set name="rule6">1d, /spam#rule6</set>
                    <set name="rule7">1d, /spam#rule7</set>
                    <set name="rule8">3d, /spam#rule8</set>
                    <set name="rule9">3h, /spam#rule9</set>
                    <set name="rule10">3d, /spam#rule10</set>

                    <set name="stack">1d, /spam#stack</set>

                    <set name="lang">/rule8</set>
                    <set name="language">/rule8</set>
                    <set name="cuss">/rule8</set>
                    <set name="profanity">/rule8</set>

                    <set name="name">/rule5</set>
                    <set name="color">1h, ^7No in-game (double caret (^)) color in names</set>
                    <set name="badname">1h, ^7No offensive, potentially offensive, or annoying names</set>
                    <set name="spec">/spectator</set>


                    <set name="adv">/rule7</set>
                    <set name="racism">/rule1</set>
                    <set name="stack">/rule2</set>
                    <set name="recruit">/rule6</set>
                    <set name="argue">/rule3</set>
                    <set name="sfire">/rule9</set>
                    <set name="spawnfire">/rule9</set>
                    <set name="jerk">/rule4</set>

                    <set name="afk">5m, ^7you appear to be away from your keyboard</set>
                    <set name="tk">1d, ^7stop team killing!</set>
                    <set name="obj">1h, ^7go for the objective!</set>
                    <set name="camp">1h, ^7stop camping or you will be kicked!</set>
                    <set name="fakecmd">1h, ^7do not use fake commands</set>
                    <set name="nocmd">1h, ^7do not use commands that you do not have access to, try using !help</set>
                    <set name="ci">5m, ^7connection interupted, reconnect</set>
                    <set name="spectator">5m, ^7spectator too long on full server</set>
                    <set name="spam">1h, ^7do not spam, shut-up!</set>
                </settings>
            </configuration>
        """)

        cls.p = AdminPlugin(cls.fakeConsole, cls.conf)
        cls.p.onLoadConfig()
        cls.p.onStartup()


    def test_tempban_no_duration(self):
        joe = FakeClient(Admin_functional_test.fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=128, team=b3.TEAM_RED)
        mike = FakeClient(Admin_functional_test.fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_BLUE)

        joe.message = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.says('!tempban mike')
        joe.message.assert_called_with('^7Invalid parameters')


    def test_tempban_bad_duration(self):
        joe = FakeClient(Admin_functional_test.fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=128, team=b3.TEAM_RED)
        mike = FakeClient(Admin_functional_test.fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_BLUE)

        joe.message = Mock()
        joe.connects(0)
        mike.connects(1)
        mike.tempban = Mock()

        joe.says('!tempban mike 5hour')
        joe.message.assert_called_with('^7Invalid parameters')
        assert not mike.tempban.called


    def test_tempban_non_existing_player(self):
        joe = FakeClient(Admin_functional_test.fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=128, team=b3.TEAM_RED)
        mike = FakeClient(Admin_functional_test.fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_BLUE)

        joe.message = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.says('!tempban foo 5h')
        joe.message.assert_called_with('^7No players found matching foo')


    def test_tempban_no_reason(self):
        joe = FakeClient(Admin_functional_test.fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=128, team=b3.TEAM_RED)
        mike = FakeClient(Admin_functional_test.fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_BLUE)

        joe.message = Mock()
        joe.connects(0)
        mike.connects(1)
        mike.tempban = Mock()

        joe.says('!tempban mike 5h')
        mike.tempban.assert_called_with('', None, 5*60, joe)


if __name__ == '__main__':
    unittest.main()