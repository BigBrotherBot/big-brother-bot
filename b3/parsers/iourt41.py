#
# ioUrT Parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2008 Mark Weirath (xlr8or@xlr8or.com)
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
#
# CHANGELOG
# v1.0.3 - Courgette added support for banlist.txt
#          xlr8or added parsing Damage (OnHit)
# v1.0.4 - xlr8or added EVT_CLIENT_TEAM_CHANGE in OnKill
# v1.0.5 - xlr8or added hitloc and damageType info to accomodate XLRstats
# v1.0.6 - Fixed a bug where the parser wouldn't parse the shutdowngame and warmup functions
# v1.0.7 - Better synchronizing and identification of connecting players and zombies
# v1.0.8 - Better Zombie handling (Zombies being a result of: sv_zombietime (default 2 seconds))
#          (Zombie time is the time after a disconnect that the slot cannot be used and thus is in Zombie state)
#          Added functionality to use ip's only, not using the guid at all (experimental)
# v1.0.9 - Try to get the map name at start
#           Provide getPlayerScores method
# v1.0.10 - Modified _reColor so name sanitation is the same as UrT. Here it does more than just remove color.
# v1.0.11 - Courgette - Add getScores  # NOTE: this won't work properly if the server has private slots. see http://forums.urbanterror.net/index.php/topic,9356.0.html
# v1.0.12 - Courgette - Fix regex that failed to parse chat lines when player's name ends with ':'
# v1.0.13 - xlr8or - support for !maps and !nextmap command
# v1.0.14 - xlr8or - better understanding of mapcycle.txt
# v1.0.15 - mindriot - 01-Nov-2008
# * client with empty name ("") resulted in error and B3 not registering client - now given _empty_name_default
# v1.0.16 - xlr8or - added IpCombi. Setting True will replace the last part of the guid with two segments of the ip
#                    Increases security on admins who have cl_guidServerUniq set to 0 in client config (No cloning).
# v1.0.17 - mindriot - 02-Nov-2008
# * _empty_name_default now only given upon client connect, due to possibility of no name specified in ClientUserinfo at any time
# v1.0.19 - xlr8or - Disabled PunkBuster default settings due to recent supportrequests in the forums with missing PB line in b3.xml
#
# v1.1.0 - xlr8or - Added Action Mechanism (event) for B3 v1.1.5+
# v1.1.1 - courgette
# * Debugged Action Mechanism (event) for B3 v1.1.5+
# v1.2.0 - 19/08/2009 - Courgette
# * adds slap, nuke, mute new custom penalty types (can be used in censor or admin plugin)
# * requires admin plugin v1.4+ and parser.py v1.10+
# v1.3.0 - 20/10/2009 - Courgette
# * upon bot start, already connected players are correctly recognized
# v1.4.0 - 26/10/2009 - Courgette
# * when no client is found by cid, try to join the player using /rcon dumpuser <cid>
# v1.5.0 - 11/11/2009 - Courgette
#    * create a new event: EVT_GAME_FLAG_RETURNED which is fired when the flag return because of time
#    * code refactoring
# v1.5.1 - 17/11/2009 - Courgette
#    * harden getNextMap by :
#      o wrapping initial getCvar queries with try:except bloc
#      o requerying required cvar if missing
#      o forcing map list refresh on server reload or round end
# v1.5.2 - 26/11/2009 - Courgette
#    * fix a bug that prevented kills by slap or nuke from firing kill events
# v1.6.1 - 30/11/2009 - Courgette
#    * separate parsing of lines ClientUserInfo and ClientUserInfoChanged to better translate 
#    ClientUserInfoChanged data. Also OnClientUserInfoChanged does not create new client if 
#    cid is unknown.
# v1.6.2 - 05/12/2009 - Courgette
#    * fix _rePlayerScore regexp
#    * on startup, also try to get players' team (which is not given by dumpuser)
# v1.6.3 - 06/12/2009 - Courgette
#    * harden queryClientUserInfoByCid making sure we got a positive response. (Never trust input data...)
#    * fix _rePlayerScore regexp again
# v1.6.4 - 06/12/2009 - Courgette
#    * sync() will retries to get player list up to 4 for times before giving up as
#      sync() after map change too often fail 2 times.
# v1.6.5 - 09/12/2009 - Courgette
#    * different handling of 'name' in OnClientuserinfo. Now log looks less worrying
#    * prevent exception on the rare case where a say line shows no text after cid (hence no regexp match)
# v1.7 - 21/12/2009 - Courgette
#    * add new UrT specific event : EVT_CLIENT_GEAR_CHANGE
# v1.7.1 - 30/12/2009 - Courgette
#    * Say, Sayteam and Saytell lines do not trigger name change anymore and detect the UrT bug described
#      in http://www.bigbrotherbot.net/forums/urt/b3-bot-sometimes-mix-up-client-id%27s/ . Hopefully this
#      definitely fixes the wrong aliases issue.
# v1.7.2 - 30/12/2009 - Courgette
#    * improve say lines slot bug detection for cases where no player exists on slot 0. 
#      Refactor detection code to follow the KISS rule (keep it simple and stupid)
# v1.7.3 - 31/12/2009 - Courgette
#    * fix bug getting client by name when UrT slot 0 bug 
#    * requires clients.py 1.2.8+
# v1.7.4 - 02/01/2010 - Courgette
#    * improve Urt slot bug woraround as it appears it can occur with slot num different than 0
# v1.7.5 - 05/01/2010 - Courgette
#    * fix minor bug in saytell
# v1.7.6 - 16/01/2010 - xlr8or
#    * removed maxRetries=4 keyword from getPlayerList()
# v1.7.7 - 16/01/2010 - Courgette
#    * put back maxRetries=4 keyword from getPlayerList(). @xlr8or: make sure you have the latest
#      q3a.py file (v1.3.1+) for maxRetries to work.
# v1.7.8 - 18/01/2010 - Courgette
#    * update getPlayerList and sync so that connecting players (CNCT) are not ignored.
#      This will allow to use commands like !ci or !kick on hanging players.
# v1.7.9 - 26/01/2010 - xlr8or
#    * moved getMap() to q3a.py
# v1.7.10 - 10/04/2010 - Bakes
#    * bigsay() function can be used by plugins.
# v1.7.11 - 15/04/2010 - Courgette
#    * add debugging info for getNextMap()
# v1.7.12 - 28/05/2010 - xlr8or
#    * connect bots
# v1.7.13 - 07/11/2010 - GrosBedo
#    * messages now support named $variables instead of %s
# v1.7.14 - 08/11/2010 - GrosBedo
#    * messages can now be empty (no message broadcasted on kick/tempban/ban/unban)
# v1.7.15 - 21/12/2010 - SGT
#    * fix CNCT ping error in getPlayersPings
#    * fix incorrect game type for ffa
#    * move getMapList after game initialization
# v1.7.16 - 09/04/2011 - Courgette
#    * reflect that cid are not converted to int anymore in the clients module
# v1.7.17 - 03/05/2011 - Courgette
#     * reflect changes in inflictCustomPenalty method signature
# v1.8.0 - 31/05/2011 - Courgette
#     * Damage event now carry correct damage points
#     * Damage event weapon code is now the same as the one used for Kill events
# v1.8.1 / 1.8.2 - 01/06/2011 - Courgette
#     * fix Damage points
#     * when game log provides hit info, Kill event will use last damage points instead of 100
# v1.9.0 - 2011-06-04 - Courgette
# makes use of the new pluginsStarted parser hook
# v1.10.0 - 2011-06-05 - Courgette
# * change data format for EVT_CLIENT_BAN events
# 14/06/2011 - 1.11.0 - Courgette
# * cvar code moved to q3a AbstractParser
# 12/09/2011 - 1.11.1 - Courgette
# * EVT_CLIENT_JOIN event is now triggered when player actually join a team
# * the call to self.clients.sync() that was made each round is now made on game init and in its own thread  
# 29/09/2011 - 1.11.2 - Courgette
# * fix MOD_TELEFRAG attacker on kill event to prevent people from being considered
#   as tkers in such cases.
# 15/10/2011 - 1.11.3 - Courgette
# * better team recognition of existing players at B3 start
# 15/11/2011 - 1.11.4 - Courgette
# * players's team get refreshed after unpausing the bot (useful when used with FTP and B3 lose the connection for a while)
#
__author__  = 'xlr8or, Courgette'
__version__ = '1.11.4'

