# OpenArena 0.8.1 parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 Courgette & GrosBedo
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA    02110-1301    USA
#
# CHANGELOG
# 08/08/2010 - 0.1 - Courgette
# * creation based on smg11 parser
# 09/08/2010 - 0.2 - Courgette
# * implement rotatemap()
# 09/08/2010 - 0.3 - Courgette & GrosBedo
# * bot now recognize /tell commands correctly
# 10/08/2010 - 0.4 - Courgette
# * recognizes MOD_SUICIDE as suicide
# * get rid of PunkBuster related code
# * should \rcon dumpuser in cases the ClientUserInfoChanged line does not have
#   guid while player is not a bot. (untested, cannot reproduce)
# 11/08/2010 - 0.5 - GrosBedo
# * minor fix for the /rcon dumpuser when no guid
# * added !nextmap (with recursive detection !)
# 11/08/2010 - 0.6 - GrosBedo
# * fixed the permanent ban command (banClient -> banaddr)
# 12/08/2010 - 0.7 - GrosBedo
# * added weapons and means of death. Define what means of death are suicides
# 17/08/2010 - 0.7.1 - GrosBedo
# * added say_team recognition
# 20/08/2010 - 0.7.5 - GrosBedo
# * added many more regexp to detect ctf events, cvars and awards
# * implement permban by ip and unbanbyip
# * implement team recognition
# 20/08/2010 - 0.8 - Courgette
# * clean regexp (Item, CTF, Award, fallback)
# * clean OnItem
# * remove OnDamage
# * add OnCtf and OnAward
# 27/08/2010 - 0.8.1 - GrosBedo
# * fixed findnextmap underscore bug (maps and vstr cvars with an underscore are now correctly parsed)
# 28/08/2010 - 0.8.2 - Courgette
# * fix another findnextmap underscore bug
# 28/08/2010 - 0.8.3 - Courgette
# * fix issue with the regexp that match 'Award:' lines
# 04/09/2010 - 0.8.4 - GrosBedo
# * fix issue with CTF flag capture events
# 17/09/2010 - 0.8.5 - GrosBedo
# * fix crash issue when a player has disconnected at the very time the bot check for the list of players
# 20/10/2010 - 0.9 - GrosBedo
# * fix a BIG issue when detecting teams (were always unknown)
# 20/10/2010 - 0.9.1 - GrosBedo
# * fix tk issue with DM and other team free gametypes
# 20/10/2010 - 0.9.2 - GrosBedo
# * added EVT_GAME_FLAG_RETURNED (move it to q3a or a generic ioquake3 parser?)
# 23/10/2010 - 0.9.3 - GrosBedo
# * detect gametype and modname at startup
# * added flag_taken action
# * fix a small bug when triggering the flag return event
# 07/11/2010 - 0.9.4 - GrosBedo
# * ban and unban messages are now more generic and can be configured from b3.xml
# * messages now support named $variables instead of %s
# 08/11/2010 - 0.9.5 - GrosBedo
# * messages can now be empty (no message broadcasted on kick/tempban/ban/unban)
# 09/04/2011 - 0.9.6 - Courgette
# * reflect that cid are not converted to int anymore in the clients module
# 06/06/2011 - 0.10.0 - Courgette
# * change data format for EVT_CLIENT_BAN events
# 14/06/2011 - 0.11.0 - Courgette
# * cvar code moved to q3a AbstractParser
#
__author__  = 'Courgette, GrosBedo'
__version__ = '0.11.0'

import re, string, thread, time, threading
import b3
import b3.events
from b3.parsers.q3a.abstractParser import AbstractParser

