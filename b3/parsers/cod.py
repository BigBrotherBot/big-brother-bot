# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
# 7/23/2005 - 1.1.0
#    * Added damage type to Damage and Kill event data
# 27/6/2009 - 1.3.1 - xlr8or - Added Action Mechanism (event) for version 1.1.5 
# 28/8/2009 - 1.3.2 - Bakes - added regexp for CoD4 suicides
# 17/1/2010 - 1.3.3 - xlr8or - moved sync to InitGame (30 second delay)
# 25/1/2010 - 1.4.0 - xlr8or - refactored cod parser series
# 26/1/2010 - 1.4.1 - xlr8or
#    * Added authorizeClients() for IpsOnly
#    * minor bugfixes after initial tests
# 26/1/2010 - 1.4.2 - xlr8or - Added mapEnd() on Exitlevel
# 27/1/2010 - 1.4.3 - xlr8or - Minor bugfix in sync() for IpsOnly
# 28/1/2010 - 1.4.4 - xlr8or - Make sure cid is entering Authentication queue only once. 
# 29/1/2010 - 1.4.5 - xlr8or - Minor rewrite of Auth queue check 
# 31/1/2010 - 1.4.6 - xlr8or
#    * Added unban for non pb servers
#    * Fixed bug: rcon command banid replaced by banclient
# 28/3/2010 - 1.4.7 - xlr8or - Added PunkBuster activity check on startup
# 18/4/2010 - 1.4.8 - xlr8or - Trying to prevent key errors in newPlayer()
# 18/4/2010 - 1.4.9 - xlr8or - Forcing g_logsync to make server write unbuffered gamelogs
# 01/5/2010 - 1.4.10 - xlr8or - delegate guid length checking to cod parser
# 24/5/2010 - 1.4.11 - xlr8or - check if guids match on existing client objects when joining after a mapchange
# 30/5/2010 - 1.4.12 - xlr8or - adding dummy setVersionExceptions() to enable overriding of variables based on the shortversion 
# 10/8/2010 - 1.4.13 - xlr8or - fixed a bug where clients would be disconnected after mapchange.  
# 10/9/2010 - 1.4.14 - xlr8or - don't save client.name on say and sayteam when name is the same (sanitization problem)
# 24/10/2010 - 1.4.15 - xlr8or - some documentation on line formats
# 07/11/2010 - 1.4.16 - GrosBedo - messages now support named $variables instead of %s
# 08/11/2010 - 1.4.17 - GrosBedo - messages can now be empty (no message broadcasted on kick/tempban/ban/unban)
# 02/02/2011 - 1.4.18 - xlr8or - add cod7 suicide _lineformat
# 16/03/2011 - 1.4.19 - xlr8or - improve PunkBuster check
# 28/03/2011 - 1.4.20 - Bravo17 - CoD5 JT regexp fix

__author__  = 'ThorN, xlr8or'
__version__ = '1.4.20'

import re, string, threading
import b3
import b3.events
from b3.parsers.q3a.abstractParser import AbstractParser
import b3.parsers.punkbuster