from b3.parsers.q3a.abstractParser import AbstractParser
import re, string, threading, time, os, thread
import b3
import b3.events

#----------------------------------------------------------------------------------------------------------------------------------------------
class Iourt41Parser(AbstractParser):
    gameName = 'iourt41'
    IpsOnly = False
    IpCombi = False
    _maplist = None

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _empty_name_default = 'EmptyNameDefault'

    _commands = {}
    _commands['broadcast'] = '%(prefix)s^7 %(message)s'
    _commands['message'] = 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'
    _commands['saybig'] = 'bigtext "%(prefix)s %(message)s"'

    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'addip %(cid)s'
    _commands['tempban'] = 'clientkick %(cid)s'
    _commands['banByIp'] = 'addip %(ip)s'
    _commands['unbanByIp'] = 'removeip %(ip)s'
    _commands['slap'] = 'slap %(cid)s'
    _commands['nuke'] = 'nuke %(cid)s'
    _commands['mute'] = 'mute %(cid)s %(seconds)s'

    _eventMap = {
        #'warmup' : b3.events.EVT_GAME_WARMUP,
        #'shutdowngame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    #0:00 ClientUserinfo: 0:

    _lineFormats = (
        #Generated with ioUrbanTerror v4.1:
        #Hit: 12 7 1 19: BSTHanzo[FR] hit ercan in the Helmet
        #Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<hitloc>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>.*))$', re.IGNORECASE),
        #re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<hitloc>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>(?P<aname>[^:])\shit\s(?P<name>[^:])\sin\sthe(?P<locname>.*)))$', re.IGNORECASE),

        #6:37 Kill: 0 1 16: XLR8or killed =lvl1=Cheetah by UT_MOD_SPAS
        #2:56 Kill: 14 4 21: Qst killed Leftovercrack by UT_MOD_PSG1
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>.*))$', re.IGNORECASE),
        #re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>(?P<aname>[^:])\skilled\s(?P<name>[^:])\sby\s(?P<modname>.*)))$', re.IGNORECASE),

        #Processing chats and tell events...
        #5:39 saytell: 15 16 repelSteeltje: nno
        #5:39 saytell: 15 15 repelSteeltje: nno
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<name>[^ ]+):\s+(?P<text>.*))$', re.IGNORECASE),

        # We're not using tell in this form so this one is disabled
        #5:39 tell: repelSteeltje to B!K!n1: nno
        #re.compile(r'^(?P<action>[a-z]+):\s+(?P<data>(?P<name>[^:]+)\s+to\s+(?P<aname>[^:]+):\s+(?P<text>.*))$', re.IGNORECASE),

        #3:53 say: 8 denzel: lol
        #15:37 say: 9 .:MS-T:.BstPL: this name is quite a challenge
        #2:28 sayteam: 12 New_UrT_Player_v4.1: woekele
        #16:33 Flag: 2 0: team_CTF_redflag
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<name>[^ ]+):\s+(?P<text>.*))$', re.IGNORECASE),

        #15:42 Flag Return: RED
        #15:42 Flag Return: BLUE
        re.compile(r'^(?P<action>Flag Return):\s(?P<data>(?P<color>.+))$', re.IGNORECASE),

        #Bombmode actions:
        #3:06 Bombholder is 2
        re.compile(r'^(?P<action>Bombholder)(?P<data>\sis\s(?P<cid>[0-9]))$', re.IGNORECASE),
        #was planted, was defused, was tossed, has been collected (doh, how gramatically correct!)
        #2:13 Bomb was tossed by 2
        #2:32 Bomb was planted by 2
        #3:01 Bomb was defused by 3!
        #2:17 Bomb has been collected by 2
        re.compile(r'^(?P<action>Bomb)\s(?P<data>(was|has been)\s(?P<subaction>[a-z]+)\sby\s(?P<cid>[0-9]+).*)$', re.IGNORECASE),

        #Falling thru? Item stuff and so forth
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>.*)$', re.IGNORECASE),
        #Shutdowngame and Warmup... the one word lines
        re.compile(r'^(?P<action>[a-z]+):$', re.IGNORECASE)
    )

    # map: ut4_casa
    # num score ping name            lastmsg address               qport rate
    # --- ----- ---- --------------- ------- --------------------- ----- -----
    #   2     0   19 ^1XLR^78^8^9or^7        0 145.99.135.227:27960  41893  8000  # player with a live ping
    #   4     0 CNCT Dz!k^7                450 83.175.191.27:64459   50308 20000  # connecting player (or inbetween rounds)
    #   9     0 ZMBI ^7                   1900 81.178.80.68:27960    10801  8000  # zombies (need to be disconnected!)
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+|CNCT|ZMBI)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)
    _reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')

    # Map: ut4_algiers
    # Players: 8
    # Scores: R:97 B:98
    # 0:  FREE k:0 d:0 ping:0
    # 4: yene RED k:16 d:8 ping:50 92.104.110.192:63496
    _reTeamScores = re.compile(r'^Scores:\s+R:(?P<RedScore>.+)\s+B:(?P<BlueScore>.+)$', re.I)
    _rePlayerScore = re.compile(r'^(?P<slot>[0-9]+): (?P<name>.*) (?P<team>RED|BLUE|SPECTATOR|FREE) k:(?P<kill>[0-9]+) d:(?P<death>[0-9]+) ping:(?P<ping>[0-9]+|CNCT|ZMBI)( (?P<ip>[0-9.]+):(?P<port>[0-9-]+))?$', re.I) # NOTE: this won't work properly if the server has private slots. see http://forums.urbanterror.net/index.php/topic,9356.0.html


    PunkBuster = None

    ## kill modes
    MOD_WATER='1'
    MOD_LAVA='3'
    MOD_TELEFRAG='5'
    MOD_FALLING='6'
    MOD_SUICIDE='7'
    MOD_TRIGGER_HURT='9'
    MOD_CHANGE_TEAM='10'
    UT_MOD_KNIFE='12'
    UT_MOD_KNIFE_THROWN='13'
    UT_MOD_BERETTA='14'
    UT_MOD_DEAGLE='15'
    UT_MOD_SPAS='16'
    UT_MOD_UMP45='17'
    UT_MOD_MP5K='18'
    UT_MOD_LR300='19'
    UT_MOD_G36='20'
    UT_MOD_PSG1='21'
    UT_MOD_HK69='22'
    UT_MOD_BLED='23'
    UT_MOD_KICKED='24'
    UT_MOD_HEGRENADE='25'
    UT_MOD_SR8='28'
    UT_MOD_AK103='30'
    UT_MOD_SPLODED='31'
    UT_MOD_SLAPPED='32'
    UT_MOD_BOMBED='33'
    UT_MOD_NUKED='34'
    UT_MOD_NEGEV='35'
    UT_MOD_HK69_HIT='37'
    UT_MOD_M4='38'
    UT_MOD_FLAG='39'
    UT_MOD_GOOMBA='40'
    
    ## weapons id on Hit: lines are different than the one
    ## on the Kill: lines. Here the translation table
    hitweapon2killweapon = {
        1: UT_MOD_KNIFE,
        2: UT_MOD_BERETTA,
        3: UT_MOD_DEAGLE,
        4: UT_MOD_SPAS,
        5: UT_MOD_MP5K,
        6: UT_MOD_UMP45,
        8: UT_MOD_LR300,
        9: UT_MOD_G36,
        10: UT_MOD_PSG1,
        14: UT_MOD_SR8,
        15: UT_MOD_AK103,
        17: UT_MOD_NEGEV,
        19: UT_MOD_M4,
        21: UT_MOD_HEGRENADE,
        22: UT_MOD_KNIFE_THROWN,
    }

    """ From data provided by Garreth http://bit.ly/jf4QXc on http://bit.ly/krwBCv :

                                Head(0) Helmet(1)     Torso(2)     Kevlar(3)     Arms(4)    Legs(5)    Body(6)    Killed
    MOD_TELEFRAG='5'             0        0             0             0             0         0         0         0
    UT_MOD_KNIFE='12'           100      60            44            35            20        20        44        100
    UT_MOD_KNIFE_THROWN='13'    100      60            44            35            20        20        44        100
    UT_MOD_BERETTA='14'         100      34            30            20            11        11        30        100
    UT_MOD_DEAGLE='15'          100      66            57            38            22        22        57        100
    UT_MOD_SPAS='16'            25       25            25            25            25        25        25        100
    UT_MOD_UMP45='17'           100      51            44            29            17        17        44        100
    UT_MOD_MP5K='18'            50       34            30            20            11        11        30        100
    UT_MOD_LR300='19'           100      51            44            29            17        17        44        100
    UT_MOD_G36='20'             100      51            44            29            17        17        44        100
    UT_MOD_PSG1='21'            100      63            97            63            36        36        97        100
    UT_MOD_HK69='22'            50       50            50            50            50        50        50        100
    UT_MOD_BLED='23'            15       15            15            15            15        15        15        15
    UT_MOD_KICKED='24'          20       20            20            20            20        20        20        100
    UT_MOD_HEGRENADE='25'       50       50            50            50            50        50        50        100
    UT_MOD_SR8='28'             100      100           100           100           50        50        100       100
    UT_MOD_AK103='30'           100      58            51            34            19        19        51        100
    UT_MOD_NEGEV='35'           50       34            30            20            11        11        30        100
    UT_MOD_HK69_HIT='37'        20       20            20            20            20        20        20        100
    UT_MOD_M4='38'              100      51            44            29            17        17        44        100
    UT_MOD_GOOMBA='40'          100      100           100           100           100       100       100       100
    """
    damage = {
        MOD_TELEFRAG: [0, 0, 0, 0, 0, 0, 0, 0],
        UT_MOD_KNIFE: [100, 60, 44, 35, 20, 20, 44, 100],
        UT_MOD_KNIFE_THROWN: [100, 60, 44, 35, 20, 20, 44, 100],
        UT_MOD_BERETTA: [100, 34, 30, 20, 11, 11, 30, 100],
        UT_MOD_DEAGLE: [100, 66, 57, 38, 22, 22, 57, 100],
        UT_MOD_SPAS: [25, 25, 25, 25, 25, 25, 25, 100],
        UT_MOD_UMP45: [100, 51, 44, 29, 17, 17, 44, 100],
        UT_MOD_MP5K: [50, 34, 30, 20, 11, 11, 30, 100],
        UT_MOD_LR300: [100, 51, 44, 29, 17, 17, 44, 100],
        UT_MOD_G36: [100, 51, 44, 29, 17, 17, 44, 100],
        UT_MOD_PSG1: [100, 63, 97, 63, 36, 36, 97, 100],
        UT_MOD_HK69: [50, 50, 50, 50, 50, 50, 50, 100],
        UT_MOD_BLED: [15, 15, 15, 15, 15, 15, 15, 15],
        UT_MOD_KICKED: [20, 20, 20, 20, 20, 20, 20, 100],
        UT_MOD_HEGRENADE: [50, 50, 50, 50, 50, 50, 50, 100],
        UT_MOD_SR8: [100, 100, 100, 100, 50, 50, 100, 100],
        UT_MOD_AK103: [100, 58, 51, 34, 19, 19, 51, 100],
        UT_MOD_NEGEV: [50, 34, 30, 20, 11, 11, 30, 100],
        UT_MOD_HK69_HIT: [20, 20, 20, 20, 20, 20, 20, 100],
        UT_MOD_M4: [100, 51, 44, 29, 17, 17, 44, 100],
        UT_MOD_GOOMBA: [100, 100, 100, 100, 100, 100, 100, 100],
     }

    def startup(self):

        # add UrT specific events
        self.Events.createEvent('EVT_GAME_FLAG_RETURNED', 'Flag returned')
        self.Events.createEvent('EVT_CLIENT_GEAR_CHANGE', 'Client gear change')

        # add the world client
        self.clients.newClient('-1', guid='WORLD', name='World', hide=True, pbid='WORLD')

        # PunkBuster for iourt is not supported!
        #if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
        #    self.PunkBuster = b3.parsers.punkbuster.PunkBuster(self)

        # get map from the status rcon command
        map_name = self.getMap()
        if map_name:
            self.game.mapName = map_name
            self.info('map is: %s'%self.game.mapName)

        # get gamepaths/vars
        try:
            self.game.fs_game = self.getCvar('fs_game').getString()
        except:
            self.game.fs_game = None
            self.warning("Could not query server for fs_game")

        try:
            self.game.fs_basepath = self.getCvar('fs_basepath').getString().rstrip('/')
            self.debug('fs_basepath: %s' % self.game.fs_basepath)
        except:
            self.game.fs_basepath = None
            self.warning("Could not query server for fs_basepath")

        try:
            self.game.fs_homepath = self.getCvar('fs_homepath').getString().rstrip('/')
            self.debug('fs_homepath: %s' % self.game.fs_homepath)
        except:
            self.game.fs_homepath = None
            self.warning("Could not query server for fs_homepath")

        self._maplist = self.getMaps()

    def pluginsStarted(self):
        # initialize connected clients
        plist = self.getPlayerList()
        for cid in plist.keys():
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfo(None, userinfostring)
        
        player_teams = {}
        tries = 0
        while tries < 3:
            try:
                tries += 1
                player_teams = self.getPlayerTeams()
                break
            except Exception, err:
                if tries < 3:
                    self.warning(err)
                else:
                    self.error("cannot fix players teams : %s" % err) 
        for cid in plist.keys():
            client = self.clients.getByCID(cid)
            if client and client.cid in player_teams:
                newteam = player_teams[client.cid]
                if newteam != client.team:
                    self.debug('Fixing client team for %s : %s is now %s' % (client.name, client.team, newteam))
                    setattr(client, 'team', newteam)
            
    def unpause(self):
        self.pluginsStarted() # so we get teams refreshed
        self.clients.sync()
        b3.parser.Parser.unpause(self)

    def getLineParts(self, line):
        line = re.sub(self._lineClear, '', line, 1)

        for f in self._lineFormats:
            m = re.match(f, line)
            if m:
                #self.debug('line matched %s' % f.pattern)
                break

        if m:
            client = None
            target = None
            try:
                data = m.group('data').strip()
            except:
                data = None
            return (m, m.group('action').lower(), data, client, target)
        elif '------' not in line:
            self.verbose('line did not match format: %s' % line)

    def parseUserInfo(self, info):
        """Just extract the cid and pairs of key/value without any treatment"""
        #2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or\rate\8000\cg_predictitems\0\snaps\20\model\sarge\headmodel\sarge\team_model\james\team_headmodel\*james\color1\4\color2\5\handicap\100\sex\male\cl_anonymous\0\teamtask\0\cl_guid\58D4069246865BB5A85F20FB60ED6F65
        #7 n\[SNT]^1XLR^78or\t\3\r\2\tl\0\f0\\f1\\f2\\a0\0\a1\0\a2\0
        playerID, info = string.split(info, ' ', 1)

        if info[:1] != '\\':
            info = '\\' + info

        options = re.findall(r'\\([^\\]+)\\([^\\]+)', info)

        data = {}
        for o in options:
            data[o[0]] = o[1]

        data['cid'] = playerID
        return data


    def getTeam(self, team):
        if str(team).lower() == 'red':
            team = 1
        elif str(team).lower() == 'blue':
            team = 2
        elif str(team).lower() == 'spectator':
            team = 3
        elif str(team).lower() == 'free':
            team = -1 # will fall back to b3.TEAM_UNKNOWN
        
        team = int(team)
        if team == 1:
            result = b3.TEAM_RED
        elif team == 2:
            result = b3.TEAM_BLUE
        elif team == 3:
            result = b3.TEAM_SPEC
        else:
            result = b3.TEAM_UNKNOWN
            
        #self.debug('getTeam(%s) -> %s' % (team, result))
        return result

    # Translate the gameType to a readable format (also for teamkill plugin!)
    def defineGameType(self, gameTypeInt):

        _gameType = ''
        _gameType = str(gameTypeInt)
        #self.debug('gameTypeInt: %s' % gameTypeInt)

        if gameTypeInt == '0':
            _gameType = 'ffa'
        elif gameTypeInt == '1':   # Dunno what this one is
            _gameType = 'dm'
        elif gameTypeInt == '2':   # Dunno either
            _gameType = 'dm'
        elif gameTypeInt == '3':
            _gameType = 'tdm'
        elif gameTypeInt == '4':
            _gameType = 'ts'
        elif gameTypeInt == '5':
            _gameType = 'ftl'
        elif gameTypeInt == '6':
            _gameType = 'cah'
        elif gameTypeInt == '7':
            _gameType = 'ctf'
        elif gameTypeInt == '8':
            _gameType = 'bm'

        #self.debug('_gameType: %s' % _gameType)
        return _gameType

    # self.console.broadcast, a variant on self.console.say in UrT. This will print to upper left, the server message area.
    def broadcast(self, msg):
        lines = []
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            lines.append(self.getCommand('broadcast', prefix=self.msgPrefix, message=line))

        if len(lines):
            self.writelines(lines)

    def saybig(self, msg):
        lines = []
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            lines.append(self.getCommand('saybig', prefix=self.msgPrefix, message=line))

        if len(lines):
            self.writelines(lines)

    def inflictCustomPenalty(self, type, client, reason=None, duration=None, admin=None, data=None):
        if type == 'slap' and client:
            cmd = self.getCommand('slap', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif type == 'nuke' and client:
            cmd = self.getCommand('nuke', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif type == 'mute' and client:
            if duration is None:
                seconds = 60
            else:
                seconds = round(float(b3.functions.time2minutes(duration) * 60), 0)

            # make sure to unmute first
            cmd = self.getCommand('mute', cid=client.cid, seconds=0)
            self.write(cmd)
            # then mute
            cmd = self.getCommand('mute', cid=client.cid, seconds=seconds)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        # elif type == 'morron' and client:
            # client.message('you morron')
            # return True



#----------------------------------------------------------------------------------

    # Connect/Join
    def OnClientconnect(self, action, data, match=None):
        self.debug('Client Connected - ready to parse Userinfoline')
        #client = self.clients.getByCID(data)
        #return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)

    def OnClientbegin(self, action, data, match=None):
        # we get user info in two parts:
        # 19:42.36 ClientBegin: 4
        client = self.getByCidOrJoinPlayer(data)
        if client:
            return b3.events.Event(b3.events.EVT_CLIENT_JOIN, data=data, client=client)

    # Parse Userinfo
    def OnClientuserinfo(self, action, data, match=None):
        #2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or\rate\8000\cg_predictitems\0\snaps\20\model\sarge\headmodel\sarge\team_model\james\team_headmodel\*james\color1\4\color2\5\handicap\100\sex\male\cl_anonymous\0\teamtask\0\cl_guid\58D4069246865BB5A85F20FB60ED6F65
        #conecting bot:
        #0 \gear\GMIORAA\team\blue\skill\5.000000\characterfile\bots/ut_chicken_c.c\color\4\sex\male\race\2\snaps\20\rate\25000\name\InviteYourFriends!
        bclient = self.parseUserInfo(data)
        
        if not bclient.has_key('cl_guid') and bclient.has_key('skill'):
            # must be a bot connecting
            self.bot('Bot Connecting!')
            bclient['ip'] = '0.0.0.0'
            bclient['cl_guid'] = 'BOT' + str(bclient['cid'])

        if bclient.has_key('name'):
            # remove spaces from name
            bclient['name'] = bclient['name'].replace(' ','')


        # split port from ip field
        if bclient.has_key('ip'):
            ipPortData = string.split(bclient['ip'], ':', 1)
            bclient['ip'] = ipPortData[0]
            if len(ipPortData) > 1:
                bclient['port'] = ipPortData[1] 

        if bclient.has_key('team'):
            bclient['team'] = self.getTeam(bclient['team'])

        if bclient.has_key('cl_guid') and not bclient.has_key('pbid') and self.PunkBuster:
            bclient['pbid'] = bclient['cl_guid']

        self.verbose('Parsed user info %s' % bclient)
        
        if bclient:
            client = self.clients.getByCID(bclient['cid'])

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    if hasattr(client, 'gear') and k == 'gear' and client.gear != v:
                        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_GEAR_CHANGE, v, client))
                    setattr(client, k, v)
            else:
                #make a new client
                if self.PunkBuster:
                    # we will use punkbuster's guid
                    guid = None
                else:
                    # use io guid
                    if bclient.has_key('cl_guid'):
                        guid = bclient['cl_guid']
                    else:
                        guid = 'unknown'

                # v1.0.17 - mindriot - 02-Nov-2008
                if not bclient.has_key('name'):
                    bclient['name'] = self._empty_name_default

                if not bclient.has_key('ip') and guid == 'unknown':
                    # happens when a client is (temp)banned and got kicked so client was destroyed, but
                    # infoline was still waiting to be parsed.
                    self.debug('Client disconnected. Ignoring.')
                    return None

                nguid = ''
                # overide the guid... use ip's only if self.console.IpsOnly is set True.
                if self.IpsOnly:
                    nguid = bclient['ip']
                # replace last part of the guid with two segments of the ip
                elif self.IpCombi:
                    i = bclient['ip'].split('.')
                    d = len(i[0])+len(i[1])
                    nguid = guid[:-d]+i[0]+i[1]
                # Quake clients don't have a cl_guid, we'll use ip instead
                elif guid == 'unknown':
                    nguid = bclient['ip']

                if nguid != '':
                    guid = nguid

                client = self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'], state=b3.STATE_ALIVE, guid=guid, data={ 'guid' : guid })

        return None

    # when userinfo changes
    def OnClientuserinfochanged(self, action, data, match=None):
        #7 n\[SNT]^1XLR^78or\t\3\r\2\tl\0\f0\\f1\\f2\\a0\0\a1\0\a2\0
        parseddata = self.parseUserInfo(data)

        if parseddata:
            client = self.clients.getByCID(parseddata['cid'])

            if client:
                # update existing client
                if parseddata.has_key('n'):
                    setattr(client, 'name', parseddata['n'])
                
                if parseddata.has_key('t'):
                    team = self.getTeam(parseddata['t'])
                    setattr(client, 'team', team)
                
                    if parseddata.has_key('r'):
                        if team == b3.TEAM_BLUE:
                            setattr(client, 'raceblue', parseddata['r'])
                        elif team == b3.TEAM_RED:
                            setattr(client, 'racered', parseddata['r'])
                    if parseddata.has_key('f0') and parseddata['f0'] is not None \
                            and parseddata.has_key('f1') and parseddata['f1'] is not None \
                            and parseddata.has_key('f2') and parseddata['f2'] is not None :
                        data = "%s,%s,%s" % (parseddata['f0'], parseddata['f1'], parseddata['f2'])
                        if team == b3.TEAM_BLUE:
                            setattr(client, 'funblue', data)
                        elif team == b3.TEAM_RED:
                            setattr(client, 'funred', data)
                        
                if parseddata.has_key('a0') and parseddata.has_key('a1') and parseddata.has_key('a2'):
                    setattr(client, 'cg_rgb', "%s %s %s" % (parseddata['a0'], parseddata['a1'], parseddata['a2']))
                    
        return None

    # damage
    #Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
    #Hit: cid acid hitloc aweap: text
    def OnHit(self, action, data, match=None):
        victim = self.clients.getByCID(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnClientuserinfo(action, data, match)
            return None

        attacker = self.clients.getByCID(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        event = b3.events.EVT_CLIENT_DAMAGE

        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_DAMAGE_SELF
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_DAMAGE_TEAM

        hitloc = match.group('hitloc')
        weapon = self._convertHitWeaponToKillWeapon(match.group('aweap'))
        points = self._getDamagePoints(weapon, hitloc)
        event_data = (points, weapon, hitloc)
        victim.data['lastDamageTaken'] = event_data
        #victim.state = b3.STATE_ALIVE
        # need to pass some amount of damage for the teamkill plugin - 15 seems okay
        return self.getEvent(event, event_data, attacker, victim)

    # kill
    #6:37 Kill: 0 1 16: XLR8or killed =lvl1=Cheetah by UT_MOD_SPAS
    #6:37 Kill: 7 7 10: Mike_PL killed Mike_PL by MOD_CHANGE_TEAM
    #kill: acid cid aweap: <text>
    def OnKill(self, action, data, match=None):
        # kill modes caracteristics :
        """
        1:      MOD_WATER === exclusive attackers : , 1022(<world>), 0(<non-client>)
        3:      MOD_LAVA === exclusive attackers : , 1022(<world>), 0(<non-client>)
        5:      MOD_TELEFRAG --- normal kill line
        6:      MOD_FALLING === exclusive attackers : , 1022(<world>), 0(<non-client>)
        7:      MOD_SUICIDE ===> attacker is always the victim
        9:      MOD_TRIGGER_HURT === exclusive attackers : , 1022(<world>)
        10:     MOD_CHANGE_TEAM ===> attacker is always the victim
        12:     UT_MOD_KNIFE --- normal kill line
        13:     UT_MOD_KNIFE_THROWN --- normal kill line
        14:     UT_MOD_BERETTA --- normal kill line
        15:     UT_MOD_DEAGLE --- normal kill line
        16:     UT_MOD_SPAS --- normal kill line
        17:     UT_MOD_UMP45 --- normal kill line
        18:     UT_MOD_MP5K --- normal kill line
        19:     UT_MOD_LR300 --- normal kill line
        20:     UT_MOD_G36 --- normal kill line
        21:     UT_MOD_PSG1 --- normal kill line
        22:     UT_MOD_HK69 --- normal kill line
        23:     UT_MOD_BLED --- normal kill line
        24:     UT_MOD_KICKED --- normal kill line
        25:     UT_MOD_HEGRENADE --- normal kill line
        28:     UT_MOD_SR8 --- normal kill line
        30:     UT_MOD_AK103 --- normal kill line
        31:     UT_MOD_SPLODED ===> attacker is always the victim
        32:     UT_MOD_SLAPPED ===> attacker is always the victim
        33:     UT_MOD_BOMBED --- normal kill line
        34:     UT_MOD_NUKED --- normal kill line
        35:     UT_MOD_NEGEV --- normal kill line
        37:     UT_MOD_HK69_HIT --- normal kill line
        38:     UT_MOD_M4 --- normal kill line
        39:     UT_MOD_FLAG === exclusive attackers : , 0(<non-client>)
        40:     UT_MOD_GOOMBA --- normal kill line
        """
        self.debug('OnKill: %s (%s)'%(match.group('aweap'),match.group('text')))

        victim = self.getByCidOrJoinPlayer(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnClientuserinfo(action, data, match)
            return None

        weapon = match.group('aweap')
        if not weapon:
            self.debug('No weapon')
            return None

        ## Fix attacker
        if match.group('aweap') in (self.UT_MOD_SLAPPED, self.UT_MOD_NUKED, self.MOD_TELEFRAG):
            self.debug('OnKill: slap/nuke => attacker should be None')
            attacker = self.clients.getByCID(-1) # make the attacker 'World'
        elif match.group('aweap') in (self.MOD_WATER,self.MOD_LAVA,self.MOD_FALLING,self.MOD_TRIGGER_HURT,self.UT_MOD_BOMBED,self.UT_MOD_FLAG):
            # those kills should be considered suicides
            self.debug('OnKill: water/lava/falling/trigger_hurt/bombed/flag should be suicides')
            attacker = victim
        else:
            attacker = self.getByCidOrJoinPlayer(match.group('acid'))
        ## end fix attacker

        if not attacker:
            self.debug('No attacker')
            return None

        dType = match.group('text').split()[-1:][0]
        if not dType:
            self.debug('No damageType, weapon: %s' % weapon)
            return None

        event = b3.events.EVT_CLIENT_KILL

        # fix event for team change and suicides and tk
        if attacker.cid == victim.cid:
            if weapon == self.MOD_CHANGE_TEAM:
                """
                Do not pass a teamchange event here. That event is passed
                shortly after the kill.
                """
                self.verbose('Team Change Event Caught, exiting')
                return None
            else:
                event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        # if not logging damage we need a general hitloc (for xlrstats)
        if 'lastDamageTaken' in victim.data:
            lastDamageData = victim.data['lastDamageTaken']
            del victim.data['lastDamageTaken']
        else:
            lastDamageData = (100, weapon, 'body')

        victim.state = b3.STATE_DEAD
        #self.verbose('OnKill Victim: %s, Attacker: %s, Weapon: %s, Hitloc: %s, dType: %s' % (victim.name, attacker.name, weapon, victim.hitloc, dType))
        # need to pass some amount of damage for the teamkill plugin - 100 is a kill
        return self.getEvent(event, (lastDamageData[0], weapon, lastDamageData[2], dType), attacker, victim)

    # disconnect
    def OnClientdisconnect(self, action, data, match=None):
        client = self.clients.getByCID(data)
        if client: client.disconnect()
        return None

#--- Action Mechanism (new in B3 version 1.1.5) --------------------------------
    def OnFlag(self, action, data, match=None):
        #Flag: 1 2: team_CTF_blueflag
        #Flag: <_cid> <_subtype:0/1/2>: <text>
        _cid = match.group('cid')
        _subtype = int(match.group('name'))
        data = match.group('text')

        if _subtype == 0:
            _actiontype = 'flag_dropped'
        elif _subtype == 1:
            _actiontype = 'flag_returned'
        elif _subtype == 2:
            _actiontype = 'flag_captured'
        else:
            return None
        return self.OnAction(_cid, _actiontype, data)

    def OnFlagReturn(self, action, data, match=None):
        #Flag Return: RED
        #Flag Return: BLUE
        #Flag Return: <color>
        color = match.group('color')
        return b3.events.Event(b3.events.EVT_GAME_FLAG_RETURNED, color)

    def OnBomb(self, action, data, match=None):
        _cid = match.group('cid')
        _subaction = match.group('subaction')
        if _subaction == 'planted':
            _actiontype = 'bomb_planted'
        elif _subaction == 'defused':
            _actiontype = 'bomb_defused'
        elif _subaction == 'tossed':
            _actiontype = 'bomb_tossed'
        elif _subaction == 'collected':
            _actiontype = 'bomb_collected'
        else:
            return None
        return self.OnAction(_cid, _actiontype, data)

    def OnBombholder(self, action, data, match=None):
        _cid = match.group('cid')
        _actiontype = 'bomb_holder_spawn'
        return self.OnAction(_cid, _actiontype, data)

    # Action
    def OnAction(self, cid, actiontype, data, match=None):
        #Need example
        client = self.clients.getByCID(cid)
        if not client:
            self.debug('No client found')
            return None
        self.verbose('OnAction: %s: %s %s' % (client.name, actiontype, data) )
        return b3.events.Event(b3.events.EVT_CLIENT_ACTION, actiontype, client)

    # item
    def OnItem(self, action, data, match=None):
        #Item: 3 ut_item_helmet
        #Item: 0 team_CTF_redflag
        cid, item = string.split(data, ' ', 1)
        client = self.getByCidOrJoinPlayer(cid)
        if client:
            #correct flag/bomb-pickups
            if 'flag' in item or 'bomb' in item:
                self.verbose('Itempickup corrected to action: %s' %item)
                return self.OnAction(cid, item, data)
            #self.verbose('OnItem: %s picked up %s' % (client.name, item) )
            return b3.events.Event(b3.events.EVT_CLIENT_ITEM_PICKUP, item, client)
        return None

#-------------------------------------------------------------------------------
    # say
    def OnSay(self, action, data, match=None):
        #3:53 say: 8 denzel: lol
        
        if match is None:
            return
        
        name = self.stripColors(match.group('name'))
        cid = int(match.group('cid'))
        client = self.getByCidOrJoinPlayer(match.group('cid'))

        if not client or client.name != name:
            self.debug('UrT bug spotted. Trying to get client by name')
            client = self.clients.getByName(name)

        if not client:
            self.verbose('No Client Found!')
            return None
                
        self.verbose('Client Found: %s on slot %s' % (client.name, client.cid))
        
        data = match.group('text')

        #removal of weird characters
        if data and ord(data[:1]) == 21:
            data = data[1:]

        return b3.events.Event(b3.events.EVT_CLIENT_SAY, data, client)


    # sayteam
    def OnSayteam(self, action, data, match=None):
        #2:28 sayteam: 12 New_UrT_Player_v4.1: wokele
        if match is None:
            return
        
        name = self.stripColors(match.group('name'))
        cid = int(match.group('cid'))
        client = self.getByCidOrJoinPlayer(match.group('cid'))

        if not client or client.name != name:
            self.debug('UrT bug spotted. Trying to get client by name')
            client = self.clients.getByName(name)

        if not client:
            self.verbose('No Client Found!')
            return None
                
        self.verbose('Client Found: %s on slot %s' % (client.name, client.cid))
        
        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, data, client, client.team)


    # saytell
    def OnSaytell(self, action, data, match=None):
        #5:39 saytell: 15 16 repelSteeltje: nno
        #5:39 saytell: 15 15 repelSteeltje: nno

        #data = match.group('text')
        #if not len(data) >= 2 and not (data[:1] == '!' or data[:1] == '@') and match.group('cid') == match.group('acid'):
        #    return None

        if match is None:
            return
        
        name = self.stripColors(match.group('name'))
        cid = int(match.group('cid'))
        client = self.getByCidOrJoinPlayer(match.group('cid'))
        tclient = self.clients.getByCID(match.group('acid'))

        if not client or client.name != name:
            self.debug('UrT bug spotted. Trying to get client by name')
            client = self.clients.getByName(name)

        if not client:
            self.verbose('No Client Found!')
            return None
                
        self.verbose('Client Found: %s on slot %s' % (client.name, client.cid))

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        return b3.events.Event(b3.events.EVT_CLIENT_PRIVATE_SAY, data, client, tclient)



    # tell
    def OnTell(self, action, data, match=None):
        #5:27 tell: woekele to XLR8or: test
        #We'll use saytell instead
        return None
        """-------------------------------------------------------------------------------
        client = self.clients.getByExactName(match.group('name'))
        tclient = self.clients.getByExactName(match.group('aname'))

        if not client:
            self.verbose('No Client Found')
            return None

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_PRIVATE_SAY, data, client, tclient)
        -------------------------------------------------------------------------------"""

    # endmap/shutdown
    def OnShutdowngame(self, action, data=None, match=None):
        self.debug('EVENT: OnShutdowngame')
        self.game.mapEnd()
        # self.clients.sync()
        # self.debug('Synchronizing client info')
        self._maplist = None # when UrT server reloads, newly uploaded maps get available: force refresh
        return b3.events.Event(b3.events.EVT_GAME_EXIT, data)

    # Startgame
    def OnInitgame(self, action, data, match=None):
        self.debug('EVENT: OnInitgame')
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', data)

        # capturelimit / fraglimit / timelimit
        for o in options:
            if o[0] == 'mapname':
                self.game.mapName = o[1]
            elif o[0] == 'g_gametype':
                self.game.gameType = self.defineGameType(o[1])
            elif o[0] == 'fs_game':
                self.game.modName = o[1]
            elif o[0] == 'capturelimit':
                self.game.captureLimit = o[1]
            elif o[0] == 'fraglimit':
                self.game.fragLimit = o[1]
            elif o[0] == 'timelimit':
                self.game.timeLimit = o[1]
            else:
                setattr(self.game, o[0], o[1])

        self.verbose('...self.console.game.gameType: %s' % self.game.gameType)
        self.game.startMap()
        self.game.rounds = 0
        thread.start_new_thread(self.clients.sync, ())
        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)


    # Warmup
    def OnWarmup(self, action, data=None, match=None):
        self.debug('EVENT: OnWarmup')
        self.game.rounds = 0
        return b3.events.Event(b3.events.EVT_GAME_WARMUP, data)

    # Start Round
    def OnInitround(self, action, data, match=None):
        self.debug('EVENT: OnInitround')
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', data)

        # capturelimit / fraglimit / timelimit
        for o in options:
            if o[0] == 'mapname':
                self.game.mapName = o[1]
            elif o[0] == 'g_gametype':
                self.game.gameType = self.defineGameType(o[1])
            elif o[0] == 'fs_game':
                self.game.modName = o[1]
            elif o[0] == 'capturelimit':
                self.game.captureLimit = o[1]
            elif o[0] == 'fraglimit':
                self.game.fragLimit = o[1]
            elif o[0] == 'timelimit':
                self.game.timeLimit = o[1]
            else:
                setattr(self.game, o[0], o[1])

        self.verbose('...self.console.game.gameType: %s' % self.game.gameType)
        self.game.startRound()

        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)


    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, b3.clients.Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('ban', cid=client, reason=reason))
            return
        elif not client.id:
            # no client id, database must be down, do tempban
            self.error('Q3AParser.ban(): no client id, database must be down, doing tempban')
            return self.tempban(client, reason, '1d', admin, silent)

        if admin:
            fullreason = self.getMessage('banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('banned', self.getMessageVariables(client=client, reason=reason))

        if client.cid is None:
            # ban by ip, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s',self.getCommand('banByIp', ip=client.ip, reason=reason))
            self.write(self.getCommand('banByIp', ip=client.ip, reason=reason))
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s',self.getCommand('ban', cid=client.cid, reason=reason))
            self.write(self.getCommand('ban', cid=client.cid, reason=reason))

        if not silent and fullreason != '':
            self.say(fullreason)

        if admin:
            admin.message('^3banned^7: ^1%s^7 (^2@%s^7). His last ip (^1%s^7) has been added to banlist'%(client.exactName, client.id, client.ip))

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, {'reason': reason, 'admin': admin}, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        self.debug('EFFECTIVE UNBAN : %s',self.getCommand('unbanByIp', ip=client.ip, reason=reason))
        self.write(self.getCommand('unbanByIp', ip=client.ip, reason=reason))
        if admin:
            admin.message('^3Unbanned^7: ^1%s^7 (^2@%s^7). His last ip (^1%s^7) has been removed from banlist. Trying to remove duplicates...' % (client.exactName, client.id, client.ip))
        t1 = threading.Timer(1, self._unbanmultiple, (client, admin))
        t1.start()

    def _unbanmultiple(self, client, admin=None):
        # UrT adds multiple instances to banlist.txt Make sure we remove up to 4 remaining duplicates in a separate thread
        c = 0
        while c < 4:
            self.write(self.getCommand('unbanByIp', ip=client.ip))
            time.sleep(2)
            c+=1
        if admin:
            admin.message('^3Unbanned^7: ^1%s^7. Up to 4 possible duplicate entries removed from banlist' % client.exactName )

    def getPlayerPings(self):
        data = self.write('status')
        if not data:
            return {}

        players = {}
        for line in data.split('\n'):
            m = re.match(self._regPlayer, line.strip())
            if m:
                if m.group('ping') == 'ZMBI':
                    # ignore them, let them not bother us with errors
                    pass
                else:
                    try:
                        players[str(m.group('slot'))] = int(m.group('ping'))
                    except:
                        players[str(m.group('slot'))] = 999
        return players

    def sync(self):
        self.debug('Synchronizing client info')
        plist = self.getPlayerList(maxRetries=4)
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.getByCidOrJoinPlayer(cid)
            if client:
                # Disconnect the zombies first
                if c['ping'] == 'ZMBI':
                    self.debug('slot is in state zombie: %s - ignoring', c['ip'])
                    # client.disconnect()
                elif client.guid and c.has_key('guid'):
                    if client.guid == c['guid']:
                        # player matches
                        self.debug('in-sync %s == %s', client.guid, c['guid'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.guid, c['guid'])
                        client.disconnect()
                elif client.ip and c.has_key('ip'):
                    if client.ip == c['ip']:
                        # player matches
                        self.debug('in-sync %s == %s', client.ip, c['ip'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.ip, c['ip'])
                        client.disconnect()
                else:
                    self.debug('no-sync: no guid or ip found.')

        return mlist

    def getMaps(self):
        if self._maplist is not None:
            return self._maplist

        data = self.write('fdir *.bsp')
        if not data:
            return []

        mapregex = re.compile(r'^maps/(?P<map>.+)\.bsp$', re.I)
        maps = []
        for line in data.split('\n'):
            m = re.match(mapregex, line.strip())
            if m:
                if m.group('map'):
                    maps.append(m.group('map'))

        return maps

    def getNextMap(self):
        # let's first check if a vote passed for the next map
        nmap = self.getCvar('g_nextmap').getString()
        self.debug('g_nextmap: %s' % nmap)
        if nmap != "":
            if nmap[:4] == 'ut4_': nmap = nmap[4:]
            elif nmap[:3] == 'ut_': nmap = nmap[3:]
            return nmap.title()

        # seek the next map from the mapcyle file
        if not self.game.mapName: return None

        mapcycle = self.getCvar('g_mapcycle').getString()
        if self.game.fs_game is None:
            try:
                self.game.fs_game = self.getCvar('fs_game').getString().rstrip('/')
            except:
                self.game.fs_game = None
                self.warning("Could not query server for fs_game")
        if self.game.fs_basepath is None:
            try:
                self.game.fs_basepath = self.getCvar('fs_basepath').getString().rstrip('/')
            except:
                self.game.fs_basepath = None
                self.warning("Could not query server for fs_basepath")
        mapfile = self.game.fs_basepath + '/' + self.game.fs_game + '/' + mapcycle
        if not os.path.isfile(mapfile):
            self.debug('coud not read mapcycle file at %s' % mapfile)
            if self.game.fs_homepath is None:
                try:
                    self.game.fs_homepath = self.getCvar('fs_homepath').getString().rstrip('/')
                except:
                    self.game.fs_homepath = None
                    self.warning("Could not query server for fs_homepath")
            mapfile = self.game.fs_homepath + '/' + self.game.fs_game + '/' + mapcycle
        if not os.path.isfile(mapfile):
            self.debug('coud not read mapcycle file at %s' % mapfile)
            self.error("Unable to find mapcycle file %s" % mapcycle)
            return None

        cyclemapfile = open(mapfile, 'r')
        lines = cyclemapfile.readlines()
        #self.debug(lines)
        if len(lines) == 0:
            return None

        # get maps
        maps = []
        try:
            while True:
                tmp = lines.pop(0).strip()
                if tmp[0] == '{':
                    while tmp[0] != '}':
                        tmp = lines.pop(0).strip()
                    tmp = lines.pop(0).strip()
                maps.append(tmp)
        except IndexError:
            pass

        #self.debug(maps)

        if len(maps) == 0:
            return None

        firstmap = maps[0]

        # find current map
        #currentmap = self.game.mapName.strip().lower() # this fails after a cyclemap
        currentmap = self.getCvar('mapname').value
        try:
            tmp = maps.pop(0)
            while currentmap != tmp:
                tmp = maps.pop(0)
            if currentmap == tmp:
                #self.debug('found current map %s' % currentmap)
                #self.debug(maps)
                if len(maps) > 0:
                    return maps.pop(0)
                else:
                    return firstmap
        except IndexError:
            return firstmap


    def getTeamScores(self):
        data = self.write('players')
        if not data:
            return None

        line = data.split('\n')[2]

        m = re.match(self._reTeamScores, line.strip())
        if m:
            return [int(m.group('RedScore')), int(m.group('BlueScore'))]

        return None

    def getScores(self):
        """
        NOTE: this won't work properly if the server has private slots. see http://forums.urbanterror.net/index.php/topic,9356.0.html
        """
        data = self.write('players')
        if not data:
            return None


        scores = {'red':None, 'blue':None, 'players':{}}

        line = data.split('\n')[2]
        m = re.match(self._reTeamScores, line.strip())
        if m:
            scores['red'] = int(m.group('RedScore'))
            scores['blue'] = int(m.group('BlueScore'))

        for line in data.split('\n')[3:]:
            m = re.match(self._rePlayerScore, line.strip())
            if m:
                scores['players'][int(m.group('slot'))] = {'kills':int(m.group('kill')), 'deaths':int(m.group('death'))}

        return scores


    def queryClientUserInfoByCid(self, cid):
        """
        : dumpuser 5
        Player 5 is not on the server
        
        : dumpuser 3
        userinfo
        --------
        ip                  62.235.246.103:27960
        name                Shinki
        racered             2
        raceblue            2
        rate                8000
        ut_timenudge        0
        cg_rgb              255 0 255
        cg_predictitems     0
        cg_physics          1
        gear                GLJAXUA
        cl_anonymous        0
        sex                 male
        handicap            100
        color2              5
        color1              4
        team_headmodel      *james
        team_model          james
        headmodel           sarge
        model               sarge
        snaps               20
        teamtask            0
        cl_guid             8982B13A8DCEE4C77A32E6AC4DD7EEDF
        weapmodes           00000110220000020002

        """
        data = self.write('dumpuser %s' % cid)
        if not data:
            return None
        
        if data.split('\n')[0] != "userinfo":
            self.debug("dumpuser %s returned : %s" % (cid, data))
            self.debug('client %s probably disconnected, but its character is still hanging in game...')
            return None

        datatransformed = "%s " % cid
        for line in data.split('\n'):
            if line.strip() == "userinfo" or line.strip() == "--------":
                continue

            var = line[:20].strip()
            val = line[20:].strip()
            datatransformed += "\\%s\\%s" % (var, val)

        return datatransformed

    def getByCidOrJoinPlayer(self, cid):
        client = self.clients.getByCID(cid)
        if client:
            return client
        else:
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfo(None, userinfostring)
            return self.clients.getByCID(cid)

    def getPlayerTeams(self):
        """return a dict having cid as keys and a B3 team as value for
        as many slots as we can get a team for.
        
        /rcon players
        Map: ut4_heroic_beta1
        Players: 16
        Scores: R:51 B:92
        0:  FREE k:0 d:0 ping:0
        0:  FREE k:0 d:0 ping:0
        2: Anibal BLUE k:24 d:11 ping:69 90.47.240.44:27960
        3: kasper01 RED k:6 d:28 ping:56 93.22.173.133:27960
        4: notorcan RED k:16 d:10 ping:51 86.206.51.250:27960
        5: laCourge SPECTATOR k:0 d:0 ping:48 81.56.143.41:27960
        6: fundy_kill BLUE k:6 d:9 ping:50 92.129.99.62:27960
        7: brillko BLUE k:25 d:11 ping:56 85.224.201.172:27960
        8: -Tuxmania- BLUE k:16 d:7 ping:48 81.231.39.32:27960
        9: j.i.goe RED k:1 d:4 ping:51 86.218.69.81:27960
        10: EasyRider RED k:10 d:12 ping:53 85.176.137.142:27960
        11: Ferd75 BLUE k:4 d:8 ping:48 90.3.171.84:27960
        12: frag4#Gost0r RED k:11 d:16 ping:74 79.229.27.54:27960
        13: {'OuT'}ToinetoX RED k:6 d:13 ping:67 81.48.189.135:27960
        14: GibsonSG BLUE k:-1 d:2 ping:37 84.60.3.67:27960
        15: Kjeldor BLUE k:16 d:9 ping:80 85.246.3.196:50851

        NOTE: this won't work fully if the server has private slots. see http://forums.urbanterror.net/index.php/topic,9356.0.html
        """
        player_teams = {}
        letters2slots = {'A': '0', 'C': '2', 'B': '1', 'E': '4', 'D': '3', 'G': '6', 'F': '5', 'I': '8', 'H': '7', 'K': '10', 'J': '9', 'M': '12', 'L': '11', 'O': '14', 'N': '13', 'Q': '16', 'P': '15', 'S': '18', 'R': '17', 'U': '20', 'T': '19', 'W': '22', 'V': '21', 'Y': '24', 'X': '23', 'Z': '25'}
        
        players_data = self.write('players')
        for line in players_data.split('\n')[3:]:
            self.debug(line.strip())
            m = re.match(self._rePlayerScore, line.strip())
            if m and line.strip() != '0:  FREE k:0 d:0 ping:0':
                cid = m.group('slot')
                team = self.getTeam(m.group('team'))
                player_teams[cid] = team

        g_blueteamlist = self.getCvar('g_blueteamlist')
        if g_blueteamlist:
            for letter in g_blueteamlist.getString():
                player_teams[letters2slots[letter]] = b3.TEAM_BLUE

        g_redteamlist = self.getCvar('g_redteamlist')
        if g_redteamlist:
            for letter in g_redteamlist.getString():
                player_teams[letters2slots[letter]] = b3.TEAM_RED
        return player_teams

    def _getDamagePoints(self, weapon, hitloc):
        try:
            points = self.damage[weapon][int(hitloc)]
            self.debug("_getDamagePoints(%s, %s) -> %s" % (weapon, hitloc, points))
            return points
        except KeyError, err:
            self.warning("_getDamagePoints(%s, %s) cannot find value : %s" % (weapon, hitloc, err))
            return 15
        
    def _convertHitWeaponToKillWeapon(self, hitweapon_id):
        """on Hit: lines identifiers for weapons are different than
        the one on Kill: lines"""
        try:
            return self.hitweapon2killweapon[int(hitweapon_id)]
        except KeyError, err:
            self.warning("unknown weapon id on Hit line: %s", err)
            return None


"""
#----- Actions -----------------------------------------------------------------
Item: 0 team_CTF_redflag -> Flag Taken/picked up
Flag: 0 0: team_CTF_blueflag -> Flag Dropped
Flag: 0 1: team_CTF_blueflag -> Flag Returned
Flag: 0 2: team_CTF_blueflag -> Flag Captured

Bombholder is 5 -> Spawn with the bomb
Bomb was planted by 5
Bomb was defused by 6!
Bomb was tossed by 4 -> either manually or by being killed
Bomb has been collected by 6 -> Picking up a tossed bomb

#----- Connection Info ---------------------------------------------------------
A little documentation on the ClientSlot states in relation to ping positions in the status response

UrT ClientSlot states:
CS_FREE,     // can be reused for a new connection
CS_ZOMBIE,   // client has been disconnected, but don't reuse
             // connection for a couple seconds
CS_CONNECTED // has been assigned to a client_t, but no gamestate yet
CS_PRIMED,   // gamestate has been sent, but client hasn't sent a usercmd
CS_ACTIVE    // client is fully in game

Snippet 1:
if (cl->state == CS_CONNECTED)
            Com_Printf ("CNCT ");
        else if (cl->state == CS_ZOMBIE)
            Com_Printf ("ZMBI ");
        else
        {
            ping = cl->ping < 9999 ? cl->ping : 9999;
            Com_Printf ("%4i ", ping);
        }

Snippet 2:
if (cl->state == CS_ZOMBIE && cl->lastPacketTime < zombiepoint) {
  // using the client id cause the cl->name is empty at this point
  Com_DPrintf( "Going from CS_ZOMBIE to CS_FREE for client %d\n", i );
  cl->state = CS_FREE; // can now be reused
}

#----- Available variables defined on Init -------------------------------------
081027 14:53:22 DEBUG   EVENT: OnInitgame
081027 14:53:22 VERBOSE ...self.console.game.sv_allowdownload: 0
081027 14:53:22 VERBOSE ...self.console.game.g_matchmode: 0
081027 14:53:22 VERBOSE ...self.console.game.sv_maxclients: 16
081027 14:53:22 VERBOSE ...self.console.game.sv_floodprotect: 1
081027 14:53:22 VERBOSE ...self.console.game.g_warmup: 15
081027 14:53:22 VERBOSE ...self.console.game.captureLimit: 0
081027 14:53:22 VERBOSE ...self.console.game.sv_hostname:   ^1[SNT]^7 TDM #4 Dungeon (B3)
081027 14:53:22 VERBOSE ...self.console.game.g_followstrict: 1
081027 14:53:22 VERBOSE ...self.console.game.fragLimit: 0
081027 14:53:22 VERBOSE ...self.console.game.timeLimit: 15
081027 14:53:22 VERBOSE ...self.console.game.g_cahtime: 60
081027 14:53:22 VERBOSE ...self.console.game.g_swaproles: 0
081027 14:53:22 VERBOSE ...self.console.game.g_roundtime: 3
081027 14:53:22 VERBOSE ...self.console.game.g_bombexplodetime: 40
081027 14:53:22 VERBOSE ...self.console.game.g_bombdefusetime: 10
081027 14:53:22 VERBOSE ...self.console.game.g_hotpotato: 2
081027 14:53:22 VERBOSE ...self.console.game.g_waverespawns: 0
081027 14:53:22 VERBOSE ...self.console.game.g_redwave: 15
081027 14:53:22 VERBOSE ...self.console.game.g_bluewave: 15
081027 14:53:22 VERBOSE ...self.console.game.g_respawndelay: 3
081027 14:53:22 VERBOSE ...self.console.game.g_suddendeath: 1
081027 14:53:22 VERBOSE ...self.console.game.g_maxrounds: 0
081027 14:53:22 VERBOSE ...self.console.game.g_friendlyfire: 1
081027 14:53:22 VERBOSE ...self.console.game.g_allowvote: 536870920
081027 14:53:22 VERBOSE ...self.console.game.g_armbands: 0
081027 14:53:22 VERBOSE ...self.console.game.g_survivorrule: 0
081027 14:53:22 VERBOSE ...self.console.game.g_gear: 0
081027 14:53:22 VERBOSE ...self.console.game.g_deadchat: 1
081027 14:53:22 VERBOSE ...self.console.game.g_maxGameClients: 0
081027 14:53:22 VERBOSE ...self.console.game.sv_dlURL: sweetopia.snt.utwente.nl/xlr
081027 14:53:22 VERBOSE ...self.console.game.sv_maxPing: 250
081027 14:53:22 VERBOSE ...self.console.game.sv_minPing: 0
081027 14:53:22 VERBOSE ...self.console.game.sv_maxRate: 0
081027 14:53:22 VERBOSE ...self.console.game.sv_minRate: 0
081027 14:53:22 VERBOSE ...self.console.game.dmflags: 0
081027 14:53:22 VERBOSE ...self.console.game.version: ioq3 1.35urt linux-i386 Dec 20 2007
081027 14:53:22 VERBOSE ...self.console.game.protocol: 68
081027 14:53:22 VERBOSE ...self.console.game.mapName: ut4_turnpike
081027 14:53:22 VERBOSE ...self.console.game.sv_privateClients: 4
081027 14:53:22 VERBOSE ...self.console.game. Admin:  XLR8or
081027 14:53:22 VERBOSE ...self.console.game. Email: admin@xlr8or.com
081027 14:53:22 VERBOSE ...self.console.game.gamename: q3ut4
081027 14:53:22 VERBOSE ...self.console.game.g_needpass: 1
081027 14:53:22 VERBOSE ...self.console.game.g_enableDust: 0
081027 14:53:22 VERBOSE ...self.console.game.g_enableBreath: 0
081027 14:53:22 VERBOSE ...self.console.game.g_antilagvis: 0
081027 14:53:22 VERBOSE ...self.console.game.g_survivor: 0
081027 14:53:22 VERBOSE ...self.console.game.g_enablePrecip: 2
081027 14:53:22 VERBOSE ...self.console.game.g_modversion: 4.1
081027 14:53:22 VERBOSE ...self.console.game.gameType: tdm

"""