class Oa081Parser(AbstractParser):
    gameName = 'oa081'
    _connectingSlots = []
    _maplist = None
    
    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _empty_name_default = 'EmptyNameDefault'

    _commands = {}
    #_commands['message'] = 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    #_commands['deadsay'] = 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['message'] = 'say %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'say %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'
    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'banaddr %(cid)s' #addip for q3a
    _commands['tempban'] = 'clientkick %(cid)s'
    _commands['banByIp'] = 'banaddr %(ip)s'
    _commands['unbanByIp'] = 'bandel %(cid)s' #removeip for q3a
    _commands['banlist'] = 'listbans' #g_banips for q3a

    _eventMap = {
        'warmup' : b3.events.EVT_GAME_WARMUP,
        'restartgame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:.]+\s?)?')

    _lineFormats = (
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<pbid>[0-9A-Z]{32}):\s*(?P<name>[^:]+):\s*(?P<num1>[0-9]+):\s*(?P<num2>[0-9]+):\s*(?P<ip>[0-9.]+):(?P<port>[0-9]+))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<name>.+):\s+(?P<text>.*))$', re.IGNORECASE),
        
        # 1:25 CTF: 1 2 2: Sarge returned the BLUE flag!
        # 1:16 CTF: 1 1 3: Sarge fragged RED's flag carrier!
        # 6:55 CTF: 2 1 2: Burpman returned the RED flag!
        # 7:02 CTF: 2 2 1: Burpman captured the BLUE flag!
        re.compile(r'^(?P<action>CTF):\s+(?P<cid>[0-9]+)\s+(?P<fid>[0-9]+)\s+(?P<type>[0-9]+):\s+(?P<data>.*(?P<color>RED|BLUE).*)$', re.IGNORECASE),
        
        #47:05 Kill: 2 4 11: Sarge killed ^6Jondah by MOD_LIGHTNING
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        
        # 7:02 Award: 2 4: Burpman gained the CAPTURE award!
        # 7:02 Award: 2 5: Burpman gained the ASSIST award!
        # 7:30 Award: 2 3: Burpman gained the DEFENCE award!
        # 29:15 Award: 2 2: SalaManderDragneL gained the IMPRESSIVE award!
        # 32:08 Award: 2 1: SalaManderDragneL gained the EXCELLENT award!
        # 8:36 Award: 10 1: Karamel is a fake gained the EXCELLENT award!
        re.compile(r'^(?P<action>Award):\s+(?P<cid>[0-9]+)\s+(?P<awardtype>[0-9]+):\s+(?P<data>(?P<name>.+) gained the (?P<awardname>\w+) award!)$', re.IGNORECASE),

        #
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+)\s(?P<text>.*))$', re.IGNORECASE),

        # 81:16 tell: grosbedo to courgette: !help
        # 81:16 say: grosbedo: !help
        re.compile(r'^(?P<action>tell):\s(?P<data>(?P<name>.+) to (?P<aname>.+): (?P<text>.*))$', re.IGNORECASE),
        
        # 19:33 sayteam: UnnamedPlayer: ahahaha
        re.compile(r'^(?P<action>sayteam):\s(?P<data>(?P<name>.+): (?P<text>.*))$', re.IGNORECASE),

        # 46:37 Item: 4 team_CTF_redflag
        # 54:52 Item: 2 weapon_plasmagun
        re.compile(r'^(?P<action>Item):\s+(?P<cid>[0-9]+)\s+(?P<data>.*)$', re.IGNORECASE),

        #
        # Falling through?
        # 1:05 ClientConnect: 3
        # 1:05 ClientUserinfoChanged: 3 guid\CAB616192CB5652375401264987A23D0\n\xlr8or\t\0\model\wq_male2/red\g_redteam\\g_blueteam\\hc\100\w\0\l\0\tt\0\tl\0
        re.compile(r'^(?P<action>[a-z_]\w*):\s*(?P<data>.*)$', re.IGNORECASE)
    )

    #map: dm_fort
    #num score ping name            lastmsg address               qport rate
    #--- ----- ---- --------------- ------- --------------------- ----- -----
    #  1     1    0 TheMexican^7          100 bot                       0 16384
    #  2     1    0 Sentenza^7             50 bot                       0 16384
    #  3     3   37 xlr8or^7                0 145.99.135.227:27960   3598 25000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)
    _reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')

    # 7:44 Exit: Capturelimit hit.
    # 7:44 red:8  blue:0
    # 7:44 score: 63  ping: 81  client: 2 ^2^^0Pha^7nt^2om^7^^0Boo
    # 7:44 score: 0  ping: 0  client: 1 Sarge
    _reTeamScores = re.compile(r'^red:(?P<RedScore>.+)\s+blue:(?P<BlueScore>.+)$', re.I)
    _rePlayerScore = re.compile(r'^score:\s+(?P<score>[0-9]+)\s+ping:\s+(?P<ping>[0-9]+|CNCT|ZMBI)\s+client:\s+(?P<slot>[0-9]+)\s+(?P<name>.*)$', re.I)

    
    # Ban #1: 200.200.200.200/32
    _reBanList = re.compile(r'^Ban #(?P<cid>[0-9]+):\s+(?P<ip>[0-9]+.[0-9]+.[0-9]+.[0-9]+)/(?P<range>[0-9]+)$', re.I)

    PunkBuster = None


    ##  means of death
    #===========================================================================
    MOD_UNKNOWN = 0
    MOD_SHOTGUN = 1
    MOD_GAUNTLET = 2
    MOD_MACHINEGUN = 3
    MOD_GRENADE = 4
    MOD_GRENADE_SPLASH = 5
    MOD_ROCKET = 6
    MOD_ROCKET_SPLASH = 7
    MOD_PLASMA = 8
    MOD_PLASMA_SPLASH = 9
    MOD_RAILGUN = 10
    MOD_LIGHTNING = 11
    MOD_BFG = 12
    MOD_BFG_SPLASH = 13
    MOD_WATER = 14
    MOD_SLIME = 15
    MOD_LAVA = 16
    MOD_CRUSH = 17
    MOD_TELEFRAG = 18
    MOD_FALLING = 19
    MOD_SUICIDE = 20
    MOD_TARGET_LASER = 21
    MOD_TRIGGER_HURT = 22
    # #ifdef MISSIONPACK
    MOD_NAIL = 23
    MOD_CHAINGUN = 24
    MOD_PROXIMITY_MINE = 25
    MOD_KAMIKAZE = 26
    MOD_JUICED = 27
    # #endif
    MOD_GRAPPLE = 28
    #===========================================================================

    
    ## meansOfDeath to be considered suicides
    Suicides = (
        MOD_WATER,
        MOD_SLIME,
        MOD_LAVA,
        MOD_CRUSH,
        MOD_FALLING,
        MOD_SUICIDE,
        MOD_TRIGGER_HURT,
    )