class CodParser(AbstractParser):
    gameName = 'cod'
    IpsOnly = False
    _guidLength = 6 # (minimum) length of the guid
    _pbRegExp = re.compile(r'^[0-9a-f]{32}$', re.IGNORECASE) # RegExp to match a PunkBuster ID
    _logSync = 3 # Value for unbuffered game logging (append mode)
    _counter = {}
    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 120

    _commands = {}
    _commands['message'] = 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'
    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'banclient %(cid)s'
    _commands['unban'] = 'unbanuser %(name)s' # remove players from game engine's ban.txt
    _commands['tempban'] = 'clientkick %(cid)s'

    _eventMap = {
        'warmup' : b3.events.EVT_GAME_WARMUP,
        'restartgame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    #0:00 InitGame: \g_gametype\dm\gamename\Call of Duty
    _lineFormats = (
        # server events
        re.compile(r'^(?P<action>[a-z]+):\s?(?P<data>.*)$', re.IGNORECASE),

        # world kills
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9-]{1,2});(?P<team>[a-z]+);(?P<name>[^;]+);(?P<aguid>[^;]*);(?P<acid>-1);(?P<ateam>world);(?P<aname>[^;]*);(?P<aweap>[a-z0-9_-]+);(?P<damage>[0-9.]+);(?P<dtype>[A-Z_]+);(?P<dlocation>[a-z_]+))$', re.IGNORECASE),
        # player kills/damage
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<team>[a-z]*);(?P<name>[^;]+);(?P<aguid>[^;]+);(?P<acid>[0-9]{1,2});(?P<ateam>[a-z]*);(?P<aname>[^;]+);(?P<aweap>[a-z0-9_-]+);(?P<damage>[0-9.]+);(?P<dtype>[A-Z_]+);(?P<dlocation>[a-z_]+))$', re.IGNORECASE),
        # suicides (cod4/cod5)
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<team>[a-z]*);(?P<name>[^;]+);(?P<aguid>[^;]*);(?P<acid>-1);(?P<ateam>[a-z]*);(?P<aname>[^;]+);(?P<aweap>[a-z0-9_-]+);(?P<damage>[0-9.]+);(?P<dtype>[A-Z_]+);(?P<dlocation>[a-z_]+))$', re.IGNORECASE),
        # suicides (cod7)
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<team>[a-z]*);(?P<name>[^;]+);(?P<aguid>[^;]*);(?P<acid>[0-9]{1,2});(?P<ateam>[a-z]*);(?P<aname>[^;]+);(?P<aweap>[a-z0-9_-]+);(?P<damage>[0-9.]+);(?P<dtype>[A-Z_]+);(?P<dlocation>[a-z_]+))$', re.IGNORECASE),

        #team actions
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<team>[a-z]+);(?P<name>[^;]+);(?P<type>[a-z_]+))$', re.IGNORECASE),
        
        # Join Team (cod5)
        re.compile(r'^(?P<action>JT);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<team>[a-z]+);(?P<name>[^;]+);)$', re.IGNORECASE),

        # tell like events
        re.compile(r'^(?P<action>[a-z]+);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<name>[^;]+);(?P<aguid>[^;]+);(?P<acid>[0-9]{1,2});(?P<aname>[^;]+);(?P<text>.*))$', re.IGNORECASE),
        # say like events
        re.compile(r'^(?P<action>[a-z]+);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<name>[^;]+);(?P<text>.*))$', re.IGNORECASE),

        # all other events
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<name>[^;]+))$', re.IGNORECASE)
    )
    # All Log Line Formats see bottom of File

    #num score ping guid   name            lastmsg address               qport rate
    #--- ----- ---- ------ --------------- ------- --------------------- ----- -----
    #2     0   29 465030 <-{^4AS^7}-^3ThorN^7->^7       50 68.63.6.62:-32085      6597  5000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)

    PunkBuster = None

    def startup(self):
        if self.IpsOnly:
            self.debug('Authentication Method: Using Ip\'s instead of GUID\'s!')
        # add the world client
        client = self.clients.newClient(-1, guid='WORLD', name='World', hide=True, pbid='WORLD')

        if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
            # test if PunkBuster is active
            result = self.write('PB_SV_Ver')
            if result != '' and result[:7] != 'Unknown':
                self.info('PunkBuster Active: %s' %result) 
                self.PunkBuster = b3.parsers.punkbuster.PunkBuster(self)
            else:
                self.warning('PunkBuster test FAILED, Check your game server setup and B3 config! Disabling PB support!')

        # get map from the status rcon command
        map = self.getMap()
        if map:
            self.game.mapName = map
            self.info('map is: %s'%self.game.mapName)

        # Force g_logsync
        self.debug('Forcing server cvar g_logsync to %s' % self._logSync)
        self.write('set g_logsync %s' %self._logSync)

        # get gamepaths/vars
        try:
            self.game.fs_game = self.getCvar('fs_game').getString()
        except:
            self.game.fs_game = None
            self.warning('Could not query server for fs_game')

        try:
            self.game.fs_basepath = self.getCvar('fs_basepath').getString().rstrip('/')
            self.debug('fs_basepath: %s' % self.game.fs_basepath)
        except:
            self.game.fs_basepath = None
            self.warning('Could not query server for fs_basepath')

        try:
            self.game.fs_homepath = self.getCvar('fs_homepath').getString().rstrip('/')
            self.debug('fs_homepath: %s' % self.game.fs_homepath)
        except:
            self.game.fs_homepath = None
            self.warning('Could not query server for fs_homepath')
        try:
            self.game.shortversion = self.getCvar('shortversion').getString()
            self.debug('shortversion: %s' % self.game.shortversion)
        except:
            self.game.shortversion = None
            self.warning('Could not query server for shortversion')

        self.setVersionExceptions()
        self.debug('Parser started.')

    def setVersionExceptions(self):
        """\
        Dummy to enable shortversionexceptions for cod2.
        Use this function in inheriting parsers to override certain vars based on ie. shortversion
        """
        pass

    # kill
    def OnK(self, action, data, match=None):
        victim = self.getClient(victim=match)
        if not victim:
            self.debug('No victim')
            self.OnJ(action, data, match)
            return None

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.debug('No attacker')
            return None

        attacker.team = self.getTeam(match.group('ateam'))
        attacker.name = match.group('aname')
        victim.team = self.getTeam(match.group('team'))
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_KILL

        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

    # damage
    def OnD(self, action, data, match=None):
        victim = self.getClient(victim=match)
        if not victim:
            self.debug('No victim - attempt join')
            self.OnJ(action, data, match)
            return None

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.debug('No attacker')
            return None

        attacker.team = self.getTeam(match.group('ateam'))
        attacker.name = match.group('aname')
        victim.team = self.getTeam(match.group('team'))
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_DAMAGE
        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_DAMAGE_SELF
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_DAMAGE_TEAM

        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

    # disconnect
    def OnQ(self, action, data, match=None):
        client = self.getClient(match)
        if client:
            client.disconnect()
        else:
            # Check if we're in the authentication queue
            if match.group('cid') in self._counter:
                # Flag it to remove from the queue
                self._counter[cid] = 'Disconnected'
                self.debug('slot %s has disconnected or was forwarded to our http download location, removing from authentication queue...' % cid)
        return None

    # join
    def OnJ(self, action, data, match=None):
        codguid = match.group('guid')
        cid = match.group('cid')
        name = match.group('name')
        
        if len(codguid) < self._guidLength:
            # invalid guid
            self.verbose2('Invalid GUID: %s' %codguid)
            codguid = None

        client = self.getClient(match)

        if client:
            self.verbose2('ClientObject already exists')
            # lets see if the name/guids match for this client, prevent player mixups after mapchange (not with PunkBuster enabled)
            if not self.PunkBuster:
                if self.IpsOnly:
                    # this needs testing since the name cleanup code may interfere with this next condition
                    if name != client.name:
                        self.debug('This is not the correct client (%s <> %s), disconnecting' %(name, client.name))
                        client.disconnect()
                        return None
                    else:
                        self.verbose2('client.name in sync: %s == %s' %(name, client.name))
                else:
                    if codguid != client.guid:
                        self.debug('This is not the correct client (%s <> %s), disconnecting' %(codguid, client.guid))
                        client.disconnect()
                        return None
                    else:
                        self.verbose2('client.guid in sync: %s == %s' %(codguid, client.guid))
            # update existing client
            client.state = b3.STATE_ALIVE
            # possible name changed
            client.name = name
            # Join-event for mapcount reasons and so forth
            return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)
        else:
            if self._counter.get(cid):
                self.verbose('cid: %s already in authentication queue. Aborting Join.' %cid)
                return None
            self._counter[cid] = 1
            t = threading.Timer(2, self.newPlayer, (cid, codguid, name))
            t.start()
            self.debug('%s connected, waiting for Authentication...' %name)
            self.debug('Our Authentication queue: %s' % self._counter)


    # action
    def OnA(self, action, data, match=None):
        #A;136528;6;allies;{^6AS^7}^6Honey;re_pickup
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            
            client = self.getClient(match)

            if not client:
                return None

        client.name = match.group('name')
        actiontype = match.group('type')
        self.verbose('OnAction: %s: %s' % (client.name, actiontype) )
        return b3.events.Event(b3.events.EVT_CLIENT_ACTION, actiontype, client)

    def OnSay(self, action, data, match=None):
        #3:12 say: <-{AS}-ThorN->: sfs
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            
            client = self.getClient(match)

            if not client:
                return None

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        if client.name != match.group('name'):
            client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_SAY, data, client)

    def OnSayteam(self, action, data, match=None):
        #3:12 sayteam: <-{AS}-ThorN->: sfs
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            
            client = self.getClient(match)

            if not client:
                return None

        data = match.group('text')
        # sometimes there is a weird character in the message
        # remove if it is there
        if data and ord(data[:1]) == 21:
            data = data[1:]

        if client.name != match.group('name'):
            client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, data, client)

    def OnTell(self, action, data, match=None):
        #4197:48tell;465030;2;ThorN;465030;2;ThorN;testing
        client = self.getClient(match)
        tclient = self.getClient(attacker=match)

        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            
            client = self.getClient(match)

            if not client:
                return None

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_PRIVATE_SAY, data, client, tclient)

    def OnInitgame(self, action, data, match=None):
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', data)

        for o in options:
            if o[0] == 'mapname':
                self.game.mapName = o[1]
            elif o[0] == 'g_gametype':
                self.game.gameType = o[1]
            elif o[0] == 'fs_game':
                self.game.modName = o[1]
            else:
                setattr(self.game, o[0], o[1])

        self.verbose('...self.console.game.gameType: %s' % self.game.gameType)
        self.game.startRound()

        #Sync clients 30 sec after InitGame
        t = threading.Timer(30, self.clients.sync)
        t.start()
        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)

    def OnExitlevel(self, action, data, match=None):
        self.game.mapEnd()
        return b3.events.Event(b3.events.EVT_GAME_EXIT, data)

    def OnItem(self, action, data, match=None):
        guid, cid, name, item = string.split(data, ';', 3)
        client = self.clients.getByCID(cid)
        if client:
            return b3.events.Event(b3.events.EVT_CLIENT_ITEM_PICKUP, item, client)
        return None

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        if self.PunkBuster:
            if client.pbid:
                result = self.PunkBuster.unBanGUID(client)

                if result:                    
                    admin.message('^3Unbanned^7: %s^7: %s' % (client.exactName, result))

                if admin:
                    fullreason = self.getMessage('unbanned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
                else:
                    fullreason = self.getMessage('unbanned', self.getMessageVariables(client=client, reason=reason))

                if not silent and fullreason != '':
                    self.say(fullreason)
            elif admin:
                admin.message('%s^7 unbanned but has no punkbuster id' % client.exactName)
        else:
            _name = self.stripColors(client.exactName)
            result = self.write(self.getCommand('unban', name=_name, reason=reason))
            if admin:
                admin.message(result)

    def getTeam(self, team):
        if team == 'allies':
            return b3.TEAM_BLUE
        elif team == 'axis':
            return b3.TEAM_RED
        else:
            return b3.TEAM_UNKNOWN

    _reMap = re.compile(r'map ([a-z0-9_-]+)', re.I)
    def getMaps(self):
        maps = self.getCvar('sv_mapRotation')

        nmaps = []
        if maps:
            maps = re.findall(self._reMap, maps[0])

            for m in maps:
                if m[:3] == 'mp_':
                    m = m[3:]

                nmaps.append(m.title())

        return nmaps

    def getNextMap(self):
        if not self.game.mapName: return None
        
        maps = self.getCvar('sv_mapRotation')

        if maps:
            maps = re.findall(self._reMap, maps[0])

            gmap = self.game.mapName.strip().lower()

            found = False
            for nmap in maps:
                nmap = nmap.strip().lower()
                if found:
                    found = nmap
                    break
                elif nmap == gmap:
                    # current map, break on next map
                    found = True

            if found == True:
                # map is first map in rotation
                nmap = maps[0].strip().lower()

            if found:
                if nmap[:3] == 'mp_': nmap = nmap[3:]
                return nmap.title()

            return None
        else:
            return None

    def sync(self):
        self.debug('Synchronising Clients.')
        plist = self.getPlayerList(maxRetries=4)
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                if client.guid and c.has_key('guid') and not self.IpsOnly:
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
                self.debug('%s found in status/playerList' %p['name'])
                return p

    def newPlayer(self, cid, codguid, name):
        if not self._counter.get(cid):
            self.verbose('newPlayer thread no longer needed, Key no longer available')
            return None
        if self._counter.get(cid) == 'Disconnected':
            self.debug('%s disconnected, removing from authentication queue' %name)
            self._counter.pop(cid)
            return None
        self.debug('newClient: %s, %s, %s' %(cid, codguid, name) )
        sp = self.connectClient(cid)
        # PunkBuster is enabled, using PB guid
        if sp and self.PunkBuster:
            self.debug('sp: %s' % sp)
            # test if pbid is valid, otherwise break off and wait for another cycle to authenticate
            if not re.match(self._pbRegExp, sp['pbid']):
                self.debug('PB-id is not valid! Giving it another try.')
                self._counter[cid] +=1
                t = threading.Timer(4, self.newPlayer, (cid, codguid, name))
                t.start()
                return None
            if self.IpsOnly:
                guid = sp['ip']
                pbid = sp['pbid']
            else:
                guid = sp['pbid']
                pbid = guid # save pbid in both fields to be consistent with other pb enabled databases
            ip = sp['ip']
            if self._counter.get(cid):
                self._counter.pop(cid)
            else:
                return None
        # PunkBuster is not enabled, using codguid
        elif sp:
            if self.IpsOnly:
                codguid = sp['ip']
            if not codguid:
                self.warning('Missing or wrong CodGuid and PunkBuster is disabled... cannot authenticate!')
                if self._counter.get(cid):
                    self._counter.pop(cid)
                return None
            else:
                guid = codguid
                pbid = None
                ip = sp['ip']
                if self._counter.get(cid):
                    self._counter.pop(cid)
                else:
                    return None
        elif self._counter.get(cid) > 10:
            self.debug('Couldn\'t Auth %s, giving up...' % name)
            if self._counter.get(cid):
                self._counter.pop(cid)
            return None
        # Player is not in the status response (yet), retry
        else:
            if self._counter.get(cid):
                self.debug('%s not yet fully connected, retrying...#:%s' %(name, self._counter.get(cid)))
                self._counter[cid] +=1
                t = threading.Timer(4, self.newPlayer, (cid, codguid, name))
                t.start()
            else:
                #Falling trough
                self.warning('All authentication attempts failed.')
            return None
            
        client = self.clients.newClient(cid, name=name, ip=ip, state=b3.STATE_ALIVE, guid=guid, pbid=pbid, data={ 'codguid' : codguid })
        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client))

    def authorizeClients(self):
        players = self.getPlayerList(maxRetries=4)
        self.verbose('authorizeClients() = %s' % players)

        for cid, p in players.iteritems():
            sp = self.clients.getByCID(cid)
            if sp:
                # Only set provided data, otherwise use the currently set data
                sp.ip   = p.get('ip', sp.ip)
                sp.pbid = p.get('pbid', sp.pbid)
                if self.IpsOnly:
                    sp.guid = p.get('ip', sp.guid)
                else:
                    sp.guid = p.get('guid', sp.guid)
                sp.data = p
                sp.auth()

