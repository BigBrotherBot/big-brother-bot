#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2008 Mark Weirath (xlr8or@xlr8or.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
#
#              1.0.3  - Courgette      - added support for banlist.txt
#                       xlr8or         - added parsing Damage (on_hit)
#              1.0.4  - xlr8or         - added EVT_CLIENT_TEAM_CHANGE in on_kill
#              1.0.5  - xlr8or         - added hitloc and damageType info to accomodate XLRstats
#              1.0.6  - xlr8or         - fixed a bug where the parser wouldn't parse the shutdowngame and warmup functions
#              1.0.7  - xlr8or         - better synchronizing and identification of connecting players and zombies
#              1.0.8  - xlr8or         - better Zombie handling (Zombies being a result of: sv_zombietime (default 2
#                                        seconds)). (Zombie time is the time after a disconnect that the slot cannot be
#                                        used and thus is in Zombie state)
#                                      - dded functionality to use ip's only, not using the guid at all (experimental)
#              1.0.9  - xlr8or         - try to get the map name at start
#                                      - provide get_player_scores method
#              1.0.10 - Courgette      - modified _recolor so name sanitation is the same as UrT
#                                        here it does more than just remove color
#              1.0.11 - Courgette      - Add get_scores  # NOTE: this won't work properly if the server has private slots.
#              1.0.12 - Courgette      - Fix regex that failed to parse chat lines when player's name ends with ':'
#              1.0.13 - xlr8or         - support for !maps and !nextmap command
#              1.0.14 - xlr8or         - better understanding of mapcycle.txt
#              1.0.15 - mindriot       - client with empty name ("") resulted in error and B3 not registering
#                                        client - now given _empty_name_default
#              1.0.16 - xlr8or         - added ipcombi. Setting True will replace the last part of the guid with two
#                                        segments of the ip: increases security on admins who have cl_guidServerUniq set
#                                        to 0 in client config (No cloning).
#              1.0.17 - mindriot       - empty_name_default now only given upon client connect, due to possibility of no
#                                        name specified in ClientUserinfo at any time
#              1.0.19 - xlr8or         - disabled PunkBuster default settings due to recent supportrequests in the forums
#                                        with missing PB line in b3.xml
#              1.1.0  - xlr8or         - added action mechanism (event) for B3 v1.1.5+
#              1.1.1  - Courgette      - debugged Action Mechanism (event) for B3 v1.1.5+
# 19/08/2009 - 1.2.0  - Courgette      - adds slap, nuke, mute new custom penalty types (can be used in censor or
#                                        admin plugin)
#                                      - requires admin plugin v1.4+ and parser.py v1.10+
# 20/10/2009 - 1.3.0  - Courgette      - upon bot start, already connected players are correctly recognized
# 26/10/2009 - 1.4.0  - Courgette      - when no client is found by cid, try to join the player using /rcon dumpuser <cid>
# 11/11/2009 - 1.5.0  - Courgette      - create a new event: EVT_GAME_FLAG_RETURNED which is fired when the flag
#                                        return because of time code refactoring
# 17/11/2009 - 1.5.1  - Courgette      - harden get_nextmap by :
#                                        * wrapping initial getcvar queries with try:except bloc
#                                        * requerying required cvar if missing
#                                        * forcing map list refresh on server reload or round end
# 26/11/2009 - 1.5.2  - Courgette      - fix a bug that prevented kills by slap or nuke from firing kill events
# 30/11/2009 - 1.6.1  - Courgette      - separate parsing of lines ClientUserInfo and ClientUserInfoChanged to better
#                                        translate ClientUserInfoChanged data. Also OnClientUserInfoChanged does not create
#                                        new client if cid is unknown
# 05/12/2009 - 1.6.2  - Courgette      - fix _replayerscore regexp
#                                      - on startup, also try to get players' team (which is not given by dumpuser)
# 06/12/2009 - 1.6.3  - Courgette      - harden query_client_userinfo_by_cid making sure we got a positive response. (Never
#                                        trust input data...)
#                                      - fix _replayerscore regexp again
# 06/12/2009 - 1.6.4  - Courgette      - sync() will retries to get player list up to 4 for times before giving up as
#                                        sync() after map change too often fail 2 times.
# 09/12/2009 - 1.6.5  - Courgette      - different handling of 'name' in OnClientuserinfo. Now log looks less worrying
#                                      - prevent exception on the rare case where a say line shows no text after cid (hence
#                                        no regexp match)
# 21/12/2009 - 1.7    - Courgette      - add new UrT specific event : EVT_CLIENT_GEAR_CHANGE
# 30/12/2009 - 1.7.1  - Courgette      - Say, Sayteam and Saytell lines do not trigger name change anymore and detect
#                                        the UrT bug described in
#                                        http://www.bigbrotherbot.net/forums/urt/b3-bot-sometimes-mix-up-client-id%27s/ .
#                                        Hopefully this definitely fixes the wrong aliases issue
# 30/12/2009 - 1.7.2  - Courgette      - improve say lines slot bug detection for cases where no player exists on slot 0
#                                      - refactor detection code to follow the KISS rule (keep it simple and stupid)
# 31/12/2009 - 1.7.3  - Courgette      - fix bug getting client by name when UrT slot 0 bug
#                                      - requires clients.py 1.2.8+
# 02/01/2010 - 1.7.4  - Courgette      - improve Urt slot bug workaround as it appears it can occur with slot num
#                                        different than 0
# 05/01/2010 - 1.7.5  - Courgette      - fix minor bug in saytell
# 16/01/2010 - 1.7.6  - xlr8or         - removed max_retries=4 keyword from get_player_list()
# 16/01/2010 - 1.7.7  - Courgette      - put back max_retries=4 keyword from get_player_list(). @xlr8or: make sure you have
#                                        the latest q3a.py file (v1.3.1+) for max_retries to work.
# 18/01/2010 - 1.7.8  - Courgette      - update get_player_list and sync so that connecting players (CNCT) are not ignored.
#                                        This will allow to use commands like !ci or !kick on hanging players.
# 26/01/2010 - 1.7.9  - xlr8or         - moved get_map() to q3a.py
# 10/04/2010 - 1.7.10 - Bakes          - bigsay() function can be used by plugins.
# 15/04/2010 - 1.7.11 - Courgette      - add debugging info for get_nextmap()
# 28/05/2010 - 1.7.12 - xlr8or         - connect bots
# 07/11/2010 - 1.7.13 - GrosBedo       - messages now support named $variables instead of %s
# 08/11/2010 - 1.7.14 - GrosBedo       - messages can now be empty (no message broadcasted on kick/tempban/ban/unban)
# 21/12/2010 - 1.7.15 - SGT            - fix CNCT ping error in getPlayersPings
#                                      - fix incorrect game type for ffa
#                                      - move getMapList after game initialization
# 09/04/2011 - 1.7.16 - Courgette      - reflect that cid are not converted to int anymore in the clients module
# 03/05/2011 - 1.7.17 - Courgette      - reflect changes in inflict_custom_penalty method signature
# 31/05/2011 - 1.8.0  - Courgette      - damage event now carry correct damage points
#                                      - damage event weapon code is now the same as the one used for Kill events
# 01/06/2011 - 1.8.1  - Courgette      - fix Damage points
#                                      - when game log provides hit info, Kill event will use last dmg points instead of 100
# 04/06/2011 - 1.9.0  - Courgette      - makes use of the new plugins_started parser hook
# 05/06/2011 - 1.10.0 - Courgette      - change data format for EVT_CLIENT_BAN events
# 14/06/2011 - 1.11.0 - Courgette      - cvar code moved to q3a AbstractParser
# 12/09/2011 - 1.11.1 - Courgette      - EVT_CLIENT_JOIN event is now triggered when player actually join a team
#                                      - the call to self.clients.sync() that was made each round is now made on game
#                                        init and in its own thread
# 29/09/2011 - 1.11.2 - Courgette      - fix MOD_TELEFRAG attacker on kill event to prevent people from being considered
#                                        as tkers in such cases.
# 15/10/2011 - 1.11.3 - Courgette      - better team recognition of existing players at B3 start
# 15/11/2011 - 1.11.4 - Courgette      - players's team get refreshed after unpausing the bot (useful when used with FTP
#                                        and B3 lose the connection for a while)
# 03/03/2012 - 1.11.5 - SGT            - create Survivor Winner event
#                                      - create Unban event
#                                      - fix issue with on_say when something like this come and the match couldn't find
#                                        the name group, say: 7 -crespino-
# 08/04/2012 - 1.12   - Courgette      - fixes rotatemap() - thanks to Beber888
#                                      - refactor unban()
#                                      - change_map() can now provide suggestions
# 05/05/2012 - 1.13   - Courgette      - fixes issue xlr8or/big-brother-bot#87 - missing ip when trying to auth a
#                                        client crashes the bot
# 19/05/2012 - 1.13.1 - Courgette      - fixes issue with kill events when killed by UT_MOD_SLAPPED,
#                                        UT_MOD_NUKED, MOD_TELEFRAG
# 07/07/2012 - 1.13.2 - Courgette      - ensures the config file has option 'game_log' in section 'server'
# 12/08/2012 - 1.13.3 - Courgette      - fix !nextmap bug when the mapcycle file contains empty lines
# 19/10/2012 - 1.14   - Courgette      - improve finding the exact map in get_maps_sounding_like. Also improves change_map()
#                                        behavior as a consequence
# 26/11/2012 - 1.15   - Courgette      - protect some of the Client object property
# 08/04/2013 - 1.16   - Courgette      - add EVT_BOMB_EXPLODED event
# 14/07/2013 - 1.17   - Courgette      - add hitlocation constants : HL_HEAD, HL_HELMET and HL_TORSO
# 10/08/2013 - 1.18   - Fenix          - change get_nextmap to use CVARs only (no more mapcycle file parsing)
# 13/01/2014 - 1.19   - Fenix          - PEP8 coding standards
#                                          - correctly set the client bot flag upon new client connection
# 14/04/2014 - 1.20   - Fenix          - rewritten regular expressions on multiline: respect PEP8 constraint
#                                          - use get_event_id method to obtain event ids: remove some warnings
# 02/06/2014 - 1.20.1 - Fenix          - fixed reColor regex stripping whitespaces between words
# 18/07/2014 - 1.21   - Fenix          - updated parser to comply with the new get_wrap implementation
#                                      - general parser cleanup
#                                      - reformat changelog to it can actually be read :)
#                                      - removed _settings dict re-declaration: was the same of the AbstractParser
#                                      - updated rcon command patterns
# 03/08/2014 - 1.22   - Fenix          - syntax cleanup
# 13/09/2014 - 1.23   - Fenix          - added new event: EVT_SENTRY_KILL
# 02/10/2014 - 1.24   - Fenix          - fixed regression introduced in 1.22
# 15/01/2015 - 1.25   - Fenix          - fixed another regression introduced in 1.22
# 27/01/2015 - 1.26   - Thomas LEVEIL  - `fdir *.bsp` waits for a game server response for 15s
# 15/06/2015 - 1.27   - Fenix          - fixed client userinfo parsing!
# 26/07/2015 - 1.28   - Fenix          - queue EVT_GAME_ROUND_END when survivor winner is triggered