#---------------------------------------------------------------------------------------------------

    def startup(self):
    
        # registering a ioquake3 specific event
        self.Events.createEvent('EVT_GAME_FLAG_RETURNED', 'Flag returned')

        # add the world client
        self.clients.newClient('1022', guid='WORLD', name='World', hide=True, pbid='WORLD')

        # get map from the status rcon command
        map_name = self.getMap()
        if map_name:
            self.game.mapName = map_name
            self.info('map is: %s'%self.game.mapName)

        # get gamepaths/vars
        try:
            fs_game = self.getCvar('fs_game').getString()
            if fs_game == '':
                fs_game = 'baseoa'
            self.game.fs_game = fs_game
            self.game.modName = fs_game
            self.debug('fs_game: %s' % self.game.fs_game)
        except:
            self.game.fs_game = None
            self.game.modName = None
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

        try:
            self.game.gameType = self.defineGameType(self.getCvar('g_gametype').getString())
            self.debug('g_gametype: %s' % self.game.gameType)
        except:
            self.game.gameType = None
            self.warning("Could not query server for g_gametype")

        # initialize connected clients
        self.info('discover connected clients')
        plist = self.getPlayerList()
        for cid, c in plist.iteritems():
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfochanged(None, userinfostring)
        
            
#---------------------------------------------------------------------------------------------------

    # Added for debugging and identifying/catching log lineparts
    def getLineParts(self, line):
        line = re.sub(self._lineClear, '', line, 1)

        for f in self._lineFormats:
            m = re.match(f, line)
            if m:
                self.debug('XLR--------> line matched %s' % f.pattern)
                break

        if m:
            client = None
            target = None
            
            try:
                action =  m.group('action').lower()
            except IndexError:
                # special case for damage lines where no action group can be set
                action = 'damage'
            
            return (m, action, m.group('data').strip(), client, target)
        elif '------' not in line:
            self.verbose('XLR--------> line did not match format: %s' % line)