#--LogLineFormats---------------------------------------------------------------

#===============================================================================
# 
# *** CoD:
# Join:               J;160913;10;PlayerName
# Quit:               Q;160913;10;PlayerName
# Damage by world:    D;160913;14;axis;PlayerName;;-1;world;;none;6;MOD_FALLING;none
# Damage by opponent: D;160913;19;allies;PlayerName;248102;10;axis;OpponentName;mp44_mp;27;MOD_PISTOL_BULLET;right_foot
# Kill:               K;160913;4;axis;PlayerName;578287;0;axis;OpponentName;kar98k_mp;180;MOD_HEAD_SHOT;head
# Weapon/ammo pickup: Weapon;160913;8;PlayerName;m1garand_mp
# Action:             A;160913;16;axis;PlayerName;htf_scored
# Say to All:         say;160913;8;PlayerName;^Ubye
# Say to Team:        sayteam;160913;8;PlayerName;^Ulol
# Private message:    tell;160913;12;PlayerName1;1322833;8;PlayerName2;what message?
# Winners:            W;axis;160913;PlayerName1;258015;PlayerName2
# Losers:             L;allies;160913;PlayerName1;763816;PlayerName2
# 
# ExitLevel:          ExitLevel: executed
# Shutdown Engine:    ShutdownGame:
# Seperator:          ------------------------------------------------------------
# InitGame:           InitGame: \_Admin\xlr8or\_b3\B3 v1.2.1b [posix]\_Email\admin@xlr8or.com\_Host\[SNT]
#                    \_Location\Twente University - The Netherlands\_URL\http://games.snt.utwente.nl/\fs_game\xlr1.7
#                    \g_antilag\1\g_gametype\tdm\gamename\Call of Duty 2\mapname\mp_toujane\protocol\115
#                    \scr_friendlyfire\3\scr_killcam\1\shortversion\1.0\sv_allowAnonymous\0\sv_floodProtect\1
#                    \sv_hostname\^5[SNT] #3 ^7Tactical Gaming ^9(^7B3^9) (^1v1.0^9)\sv_maxclients\24\sv_maxPing\220
#                    \sv_maxRate\20000\sv_minPing\0\sv_privateClients\8\sv_pure\1\sv_voice\1
# 
# 
# *** CoD5 specific lines:
# JoinTeam:           JT;283895439;17;axis;PlayerName;
#                    AD;564;allies;580090035;6;axis;PlayerName;stg44_mp;30;MOD_RIFLE_BULLET;right_arm_lower
#===============================================================================