__author__ = 'xlr8or, Courgette, Fenix'
__version__ = '1.28'

import b3
import b3.events
import b3.clients
import b3.parser
import re
import string
import time
import thread

from b3.functions import getStuffSoundingLike
from b3.functions import prefixText
from b3.parsers.q3a.abstractParser import AbstractParser


class Iourt41Parser(AbstractParser):

    gameName = 'iourt41'

    IpsOnly = False
    IpCombi = False
    PunkBuster = None

    _logSync = 2
    _maplist = None
    _empty_name_default = 'EmptyNameDefault'

    _commands = {
        'ban': 'addip %(cid)s',
        'banByIp': 'addip %(ip)s',
        'broadcast': '%(message)s',
        'kick': 'clientkick %(cid)s',
        'message': 'tell %(cid)s %(message)s',
        'moveToTeam': 'forceteam %(cid)s %(team)s',
        'mute': 'mute %(cid)s %(seconds)s',
        'nuke': 'nuke %(cid)s',
        'say': 'say %(message)s',
        'saybig': 'bigtext "%(message)s"',
        'set': 'set %(name)s "%(value)s"',
        'slap': 'slap %(cid)s',
        'tempban': 'clientkick %(cid)s',
        'unbanByIp': 'removeip %(ip)s',
    }

    _eventMap = {
        #'warmup' : b3.events.EVT_GAME_WARMUP,
        #'shutdowngame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')

    _lineFormats = (
        # Generated with ioUrbanTerror v4.1:
        # Hit: 12 7 1 19: BSTHanzo[FR] hit ercan in the Helmet
        # Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<hitloc>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # 6:37 Kill: 0 1 16: XLR8or killed =lvl1=Cheetah by UT_MOD_SPAS
        # 2:56 Kill: 14 4 21: Qst killed Leftovercrack by UT_MOD_PSG1
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>('
                   r'?P<acid>[0-9]+)\s'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # Processing chats and tell events...
        # 5:39 saytell: 15 16 repelSteeltje: nno
        # 5:39 saytell: 15 15 repelSteeltje: nno
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<name>[^ ]+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # 3:53 say: 8 denzel: lol
        # 15:37 say: 9 .:MS-T:.BstPL: this name is quite a challenge
        # 2:28 sayteam: 12 New_UrT_Player_v4.1: woekele
        # 16:33 Flag: 2 0: team_CTF_redflag
        # SGT: fix issue with on_say when something like this come and the match could'nt find the name group
        # say: 7 -crespino-:
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<name>[^ ]+):\s*'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # 15:42 Flag Return: RED
        # 15:42 Flag Return: BLUE
        re.compile(r'^(?P<action>Flag Return):\s(?P<data>(?P<color>.+))$', re.IGNORECASE),

        # Bombmode actions:
        # 3:06 Bombholder is 2
        re.compile(r'^(?P<action>Bombholder)(?P<data>\sis\s(?P<cid>[0-9]))$', re.IGNORECASE),

        # was planted, was defused, was tossed, has been collected (doh, how gramatically correct!)
        # 2:13 Bomb was tossed by 2
        # 2:32 Bomb was planted by 2
        # 3:01 Bomb was defused by 3!
        # 2:17 Bomb has been collected by 2
        re.compile(r'^(?P<action>Bomb)\s'
                   r'(?P<data>(was|has been)\s'
                   r'(?P<subaction>[a-z]+)\sby\s'
                   r'(?P<cid>[0-9]+).*)$', re.IGNORECASE),

        #17:24 Pop!
        re.compile(r'^(?P<action>Pop)!$', re.IGNORECASE),

        # Falling thru Item stuff and so forth
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>.*)$', re.IGNORECASE),

        # Shutdowngame and Warmup... the one word lines
        re.compile(r'^(?P<action>[a-z]+):$', re.IGNORECASE)
    )

    # map: ut4_casa
    # num score ping name            lastmsg address               qport rate
    # --- ----- ---- --------------- ------- --------------------- ----- -----
    #   2     0   19 ^1XLR^78^8^9or        0 145.99.135.227:27960  41893  8000  # player with a live ping
    #   4     0 CNCT Dz!k^7              450 83.175.191.27:64459   50308 20000  # connecting player
    #   9     0 ZMBI ^7                 1900 81.178.80.68:27960    10801  8000  # zombies (need to be disconnected!)
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+'
                            r'(?P<score>[0-9-]+)\s+'
                            r'(?P<ping>[0-9]+|CNCT|ZMBI)\s+'
                            r'(?P<name>.*?)\s+'
                            r'(?P<last>[0-9]+)\s+'
                            r'(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+'
                            r'(?P<qport>[0-9]+)\s+'
                            r'(?P<rate>[0-9]+)$', re.IGNORECASE)

    _reColor = re.compile(r'(\^\d)')

    # Map: ut4_algiers
    # Players: 8
    # Scores: R:97 B:98
    # 0:  FREE k:0 d:0 ping:0
    # 4: yene RED k:16 d:8 ping:50 92.104.110.192:63496
    _reTeamScores = re.compile(r'^Scores:\s+'
                               r'R:(?P<RedScore>.+)\s+'
                               r'B:(?P<BlueScore>.+)$', re.IGNORECASE)

    _rePlayerScore = re.compile(r'^(?P<slot>[0-9]+): '
                                r'(?P<name>.*) '
                                r'(?P<team>RED|BLUE|SPECTATOR|FREE) '
                                r'k:(?P<kill>[0-9]+) d:(?P<death>[0-9]+) ping:(?P<ping>[0-9]+|CNCT|ZMBI)( '
                                r'(?P<ip>[0-9.]+):(?P<port>[0-9-]+))?$', re.IGNORECASE)

    ## kill modes
    MOD_WATER = '1'
    MOD_LAVA = '3'
    MOD_TELEFRAG = '5'
    MOD_FALLING = '6'
    MOD_SUICIDE = '7'
    MOD_TRIGGER_HURT = '9'
    MOD_CHANGE_TEAM = '10'
    UT_MOD_KNIFE = '12'
    UT_MOD_KNIFE_THROWN = '13'
    UT_MOD_BERETTA = '14'
    UT_MOD_DEAGLE = '15'
    UT_MOD_SPAS = '16'
    UT_MOD_UMP45 = '17'
    UT_MOD_MP5K = '18'
    UT_MOD_LR300 = '19'
    UT_MOD_G36 = '20'
    UT_MOD_PSG1 = '21'
    UT_MOD_HK69 = '22'
    UT_MOD_BLED = '23'
    UT_MOD_KICKED = '24'
    UT_MOD_HEGRENADE = '25'
    UT_MOD_SR8 = '28'
    UT_MOD_AK103 = '30'
    UT_MOD_SPLODED = '31'
    UT_MOD_SLAPPED = '32'
    UT_MOD_BOMBED = '33'
    UT_MOD_NUKED = '34'
    UT_MOD_NEGEV = '35'
    UT_MOD_HK69_HIT = '37'
    UT_MOD_M4 = '38'
    UT_MOD_FLAG = '39'
    UT_MOD_GOOMBA = '40'

    # HIT LOCATIONS
    HL_HEAD = '0'
    HL_HELMET = '1'
    HL_TORSO = '2'

    # WORLD CID (used for Mr. Sentry detection)
    WORLD = '1022'

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

    # From data provided by Garreth http://bit.ly/jf4QXc on http://bit.ly/krwBCv :
    #
    #                            Head(0) Helmet(1)     Torso(2)     Kevlar(3)     Arms(4)    Legs(5)    Body(6)   Killed
    # MOD_TELEFRAG='5'             0        0             0             0             0         0         0          0
    # UT_MOD_KNIFE='12'           100      60            44            35            20        20        44        100
    # UT_MOD_KNIFE_THROWN='13'    100      60            44            35            20        20        44        100
    # UT_MOD_BERETTA='14'         100      34            30            20            11        11        30        100
    # UT_MOD_DEAGLE='15'          100      66            57            38            22        22        57        100
    # UT_MOD_SPAS='16'            25       25            25            25            25        25        25        100
    # UT_MOD_UMP45='17'           100      51            44            29            17        17        44        100
    # UT_MOD_MP5K='18'            50       34            30            20            11        11        30        100
    # UT_MOD_LR300='19'           100      51            44            29            17        17        44        100
    # UT_MOD_G36='20'             100      51            44            29            17        17        44        100
    # UT_MOD_PSG1='21'            100      63            97            63            36        36        97        100
    # UT_MOD_HK69='22'            50       50            50            50            50        50        50        100
    # UT_MOD_BLED='23'            15       15            15            15            15        15        15        15
    # UT_MOD_KICKED='24'          20       20            20            20            20        20        20        100
    # UT_MOD_HEGRENADE='25'       50       50            50            50            50        50        50        100
    # UT_MOD_SR8='28'             100      100           100           100           50        50        100       100
    # UT_MOD_AK103='30'           100      58            51            34            19        19        51        100
    # UT_MOD_NEGEV='35'           50       34            30            20            11        11        30        100
    # UT_MOD_HK69_HIT='37'        20       20            20            20            20        20        20        100
    # UT_MOD_M4='38'              100      51            44            29            17        17        44        100
    # UT_MOD_GOOMBA='40'          100      100           100           100           100       100       100       100

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

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def startup(self):
        """
        Called after the parser is created before run().
        """
        if not self.config.has_option('server', 'game_log'):
            self.critical("Your main config file is missing the 'game_log' setting in section 'server'")
            raise SystemExit(220)

        # add UrT specific events
        self.Events.createEvent('EVT_GAME_FLAG_RETURNED', 'Flag returned')
        self.Events.createEvent('EVT_CLIENT_GEAR_CHANGE', 'Client gear change')
        self.Events.createEvent('EVT_SURVIVOR_WIN', 'Survivor Winner')
        self.Events.createEvent('EVT_BOMB_EXPLODED', 'Bomb exploded')
        self.Events.createEvent('EVT_SENTRY_KILL', 'Mr Sentry kill')

        # add event mappings
        self._eventMap['warmup'] = self.getEventID('EVT_GAME_WARMUP')
        self._eventMap['shutdowngame'] = self.getEventID('EVT_GAME_ROUND_END')

        # add the world client
        self.clients.newClient('-1', guid='WORLD', name='World', hide=True, pbid='WORLD')

        # get map from the status rcon command
        mapname = self.getMap()
        if mapname:
            self.game.mapName = mapname
            self.info('map is: %s' % self.game.mapName)

        # force g_logsync
        self.debug('Forcing server cvar g_logsync to %s' % self._logSync)
        self.setCvar('g_logsync', self._logSync)
        
        # get gamepaths/vars
        cvarlist = self.cvarList("fs_")

        self.game.fs_game = cvarlist.get('fs_game')
        if not self.game.fs_game:
            self.warning("Could not query server for fs_game")
        else:
            self.debug("fs_game: %s" % self.game.fs_game)

        self.game.fs_basepath = cvarlist.get('fs_basepath')
        if not self.game.fs_basepath:
            self.warning("Could not query server for fs_basepath")
        else:
            self.game.fs_basepath = self.game.fs_basepath.rstrip('/')
            self.debug('fs_basepath: %s' % self.game.fs_basepath)

        self.game.fs_homepath = cvarlist.get('fs_homepath')
        if not self.game.fs_homepath:
            self.warning("Could not query server for fs_homepath")
        else:
            self.game.fs_homepath = self.game.fs_homepath.rstrip('/')
            self.debug('fs_homepath: %s' % self.game.fs_homepath)

        self._maplist = self.getMaps()

    def pluginsStarted(self):
        """
        Called after the parser loaded and started all plugins.
        """
        plist = self.getPlayerList()
        for cid in plist.keys():
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfo(None, userinfostring)
        
        player_teams = dict()
        tries = 0
        while tries < 3:
            try:
                tries += 1
                player_teams = self.getPlayerTeams()
                break
            except Exception as err:
                if tries < 3:
                    self.warning(err)
                else:
                    self.error("Cannot fix players teams: %s" % err)
                    return

        for cid in plist.keys():
            client = self.clients.getByCID(cid)
            if client and client.cid in player_teams:
                newteam = player_teams[client.cid]
                if newteam != client.team:
                    self.debug('Fixing client team for %s : %s is now %s' % (client.name, client.team, newteam))
                    setattr(client, 'team', newteam)
            
    def unpause(self):
        """
        Unpause B3 log parsing.
        """
        self.pluginsStarted()  # so we get teams refreshed
        self.clients.sync()
        b3.parser.Parser.unpause(self)

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def getLineParts(self, line):
        """
        Parse a log line returning extracted tokens.
        :param line: The line to be parsed
        """
        line = re.sub(self._lineClear, '', line, 1)
        m = None
        for f in self._lineFormats:
            m = re.match(f, line)
            if m:
                break

        if m is not None:
            client = None
            target = None
            try:
                data = m.group('data').strip()
            except:
                data = None
            return m, m.group('action').lower(), data, client, target
        elif '------' not in line:
            self.verbose('Line did not match format: %s' % line)

    def parseUserInfo(self, info):
        """
        Parse an infostring.
        :param info: The infostring to be parsed.
        """
        # 2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or...
        # 7 n\[SNT]^1XLR^78or\t\3\r\2\tl\0\f0\\f1\\f2\\a0\0\a1\0\a2\0
        player_id, info = string.split(info, ' ', 1)

        if info[:1] != '\\':
            info = '\\' + info

        self.verbose2('Parsing userinfo: %s', info)
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', info)

        data = dict()
        for o in options:
            data[o[0]] = o[1]

        data['cid'] = player_id
        return data

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def OnClientconnect(self, action, data, match=None):
        self.debug('Client connected: ready to parse userinfo line')
        #client = self.clients.getByCID(data)
        #return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)

    def OnClientbegin(self, action, data, match=None):
        # we get user info in two parts:
        # 19:42.36 ClientBegin: 4
        client = self.getByCidOrJoinPlayer(data)
        if client:
            return b3.events.Event(self.getEventID('EVT_CLIENT_JOIN'), data=data, client=client)

    def OnClientuserinfo(self, action, data, match=None):
        # 2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or...
        # connecting bot:
        # 0 \gear\GMIORAA\team\blue\skill\5.000000\characterfile\bots/ut_chicken_c.c\color\4\sex\male\race\2\snaps\20\..
        bclient = self.parseUserInfo(data)

        bot = False
        if 'cl_guid' not in bclient and 'skill' in bclient:
            # must be a bot connecting
            self.bot('Bot connecting!')
            bclient['ip'] = '0.0.0.0'
            bclient['cl_guid'] = 'BOT' + str(bclient['cid'])
            bot = True

        if 'name' in bclient:
            # remove spaces from name
            bclient['name'] = bclient['name'].replace(' ', '')

        # split port from ip field
        if 'ip' in bclient:
            ip_port_data = string.split(bclient['ip'], ':', 1)
            bclient['ip'] = ip_port_data[0]
            if len(ip_port_data) > 1:
                bclient['port'] = ip_port_data[1]

        if 'team' in bclient:
            bclient['team'] = self.getTeam(bclient['team'])

        if 'cl_guid' in bclient and not 'pbid' in bclient and self.PunkBuster:
            bclient['pbid'] = bclient['cl_guid']

        self.verbose('Parsed userinfo: %s' % bclient)

        if bclient:
            client = self.clients.getByCID(bclient['cid'])
            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    if hasattr(client, 'gear') and k == 'gear' and client.gear != v:
                        self.queueEvent(b3.events.Event(self.getEventID('EVT_CLIENT_GEAR_CHANGE'), v, client))
                    if not k.startswith('_') and k not in ('login', 'password', 'groupBits', 'maskLevel',
                                                           'autoLogin', 'greeting'):
                        setattr(client, k, v)
            else:
                # make a new client
                if self.PunkBuster:
                    # we will use punkbuster's guid
                    guid = None
                else:
                    # use io guid
                    if 'cl_guid' in bclient:
                        guid = bclient['cl_guid']
                    else:
                        guid = 'unknown'

                # v1.0.17 - mindriot - 02-Nov-2008
                if not 'name' in bclient:
                    bclient['name'] = self._empty_name_default

                if not 'ip' in bclient:
                    if guid == 'unknown':
                        # happens when a client is (temp)banned and got kicked so client
                        # was destroyed, but infoline was still waiting to be parsed.
                        self.debug('Client disconnected: ignoring...')
                        return None
                    else:
                        try:
                            # see issue xlr8or/big-brother-bot#87 - ip can be missing
                            self.debug("Missing IP, trying to get ip with 'status'")
                            plist = self.getPlayerList()
                            client_data = plist[bclient['cid']]
                            bclient['ip'] = client_data['ip']
                        except Exception, err:
                            bclient['ip'] = ''
                            self.warning("Failed to get client %s ip address" % bclient['cid'], err)

                nguid = ''
                # override the guid... use ip's only if self.console.IpsOnly is set True.
                if self.IpsOnly:
                    nguid = bclient['ip']

                # replace last part of the guid with two segments of the ip
                elif self.IpCombi:
                    i = bclient['ip'].split('.')
                    d = len(i[0]) + len(i[1])
                    nguid = guid[:-d] + i[0] + i[1]

                # Quake clients don't have a cl_guid, we'll use ip instead
                elif guid == 'unknown':
                    nguid = bclient['ip']

                if nguid != '':
                    guid = nguid

                self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'],
                                       state=b3.STATE_ALIVE, guid=guid, bot=bot, data={'guid': guid})

        return None

    def OnClientuserinfochanged(self, action, data, match=None):
        # 7 n\[SNT]^1XLR^78or\t\3\r\2\tl\0\f0\\f1\\f2\\a0\0\a1\0\a2\0
        parseddata = self.parseUserInfo(data)
        if parseddata:
            self.verbose('Parsed userinfo: %s' % parseddata)
            client = self.clients.getByCID(parseddata['cid'])
            if client:
                # update existing client
                if 'n' in parseddata:
                    setattr(client, 'name', parseddata['n'])

                if 't' in parseddata:
                    team = self.getTeam(parseddata['t'])
                    setattr(client, 'team', team)

                    if 'r' in parseddata:
                        if team == b3.TEAM_BLUE:
                            setattr(client, 'raceblue', parseddata['r'])
                        elif team == b3.TEAM_RED:
                            setattr(client, 'racered', parseddata['r'])

                    if parseddata.get('f0') is not None \
                        and parseddata.get('f1') is not None \
                        and parseddata.get('f2') is not None:

                        data = "%s,%s,%s" % (parseddata['f0'], parseddata['f1'], parseddata['f2'])
                        if team == b3.TEAM_BLUE:
                            setattr(client, 'funblue', data)
                        elif team == b3.TEAM_RED:
                            setattr(client, 'funred', data)

                if 'a0' in parseddata and 'a1' in parseddata and 'a2' in parseddata:
                    setattr(client, 'cg_rgb', "%s %s %s" % (parseddata['a0'], parseddata['a1'], parseddata['a2']))

    def OnHit(self, action, data, match=None):
        # Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
        # Hit: cid acid hitloc aweap: text
        victim = self.clients.getByCID(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.on_clientuserinfo(action, data, match)
            return None

        attacker = self.clients.getByCID(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        event = self.getEventID('EVT_CLIENT_DAMAGE')
        if attacker.cid == victim.cid:
            event = self.getEventID('EVT_CLIENT_DAMAGE_SELF')
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = self.getEventID('EVT_CLIENT_DAMAGE_TEAM')

        hitloc = match.group('hitloc')
        weapon = self._convertHitWeaponToKillWeapon(match.group('aweap'))
        points = self._getDamagePoints(weapon, hitloc)
        event_data = (points, weapon, hitloc)
        victim.data['lastDamageTaken'] = event_data
        #victim.state = b3.STATE_ALIVE
        # need to pass some amount of damage for the teamkill plugin - 15 seems okay
        return self.getEvent(event, event_data, attacker, victim)

    def OnKill(self, action, data, match=None):
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
        self.debug('OnKill: %s (%s)' % (match.group('aweap'), match.group('text')))
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
            attacker = self.clients.getByCID('-1')  # make the attacker 'World'
        elif match.group('aweap') in (self.MOD_WATER, self.MOD_LAVA, self.MOD_FALLING,
                                      self.MOD_TRIGGER_HURT, self.UT_MOD_BOMBED, self.UT_MOD_FLAG):
            # those kills should be considered suicides
            self.debug('OnKill: water/lava/falling/trigger_hurt/bombed/flag should be suicides')
            attacker = victim
        else:
            attacker = self.getByCidOrJoinPlayer(match.group('acid'))
        ## End fix attacker

        if not attacker:
            # handle the case where Mr.Sentry killed a player
            if match.group('aweap') == self.UT_MOD_BERETTA and match.group('acid') == self.WORLD:
                return self.getEvent('EVT_SENTRY_KILL', target=victim)
            else:
                self.debug('No attacker')
                return None

        damagetype = match.group('text').split()[-1:][0]
        if not damagetype:
            self.debug('No damage type, weapon: %s' % weapon)
            return None

        event = self.getEventID('EVT_CLIENT_KILL')

        # fix event for team change and suicides and tk
        if attacker.cid == victim.cid:
            if weapon == self.MOD_CHANGE_TEAM:
                # do not pass a teamchange event here
                # that event is passed shortly after the kill
                self.verbose('Team change event caught: exiting...')
                return None
            else:
                event = self.getEventID('EVT_CLIENT_SUICIDE')
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = self.getEventID('EVT_CLIENT_KILL_TEAM')

        # if not logging damage we need a general hitloc (for xlrstats)
        if 'lastDamageTaken' in victim.data:
            last_damage_data = victim.data['lastDamageTaken']
            del victim.data['lastDamageTaken']
        else:
            last_damage_data = (100, weapon, 'body')

        victim.state = b3.STATE_DEAD
        # self.verbose('OnKill Victim: %s, Attacker: %s, Weapon: %s, Hitloc: %s, dType: %s' %
        #              (victim.name, attacker.name, weapon, victim.hitloc, dType))
        # need to pass some amount of damage for the teamkill plugin - 100 is a kill
        return self.getEvent(event, (last_damage_data[0], weapon, last_damage_data[2], damagetype), attacker, victim)

    def OnClientdisconnect(self, action, data, match=None):
        client = self.clients.getByCID(data)
        if client:
            client.disconnect()
        return None

    def OnFlag(self, action, data, match=None):
        # Flag: 1 2: team_CTF_blueflag
        # Flag: <_cid> <_subtype:0/1/2>: <text>
        cid = match.group('cid')
        subtype = int(match.group('name'))
        data = match.group('text')

        if subtype == 0:
            actiontype = 'flag_dropped'
        elif subtype == 1:
            actiontype = 'flag_returned'
        elif subtype == 2:
            actiontype = 'flag_captured'
        else:
            return None
        return self.OnAction(cid, actiontype, data)

    def OnFlagReturn(self, action, data, match=None):
        # Flag Return: RED
        # Flag Return: BLUE
        # Flag Return: <color>
        color = match.group('color')
        return self.getEvent('EVT_GAME_FLAG_RETURNED', data=color)

    def OnPop(self, action, data, match=None):
        return self.getEvent('EVT_BOMB_EXPLODED')

    def OnBomb(self, action, data, match=None):
        cid = match.group('cid')
        subaction = match.group('subaction')
        if subaction == 'planted':
            actiontype = 'bomb_planted'
        elif subaction == 'defused':
            actiontype = 'bomb_defused'
        elif subaction == 'tossed':
            actiontype = 'bomb_tossed'
        elif subaction == 'collected':
            actiontype = 'bomb_collected'
        else:
            return None
        return self.OnAction(cid, actiontype, data)

    def OnBombholder(self, action, data, match=None):
        cid = match.group('cid')
        actiontype = 'bomb_holder_spawn'
        return self.OnAction(cid, actiontype, data)

    def OnAction(self, cid, actiontype, data, match=None):
        client = self.clients.getByCID(cid)
        if not client:
            self.debug('No client found')
            return None
        self.verbose('onAction: %s: %s %s' % (client.name, actiontype, data))
        return self.getEvent('EVT_CLIENT_ACTION', data=actiontype, client=client)

    def OnItem(self, action, data, match=None):
        # Item: 3 ut_item_helmet
        # Item: 0 team_CTF_redflag
        cid, item = string.split(data, ' ', 1)
        client = self.getByCidOrJoinPlayer(cid)
        if client:
            # correct flag/bomb-pickups
            if 'flag' in item or 'bomb' in item:
                self.verbose('Item pickup corrected to action: %s' % item)
                return self.OnAction(cid, item, data)
            # self.verbose('on_item: %s picked up %s' % (client.name, item) )
            return self.getEvent('EVT_CLIENT_ITEM_PICKUP', data=item, client=client)
        return None

    def OnSurvivorwinner(self, action, data, match=None):
        # SurvivorWinner: Blue
        # SurvivorWinner: Red
        # self.debug('EVENT: on_survivorwinner')
        # queue round and in any case (backwards compatibility for plugins)
        self.queueEvent(self.getEvent('EVT_GAME_ROUND_END'))
        return self.getEvent('EVT_SURVIVOR_WIN', data=data)

    def OnSay(self, action, data, match=None):
        # 3:53 say: 8 denzel: lol
        if match is None:
            return

        name = self.stripColors(match.group('name'))
        client = self.getByCidOrJoinPlayer(match.group('cid'))

        if not client or client.name != name:
            self.debug('Urban Terror bug spotted: trying to get client by name')
            client = self.clients.getByName(name)

        if not client:
            self.verbose('No client found')
            return None

        self.verbose('Client found: %s on slot %s' % (client.name, client.cid))

        data = match.group('text')

        # removal of weird characters
        if data and ord(data[:1]) == 21:
            data = data[1:]

        return self.getEvent('EVT_CLIENT_SAY', data=data, client=client)

    def OnSayteam(self, action, data, match=None):
        # 2:28 sayteam: 12 New_UrT_Player_v4.1: wokele
        if match is None:
            return
        
        name = self.stripColors(match.group('name'))
        client = self.getByCidOrJoinPlayer(match.group('cid'))

        if not client or client.name != name:
            self.debug('Urban Terror bug spotted: trying to get client by name')
            client = self.clients.getByName(name)

        if not client:
            self.verbose('no client found!')
            return None

        self.verbose('Client found: %s on slot %s' % (client.name, client.cid))

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        return self.getEvent('EVT_CLIENT_TEAM_SAY', data=data, client=client, target=client.team)

    def OnSaytell(self, action, data, match=None):
        # 5:39 saytell: 15 16 repelSteeltje: nno
        # 5:39 saytell: 15 15 repelSteeltje: nno
        if match is None:
            return

        name = self.stripColors(match.group('name'))
        client = self.getByCidOrJoinPlayer(match.group('cid'))
        target = self.clients.getByCID(match.group('acid'))

        if not client or client.name != name:
            self.debug('Urban Terror bug spotted: trying to get client by name')
            client = self.clients.getByName(name)

        if not client:
            self.verbose('No client found')
            return None

        self.verbose('client found: %s on slot %s' % (client.name, client.cid))

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        return self.getEvent('EVT_CLIENT_PRIVATE_SAY', data=data, client=client, target=target)

    def OnTell(self, action, data, match=None):
        # 5:27 tell: woekele to XLR8or: test
        # We'll use saytell instead
        #
        #client = self.clients.get_by_exact_name(match.group('name'))
        #target = self.clients.get_by_exact_name(match.group('aname'))
        #
        #if not client:
        #    self.verbose('no client found!')
        #    return None
        #
        #data = match.group('text')
        #if data and ord(data[:1]) == 21:
        #    data = data[1:]
        #
        #client.name = match.group('name')
        #return self.get_Event('EVT_CLIENT_PRIVATE_SAY', data=data, client=client, target=target)
        return None

    # endmap/shutdown
    def OnShutdowngame(self, action, data=None, match=None):
        self.game.mapEnd()
        # self.clients.sync()
        # self.debug('Synchronizing client info')
        self._maplist = None  # when UrT server reloads, newly uploaded maps get available: force refresh
        return self.getEvent('EVT_GAME_EXIT', data=data)

    # Startgame
    def OnInitgame(self, action, data, match=None):
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
        return self.getEvent('EVT_GAME_ROUND_START', data=self.game)

    def OnWarmup(self, action, data=None, match=None):
        self.game.rounds = 0
        return self.getEvent('EVT_GAME_WARMUP', data=data)

    def OnInitround(self, action, data, match=None):
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
        return self.getEvent('EVT_GAME_ROUND_START', data=self.game)

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def broadcast(self, text):
        """
        A Say variant in UrT which will print text upper left, server message area.
        :param text: The message to be sent.
        """
        lines = []
        message = prefixText([self.msgPrefix], text)
        message = message.strip()
        for line in self.getWrap(message):
            lines.append(self.getCommand('broadcast', message=line))
        self.writelines(lines)

    def saybig(self, text):
        """
        Print a message in the center screen.
        :param text: The message to be sent.
        """
        lines = []
        message = prefixText([self.msgPrefix], text)
        message = message.strip()
        for line in self.getWrap(message):
            lines.append(self.getCommand('saybig', message=line))
        self.writelines(lines)

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Ban a given client.
        :param client: The client to ban
        :param reason: The reason for this ban
        :param admin: The admin who performed the ban
        :param silent: Whether or not to announce this ban
        """
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, b3.clients.Client) and not client.guid:
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('ban', cid=client, reason=reason))
            return
        elif not client.id:
            # no client id, database must be down, do tempban
            self.error('Q3AParser.ban(): no client id, database must be down, doing tempban')
            return self.tempban(client, reason, '1d', admin, silent)

        if admin:
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
            fullreason = self.getMessage('banned_by', variables)
        else:
            variables = self.getMessageVariables(client=client, reason=reason)
            fullreason = self.getMessage('banned', variables)

        if client.cid is None:
            # ban by ip, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s', self.getCommand('banByIp', ip=client.ip, reason=reason))
            self.write(self.getCommand('banByIp', ip=client.ip, reason=reason))
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s', self.getCommand('ban', cid=client.cid, reason=reason))
            self.write(self.getCommand('ban', cid=client.cid, reason=reason))

        if not silent and fullreason != '':
            self.say(fullreason)

        if admin:
            admin.message('^7Banned^7: ^1%s^7 (^2@%s^7)' % (client.exactName, client.id))
            admin.message('^7His last ip (^1%s^7) has been added to banlist' % client.ip)

        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', data={'reason': reason, 'admin': admin}, client=client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a client.
        :param client: The client to unban
        :param reason: The reason for the unban
        :param admin: The admin who unbanned this client
        :param silent: Whether or not to announce this unban
        """
        self.debug('EFFECTIVE UNBAN : %s', self.getCommand('unbanByIp', ip=client.ip, reason=reason))
        cmd = self.getCommand('unbanByIp', ip=client.ip, reason=reason)
        # UrT adds multiple instances to banlist.txt
        # Make sure we remove up to 5 duplicates in a separate thread
        self.writelines([cmd, cmd, cmd, cmd, cmd])
        if admin:
            admin.message('^7Unbanned^7: ^1%s^7 (^2@%s^7)' % (client.exactName, client.id))
            admin.message('^7His last ip (^1%s^7) has been removed from banlist' % client.ip)
            admin.message('^7Trying to remove duplicates...')

        self.queueEvent(self.getEvent('EVT_CLIENT_UNBAN', data=admin, client=client))

    def getPlayerPings(self, filter_client_ids=None):
        """
        Returns a dict having players' id for keys and players' ping for values.
        :param filter_client_ids: If filter_client_id is an iterable, only return values for the given client ids.
        """
        data = self.write('status')
        if not data:
            return dict()

        players = dict()
        for line in data.split('\n'):
            m = re.match(self._regPlayer, line.strip())
            if m:
                if m.group('ping') == 'ZMBI':
                    # ignore them, let them not bother us with errors
                    pass
                else:
                    try:
                        players[str(m.group('slot'))] = int(m.group('ping'))
                    except ValueError:
                        players[str(m.group('slot'))] = 999

        return players

    def sync(self):
        """
        For all connected players returned by self.get_player_list(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        """
        self.debug('synchronizing client info')
        plist = self.getPlayerList(maxRetries=4)
        mlist = dict()

        for cid, c in plist.iteritems():
            client = self.getByCidOrJoinPlayer(cid)
            if client:
                # Disconnect the zombies first
                if c['ping'] == 'ZMBI':
                    self.debug('slot is in state zombie: %s - ignoring', c['ip'])
                    # client.disconnect()
                elif client.guid and 'guid' in c:
                    if client.guid == c['guid']:
                        # player matches
                        self.debug('in-sync %s == %s', client.guid, c['guid'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.guid, c['guid'])
                        client.disconnect()
                elif client.ip and 'ip' in c:
                    if client.ip == c['ip']:
                        # player matches
                        self.debug('in-sync %s == %s', client.ip, c['ip'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.ip, c['ip'])
                        client.disconnect()
                else:
                    self.debug('no-sync: no guid or ip found')

        return mlist

    def rotateMap(self):
        """
        Load the next map/level.
        """
        self.say('^7Changing to next map')
        time.sleep(1)
        self.write('cyclemap')

    def changeMap(self, map_name):
        """
        Load a given map/level.
        """
        rv = self.getMapsSoundingLike(map_name)
        if isinstance(rv, basestring):
            self.say('^7Changing map to %s' % rv)
            time.sleep(1)
            self.write('map %s' % rv)
        else:
            return rv

    def getMaps(self):
        """
        Return the available maps/levels name.
        """
        if self._maplist is not None:
            return self._maplist

        data = self.write('fdir *.bsp', socketTimeout=15)
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

    def inflictCustomPenalty(self, penalty_type, client, reason=None, duration=None, admin=None, data=None):
        """
        Urban Terror specific punishments.
        """
        if penalty_type == 'slap' and client:
            cmd = self.getCommand('slap', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif penalty_type == 'nuke' and client:
            cmd = self.getCommand('nuke', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif penalty_type == 'mute' and client:
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

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def getTeam(self, team):
        """
        Return a B3 team given the team value.
        :param team: The team value
        """
        if str(team).lower() == 'red':
            team = 1
        elif str(team).lower() == 'blue':
            team = 2
        elif str(team).lower() == 'spectator':
            team = 3
        elif str(team).lower() == 'free':
            team = -1  # will fall back to b3.TEAM_UNKNOWN

        team = int(team)
        if team == 1:
            result = b3.TEAM_RED
        elif team == 2:
            result = b3.TEAM_BLUE
        elif team == 3:
            result = b3.TEAM_SPEC
        else:
            result = b3.TEAM_UNKNOWN

        return result

    def defineGameType(self, gametype_int):
        """
        Translate the gametype to a readable format (also for teamkill plugin!)
        """
        _gametype = str(gametype_int)

        if gametype_int == '0':
            _gametype = 'ffa'
        elif gametype_int == '1':   # Dunno what this one is
            _gametype = 'dm'
        elif gametype_int == '2':   # Dunno either
            _gametype = 'dm'
        elif gametype_int == '3':
            _gametype = 'tdm'
        elif gametype_int == '4':
            _gametype = 'ts'
        elif gametype_int == '5':
            _gametype = 'ftl'
        elif gametype_int == '6':
            _gametype = 'cah'
        elif gametype_int == '7':
            _gametype = 'ctf'
        elif gametype_int == '8':
            _gametype = 'bm'

        return _gametype

    def getNextMap(self):
        """
        Return the next map/level name to be played.
        """
        cvars = self.cvarList('g_next')
        # let's first check if a vote passed for the next map
        nmap = cvars.get('g_nextmap')
        self.debug('g_nextmap: %s' % nmap)
        if nmap != "":
            return nmap
        
        nmap = cvars.get('g_nextcyclemap')
        self.debug('g_nextcyclemap: %s' % nmap)
        if nmap != "":
            return nmap
        
        return None

    def getMapsSoundingLike(self, mapname):
        """
        Return a valid mapname.
        If no exact match is found, then return close candidates as a list.
        """
        wanted_map = mapname.lower()
        supported_maps = self.getMaps()
        if wanted_map in supported_maps:
            return wanted_map

        cleaned_supported_maps = {}
        for map_name in supported_maps:
            cleaned_supported_maps[re.sub("^ut4?_", '', map_name, count=1)] = map_name

        if wanted_map in cleaned_supported_maps:
            return cleaned_supported_maps[wanted_map]

        cleaned_wanted_map = re.sub("^ut4?_", '', wanted_map, count=1)

        matches = [cleaned_supported_maps[match] for match in getStuffSoundingLike(cleaned_wanted_map,
                                                                                   cleaned_supported_maps.keys())]
        if len(matches) == 1:
            # one match, get the map id
            return matches[0]
        else:
            # multiple matches, provide suggestions
            return matches

    def getTeamScores(self):
        """
        Return current team scores in a tuple.
        """
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
        NOTE: this won't work properly if the server has private slots.
        See http://forums.urbanterror.net/index.php/topic,9356.0.html
        """
        data = self.write('players')
        if not data:
            return None

        scores = {'red': None, 'blue': None, 'players': {}}
        line = data.split('\n')[2]
        m = re.match(self._reTeamScores, line.strip())
        if m:
            scores['red'] = int(m.group('RedScore'))
            scores['blue'] = int(m.group('BlueScore'))

        for line in data.split('\n')[3:]:
            m = re.match(self._rePlayerScore, line.strip())
            if m:
                scores['players'][int(m.group('slot'))] = {'kills': int(m.group('kill')),
                                                           'deaths': int(m.group('death'))}

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
            self.debug('Client %s probably disconnected, but its character is still hanging in game...' % cid)
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
        """
        Return the client matchign the given string.
        Will create a new client if needed
        """
        client = self.clients.getByCID(cid)
        if client:
            return client
        else:
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfo(None, userinfostring)
            return self.clients.getByCID(cid)

    def getPlayerTeams(self):
        """
        Return a dict having cid as keys and a B3 team as value for
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

        NOTE: this won't work fully if the server has private slots.
        see http://forums.urbanterror.net/index.php/topic,9356.0.html
        """
        player_teams = dict()
        letters2slots = dict(A='0', C='2', B='1', E='4', D='3', G='6', F='5', I='8', H='7', K='10', J='9', M='12',
                             L='11', O='14', N='13', Q='16', P='15', S='18', R='17', U='20', T='19', W='22',
                             V='21', Y='24', X='23', Z='25')

        players_data = self.write('players')
        for line in players_data.split('\n')[3:]:
            self.debug(line.strip())
            m = re.match(self._rePlayerScore, line.strip())
            if m and line.strip() != '0:  FREE k:0 d:0 ping:0':
                cid = m.group('slot')
                team = self.getTeam(m.group('team'))
                player_teams[cid] = team

        cvars = self.cvarList("*teamlist")
        g_blueteamlist = cvars.get('g_blueteamlist')
        if g_blueteamlist:
            for letter in g_blueteamlist:
                player_teams[letters2slots[letter]] = b3.TEAM_BLUE

        g_redteamlist = cvars.get('g_redteamlist')
        if g_redteamlist:
            for letter in g_redteamlist:
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
        """
        on Hit: lines identifiers for weapons are different than
        the one on Kill: lines
        """
        try:
            return self.hitweapon2killweapon[int(hitweapon_id)]
        except KeyError, err:
            self.warning("Unknown weapon ID on Hit line: %s", err)
            return None

    def cvarList(self, cvar_filter=None):
        """
        Return a dict having cvar id as keys and strings values.
        If cvar_filter is provided, it will be passed to the rcon cvarlist command as a parameter.

        /rcon cvarlist
            cvarlist
            S R     g_modversion "4.2.009"
            S R     auth_status "public"
            S R     auth "1"
            S       g_enablePrecip "0"
            S R     g_survivor "0"
            S     C g_antilagvis "0"

            6 total cvars
            6 cvar indexes
        """
        cvars = dict()
        cmd = 'cvarlist' if cvar_filter is None else ('cvarlist %s' % cvar_filter)
        raw_data = self.write(cmd)
        if raw_data:
            re_line = re.compile(r"""^.{7} (?P<cvar>\s*\w+)\s+"(?P<value>.*)"$""", re.MULTILINE)
            for m in re_line.finditer(raw_data):
                cvars[m.group('cvar').lower()] = m.group('value')
        return cvars

########################################################################################################################
# ----- Actions --------------------------------------------------------------------------------------------------------
# Item: 0 team_CTF_redflag -> Flag Taken/picked up
# Flag: 0 0: team_CTF_blueflag -> Flag Dropped
# Flag: 0 1: team_CTF_blueflag -> Flag Returned
# Flag: 0 2: team_CTF_blueflag -> Flag Captured
#
# Bombholder is 5 -> Spawn with the bomb
# Bomb was planted by 5
# Bomb was defused by 6!
# Bomb was tossed by 4 -> either manually or by being killed
# Bomb has been collected by 6 -> Picking up a tossed bomb
#
# ----- Connection Info ------------------------------------------------------------------------------------------------
# A little documentation on the ClientSlot states in relation to ping positions in the status response
#
# UrT ClientSlot states:
# CS_FREE,     // can be reused for a new connection
# CS_ZOMBIE,   // client has been disconnected, but don't reuse
#              // connection for a couple seconds
# CS_CONNECTED // has been assigned to a client_t, but no gamestate yet
# CS_PRIMED,   // gamestate has been sent, but client hasn't sent a usercmd
# CS_ACTIVE    // client is fully in game
#
# Snippet 1:
# if (cl->state == CS_CONNECTED)
#             Com_Printf ("CNCT ");
#         else if (cl->state == CS_ZOMBIE)
#             Com_Printf ("ZMBI ");
#         else
#         {
#             ping = cl->ping < 9999 ? cl->ping : 9999;
#             Com_Printf ("%4i ", ping);
#         }
#
# Snippet 2:
# if (cl->state == CS_ZOMBIE && cl->lastPacketTime < zombiepoint) {
#   // using the client id cause the cl->name is empty at this point
#   Com_DPrintf( "Going from CS_ZOMBIE to CS_FREE for client %d\n", i );
#   cl->state = CS_FREE; // can now be reused
# }
#
# ----- Available variables defined on Init ----------------------------------------------------------------------------
# 081027 14:53:22 DEBUG   EVENT: on_initgame
# 081027 14:53:22 VERBOSE ...self.console.game.sv_allowdownload: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_matchmode: 0
# 081027 14:53:22 VERBOSE ...self.console.game.sv_maxclients: 16
# 081027 14:53:22 VERBOSE ...self.console.game.sv_floodprotect: 1
# 081027 14:53:22 VERBOSE ...self.console.game.g_warmup: 15
# 081027 14:53:22 VERBOSE ...self.console.game.capturelimit: 0
# 081027 14:53:22 VERBOSE ...self.console.game.sv_hostname:   ^1[SNT]^7 TDM #4 Dungeon (B3)
# 081027 14:53:22 VERBOSE ...self.console.game.g_followstrict: 1
# 081027 14:53:22 VERBOSE ...self.console.game.fraglimit: 0
# 081027 14:53:22 VERBOSE ...self.console.game.timelimit: 15
# 081027 14:53:22 VERBOSE ...self.console.game.g_cahtime: 60
# 081027 14:53:22 VERBOSE ...self.console.game.g_swaproles: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_roundtime: 3
# 081027 14:53:22 VERBOSE ...self.console.game.g_bombexplodetime: 40
# 081027 14:53:22 VERBOSE ...self.console.game.g_bombdefusetime: 10
# 081027 14:53:22 VERBOSE ...self.console.game.g_hotpotato: 2
# 081027 14:53:22 VERBOSE ...self.console.game.g_waverespawns: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_redwave: 15
# 081027 14:53:22 VERBOSE ...self.console.game.g_bluewave: 15
# 081027 14:53:22 VERBOSE ...self.console.game.g_respawndelay: 3
# 081027 14:53:22 VERBOSE ...self.console.game.g_suddendeath: 1
# 081027 14:53:22 VERBOSE ...self.console.game.g_maxrounds: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_friendlyfire: 1
# 081027 14:53:22 VERBOSE ...self.console.game.g_allowvote: 536870920
# 081027 14:53:22 VERBOSE ...self.console.game.g_armbands: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_survivorrule: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_gear: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_deadchat: 1
# 081027 14:53:22 VERBOSE ...self.console.game.g_maxGameClients: 0
# 081027 14:53:22 VERBOSE ...self.console.game.sv_dlURL: sweetopia.snt.utwente.nl/xlr
# 081027 14:53:22 VERBOSE ...self.console.game.sv_maxPing: 250
# 081027 14:53:22 VERBOSE ...self.console.game.sv_minPing: 0
# 081027 14:53:22 VERBOSE ...self.console.game.sv_maxRate: 0
# 081027 14:53:22 VERBOSE ...self.console.game.sv_minRate: 0
# 081027 14:53:22 VERBOSE ...self.console.game.dmflags: 0
# 081027 14:53:22 VERBOSE ...self.console.game.version: ioq3 1.35urt linux-i386 Dec 20 2007
# 081027 14:53:22 VERBOSE ...self.console.game.protocol: 68
# 081027 14:53:22 VERBOSE ...self.console.game.mapname: ut4_turnpike
# 081027 14:53:22 VERBOSE ...self.console.game.sv_privateClients: 4
# 081027 14:53:22 VERBOSE ...self.console.game. Admin:  XLR8or
# 081027 14:53:22 VERBOSE ...self.console.game. Email: admin@xlr8or.com
# 081027 14:53:22 VERBOSE ...self.console.game.gameName: q3ut4
# 081027 14:53:22 VERBOSE ...self.console.game.g_needpass: 1
# 081027 14:53:22 VERBOSE ...self.console.game.g_enableDust: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_enableBreath: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_antilagvis: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_survivor: 0
# 081027 14:53:22 VERBOSE ...self.console.game.g_enablePrecip: 2
# 081027 14:53:22 VERBOSE ...self.console.game.g_modversion: 4.1
# 081027 14:53:22 VERBOSE ...self.console.game.gameType: tdm
########################################################################################################################