#---------------------------------------------------------------------------------------------------
       
        
    def OnClientconnect(self, action, data, match=None):
        client = self.clients.getByCID(data)
        self.debug('OnClientConnect: %s, %s' % (data, client))
        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)

    # Parse Userinfo
    def OnClientuserinfochanged(self, action, data, match=None):
        if data is None: # if the client disconnected and we are trying to force the server to give us an id, we end up with an empty data object, so we just return and everything should be fine (the slot should already be removed ln 336)
            return
        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info %s' % bclient)
        if bclient:
            cid = bclient['cid']
            
            if cid in self._connectingSlots:
                self.debug('client on slot %s is already being connected' % cid)
                return
            
            self._connectingSlots.append(cid)
            client = self.clients.getByCID(cid)

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    setattr(client, k, v)
            else:
                if not bclient.has_key('name'):
                    bclient['name'] = self._empty_name_default

                if bclient.has_key('guid'):
                    guid = bclient['guid']
                else:
                    if bclient.has_key('skill'):
                        guid = 'BOT-' + str(cid)
                        self.verbose('BOT connected!')
                        self.clients.newClient(cid, name=bclient['name'], ip='0.0.0.0', state=b3.STATE_ALIVE, guid=guid, data={ 'guid' : guid }, team=bclient['team'], money=20)
                        self._connectingSlots.remove(cid)
                        return None
                    else:
                        self.info('we are missing the guid but this is not a bot either, dumpuser')
                        self._connectingSlots.remove(cid)
                        self.OnClientuserinfochanged(None, self.queryClientUserInfoByCid(cid))
                        return
                
                if not bclient.has_key('ip'):
                    infoclient = self.parseUserInfo(self.queryClientUserInfoByCid(cid))
                    if 'ip' in infoclient:
                        bclient['ip'] = infoclient['ip']
                    else:
                        self.warning('failed to get client ip')
                
                if bclient.has_key('ip'):
                    self.clients.newClient(cid, name=bclient['name'], ip=bclient['ip'], state=b3.STATE_ALIVE, guid=guid, data={ 'guid' : guid }, team=bclient['team'], money=20)
                else:
                    self.warning('failed to get connect client')
                    
            self._connectingSlots.remove(cid)
                
        return None

    # disconnect
    def OnKill(self, action, data, match=None):
        self.debug('OnKill: %s (%s)'%(match.group('aweap'),match.group('text')))
        
        victim = self.getByCidOrJoinPlayer(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnClientuserinfochanged(action, data, match)
            return None

        weapon = match.group('aweap')
        if not weapon:
            self.debug('No weapon')
            return None

        ## Fix attacker
        if match.group('aweap') in self.Suicides:
            # those kills should be considered suicides
            self.debug('OnKill: Fixed attacker, suicide detected: %s' %match.group('text'))
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
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team != b3.TEAM_FREE and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        # if not defined we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'
        
        victim.state = b3.STATE_DEAD
        #self.verbose('OnKill Victim: %s, Attacker: %s, Weapon: %s, Hitloc: %s, dType: %s' % (victim.name, attacker.name, weapon, victim.hitloc, dType))
        # need to pass some amount of damage for the teamkill plugin - 100 is a kill
        return b3.events.Event(event, (100, weapon, victim.hitloc, dType), attacker, victim)

    def OnClientdisconnect(self, action, data, match=None):
        client = self.clients.getByCID(data)
        if client: client.disconnect()
        return None

    # startgame
    def OnInitgame(self, action, data, match=None):
        self.debug('OnInitgame: %s' % data)
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', data)

        for o in options:
            if o[0] == 'mapname':
                self.game.mapName = o[1]
            elif o[0] == 'g_gametype':
                self.game.gameType = self.defineGameType(o[1])
            elif o[0] == 'fs_game':
                self.game.modName = o[1]
            else:
                #self.debug('%s = %s' % (o[0],o[1]))
                setattr(self.game, o[0], o[1])

        self.verbose('...self.console.game.gameType: %s' % self.game.gameType)
        self.game.startRound()

        self.debug('Synchronizing client info')
        self.clients.sync()

        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)


    def OnSayteam(self, action, data, match=None):
        # Teaminfo does not exist in the sayteam logline, so we can't know in which team the user is in. So we set him in a -1 void team.
        client = self.clients.getByExactName(match.group('name'))

        if not client:
            self.verbose('No Client Found')
            return None

        data = match.group('text')
        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, data, client, -1)


    def OnTell(self, action, data, match=None):
        #5:27 tell: woekele to XLR8or: test

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

    # Action
    def OnAction(self, cid, actiontype, data, match=None):
        #Need example
        client = self.clients.getByCID(cid)
        if not client:
            self.debug('No client found')
            return None
        self.verbose('OnAction: %s: %s %s' % (client.name, actiontype, data) )
        return b3.events.Event(b3.events.EVT_CLIENT_ACTION, actiontype, client)

    def OnItem(self, action, data, match=None):
        client = self.getByCidOrJoinPlayer(match.group('cid'))
        if client:
            return b3.events.Event(b3.events.EVT_CLIENT_ITEM_PICKUP, match.group('data'), client)
        return None

    def OnCtf(self, action, data, match=None):
        # 1:25 CTF: 1 2 2: Sarge returned the BLUE flag!
        # 1:16 CTF: 1 1 3: Sarge fragged RED's flag carrier!
        # 6:55 CTF: 2 1 2: Burpman returned the RED flag!
        # 7:02 CTF: 2 2 1: Burpman captured the BLUE flag!
        # 2:12 CTF: 3 1 0: Tanisha got the RED flag!
        # 2:12 CTF: 3 2 0: Tanisha got the BLUE flag!

        cid = match.group('cid')
        client = self.getByCidOrJoinPlayer(match.group('cid'))
        flagteam = self.getTeam(match.group('fid'))
        flagcolor = match.group('color')
        action_types = {
            '0': 'flag_taken',
            '1': 'flag_captured',
            '2': 'flag_returned',
            '3': 'flag_carrier_kill',
        }
        try:
            action_id = action_types[match.group('type')]
        except KeyError:
            action_id = 'flag_action_' + match.group('type')
            self.debug('unknown CTF action type: %s (%s)' % (match.group('type'), match.group('data')))
        self.debug('CTF Event: %s from team %s %s by %s' %(action_id, flagcolor, flagteam, client.name))
        if action_id == 'flag_returned':
            return b3.events.Event(b3.events.EVT_GAME_FLAG_RETURNED, flagcolor)
        else:
            return self.OnAction(cid, action_id, data)
            #return b3.events.Event(b3.events.EVT_CLIENT_ACTION, action_id, client)

    def OnAward(self, action, data, match=None):
        ## Award: <cid> <awardtype>: <name> gained the <awardname> award!
        # 7:02 Award: 2 4: Burpman gained the CAPTURE award!
        # 7:02 Award: 2 5: Burpman gained the ASSIST award!
        # 7:30 Award: 2 3: Burpman gained the DEFENCE award!
        # 29:15 Award: 2 2: SalaManderDragneL gained the IMPRESSIVE award!
        # 32:08 Award: 2 1: SalaManderDragneL gained the EXCELLENT award!
        # 8:36 Award: 10 1: Karamel is a fake gained the EXCELLENT award!
        client = self.getByCidOrJoinPlayer(match.group('cid'))
        action_type = 'award_%s' % match.group('awardname')
        return b3.events.Event(b3.events.EVT_CLIENT_ACTION, action_type, client)


#---------------------------------------------------------------------------------------------------

    def parseUserInfo(self, info):
        #ClientUserinfoChanged: 0 n\Courgette\t\0\model\sarge/classic\hmodel\sarge/classic\g_redteam\\g_blueteam\\c1\2\c2\7\hc\100\w\0\l\0\tt\0\tl\0\id\201AB4BBC40B4EC7445B49CE82D209EC
        playerID, info = string.split(info, ' ', 1)

        if info[:1] != '\\':
            info = '\\' + info

        options = re.findall(r'\\([^\\]+)\\([^\\]+)', info)

        data = {}
        for o in options:
            data[o[0]] = o[1]

        data['cid'] = playerID

        if data.has_key('n'):
            data['name'] = data['n']

        t = -1
        if data.has_key('team'):
            t = data['team']
        elif data.has_key('t'):
            t = data['t']

        data['team'] = self.getTeam(t)
        
        
        if data.has_key('id'):
            data['guid'] = data['id']
            del data['id']
        if data.has_key('cl_guid'):
            data['guid'] = data['cl_guid']
        
        return data


    def getTeam(self, team):
        team = str(team).lower() # We convert to a string and lower the case because there is a problem when trying to detect numbers if it's not a string (weird)
        if team == 'free' or team == '0':
            #self.debug('Team is Free (no team)')
            result = b3.TEAM_FREE
        elif team == 'red' or team == '1':
            #self.debug('Team is Red')
            result = b3.TEAM_RED
        elif team == 'blue' or team == '2':
            #self.debug('Team is Blue')
            result = b3.TEAM_BLUE
        elif team == 'spectator' or team == '3':
            #self.debug('Team is Spectator')
            result = b3.TEAM_SPEC
        else:
            #self.debug('Team is Unknown')
            result = b3.TEAM_UNKNOWN
        
        #self.debug('getTeam(%s) -> %s' % (team, result))
        return result

    # Translate the gameType to a readable format (also for teamkill plugin!)
    def defineGameType(self, gameTypeInt):

        _gameType = ''
        _gameType = str(gameTypeInt)
        #self.debug('gameTypeInt: %s' % gameTypeInt)
        
        if gameTypeInt == '0':
            _gameType = 'dm'        # Free for all
        elif gameTypeInt == '1':
            _gameType = 'du'        # Tourney
        elif gameTypeInt == '3':
            _gameType = 'tdm'       # Team Deathmatch
        elif gameTypeInt == '4':
            _gameType = 'ctf'        # Capture The Flag
        elif gameTypeInt == '8':
            _gameType = 'el'        # Elimination
        elif gameTypeInt == '9':
            _gameType = 'ctfel'        # CTF Elimination
        elif gameTypeInt == '10':
            _gameType = 'lms'        # Last Man Standing
        elif gameTypeInt == '11':
            _gameType = 'del'        # Double Domination
        elif gameTypeInt == '12':
            _gameType = 'dom'        # Domination
        
        #self.debug('_gameType: %s' % _gameType)
        return _gameType

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
        data = self.write('nextmap')
        nextmap = self.findNextMap(data)
        if nextmap:
            return nextmap
        else:
            return 'no nextmap set or it is in an unrecognized format !'

    def findNextMap(self, data):
        # "nextmap" is: "vstr next4; echo test; vstr aupo3; map oasago2"
        # the last command in the line is the one that decides what is the next map
        # in a case like : map oasago2; echo test; vstr nextmap6; vstr nextmap3
        # the parser will recursively look each last vstr var, and if it can't find a map, fallback to the last map command
        self.debug('Extracting nextmap name from: %s' % (data))
        nextmapregex = re.compile(r'.*("|;)\s*((?P<vstr>vstr (?P<vstrnextmap>[a-z0-9_]+))|(?P<map>map (?P<mapnextmap>[a-z0-9_]+)))', re.IGNORECASE)
        m = re.match(nextmapregex, data)
        if m:
            if m.group('map'):
                self.debug('Found nextmap: %s' % (m.group('mapnextmap')))
                return m.group('mapnextmap')
            elif m.group('vstr'):
                self.debug('Nextmap is redirecting to var: %s' % (m.group('vstrnextmap')))
                data = self.write(m.group('vstrnextmap'))
                result = self.findNextMap(data) # recursively dig into the vstr vars to find the last map called
                if result: # if a result was found in a deeper level, then we return it to the upper level, until we get back to the root level
                    return result
                else: # if none could be found, then try to find a map command in the current string
                    nextmapregex = re.compile(r'.*("|;)\s*(?P<map>map (?P<mapnextmap>[a-z0-9_]+))"', re.IGNORECASE)
                    m = re.match(nextmapregex, data)
                    if m.group('map'):
                        self.debug('Found nextmap: %s' % (m.group('mapnextmap')))
                        return m.group('mapnextmap')
                    else: # if none could be found, we go up a level by returning None (remember this is done recursively)
                        self.debug('No nextmap found in this string !')
                        return None
        else:
            self.debug('No nextmap found in this string !')
            return None

    def rotateMap(self):
        """\
        load the next map/level
        """
        self.write('vstr nextmap')

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

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, {'reason': reason, 'admin': admin}, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        data = self.write(self.getCommand('banlist', cid=-1))
        if not data:
            self.debug('Error : unban cannot be done, no ban list returned')
        else:
            for line in data.split('\n'):
                m = re.match(self._reBanList, line.strip())
                if m:
                    if m.group('ip') == client.ip:
                        self.write(self.getCommand('unbanByIp', cid=m.group('cid'), reason=reason))
                        self.debug('EFFECTIVE UNBAN : %s',self.getCommand('unbanByIp', cid=m.group('cid')))

                if admin:
                    fullreason = self.getMessage('unbanned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
                else:
                    fullreason = self.getMessage('unbanned', self.getMessageVariables(client=client, reason=reason))

                if not silent and fullreason != '':
                    self.say(fullreason)

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
                    players[str(m.group('slot'))] = int(m.group('ping'))

        return players

    def sync(self):
        plist = self.getPlayerList()
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.getByCidOrJoinPlayer(cid)
            if client:
                if client.guid and c.has_key('guid'):
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

    def connectClient(self, ccid):
        players = self.getPlayerList()
        self.verbose('connectClient() = %s' % players)

        for cid, p in players.iteritems():
            #self.debug('cid: %s, ccid: %s, p: %s' %(cid, ccid, p))
            if int(cid) == int(ccid):
                self.debug('Client found in status/playerList')
                return p
    
    
    def getByCidOrJoinPlayer(self, cid):
        client = self.clients.getByCID(cid)
        if client:
            return client
        else:
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfochanged(None, userinfostring)
            return self.clients.getByCID(cid)
        
        
    def queryClientUserInfoByCid(self, cid):
        """
        : dumpuser 5
        Player 5 is not on the server
        
        ]\rcon dumpuser 0
        userinfo
        --------
        ip                  81.56.143.41
        cg_cmdTimeNudge     0
        cg_delag            0
        cg_scorePlums       1
        cl_voip             0
        cg_predictItems     1
        cl_anonymous        0
        sex                 male
        handicap            100
        color2              7
        color1              2
        team_headmodel      sarge/classic
        team_model          sarge/classic
        headmodel           sarge/classic
        model               sarge/classic
        snaps               20
        rate                25000
        name                Courgette
        teamtask            0
        cl_guid             201AB4BBC40B4EC7445B49CE82D209EC
        teamoverlay         0
        """
        data = self.write('dumpuser %s' % cid)
        if not data:
            return None
        
        if data.split('\n')[0] != "userinfo":
            self.debug("dumpuser %s returned : %s" % (cid, data))
            return None

        datatransformed = "%s " % cid
        for line in data.split('\n'):
            if line.strip() == "userinfo" or line.strip() == "--------":
                continue

            var = line[:20].strip()
            val = line[20:].strip()
            datatransformed += "\\%s\\%s" % (var, val)

        return datatransformed

