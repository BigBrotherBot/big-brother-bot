#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
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
# 2010/03/09 - 0.1 - Courgette
# * parser is able to connect to a distant BFBC2 server through TCP
#   and listens for BFBC2 events.
# * BFBC2 events are routed to create matching B3 events
#

__author__  = 'Courgette'
__version__ = '0.1'

import sys, time, re, string, traceback
import b3
import b3.events
import b3.parser
from b3.parsers.punkbuster import PunkBuster
import rcon
import b3.cvar

from b3.parsers.bfbc2.bfbc2Connection import *


#----------------------------------------------------------------------------------------------------------------------------------------------
class Bfbc2Parser(b3.parser.Parser):
    gameName = 'bfbc2'
    privateMsg = True
    OutputClass = rcon.Rcon
    
    _bfbc2EventsListener = None
    _bfbc2Connection = None
    _nbConsecutiveConnFailure = 0
    _connectionTimeout = 60

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _commands = {}
    _commands['broadcast'] = '%(prefix)s^7 %(message)s'
    _commands['message'] = 'admin.yell "%(prefix)s ^3[pm]^7 %(message)s" %(duration)s %(cid)s '
    _commands['deadsay'] = 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'
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
    }

    PunkBuster = None

    def startup(self):
        try:
            self._connectionTimeout = self.config.getint('server', 'timeout')
        except: 
            self.warning("Error reading timeout from config file. Using default value")
        self.info("BFBC2 connection timeout: %s" % self._connectionTimeout)
        
        if self.config.has_option('server', 'punkbuster') and self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = PunkBuster(self)
            
        version = self.output.write('version')
        self.info('BFBC2 server version : %s' % version)
        if version[0] != 'BFBC2':
            raise Exception("the bfbc2 parser can only work with BattleField Bad Company 2")
        
        self.info('BFBC2 server info : %s' % self.output.write('serverInfo'))
        
        self.info('connecting all players...')
        for p in self.getPlayerList():
            self.debug('connecting %s' % p)

    def run(self, ):
        """Main worker thread for B3"""
        self.bot('Start listening ...')
        self.screen.write('Startup Complete : Let\'s get to work!\n\n')
        self.screen.write('(Please check %s in the B3 root directory for more detailed info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        while self.working:
            if self._paused:
                if self._pauseNotice == False:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                
                try:
                    if not self._bfbc2Connection:
                        self.verbose('Connecting to BFBC2 server ...')
                        self._bfbc2Connection = Bfbc2Connection(self._rconIp, self._rconPort, self._rconPassword)
                        self._bfbc2Connection.timeout = self._connectionTimeout
                        self._bfbc2Connection.subscribeToBfbc2Events()
                        self.clients.sync()
                        self._nbConsecutiveConnFailure = 0
                        
                    bfbc2packet = self._bfbc2Connection.handle_bfbc2_events()
                    self.console("%s: %s" % (bfbc2packet[0], bfbc2packet[1:]))
                    try:
                        self.routeBfbc2Packet(bfbc2packet)
                    except SystemExit:
                        raise
                    except Exception, msg:
                        self.error('could not route BFBC2 packet %s: %s', msg, traceback.extract_tb(sys.exc_info()[2]))
                except Bfbc2Exception, e:
                    self.debug(str(e))
                    self._nbConsecutiveConnFailure += 1
                    if self._nbConsecutiveConnFailure <= 10:
                        time.sleep(1.5)
                    elif self._nbConsecutiveConnFailure <= 16:
                        self.debug('sleeping 10 sec...')
                        time.sleep(10)
                    elif self._nbConsecutiveConnFailure <= 20:
                        self.debug('sleeping 1 minute...')
                        time.sleep(60)
                    
        self.bot('Stop listening.')

        if self.exiting.acquire(1):
            self.input.close()
            self.output.close()

            if self.exitcode:
                sys.exit(self.exitcode)

    def routeBfbc2Packet(self, packet):
        bfbc2EventType = packet[0]
        bfbc2EventData = packet[1:]
        
        match = re.search(r"^(?P<actor>[^.]+)\.on(?P<event>.+)$", bfbc2EventType)
        if match:
            func = 'On%s%s' % (string.capitalize(match.group('actor')), \
                               string.capitalize(match.group('event')))
            #self.debug("-==== FUNC!!: " + func)
            
        if match and hasattr(self, func):
            func = getattr(self, func)
            event = func(bfbc2EventType, bfbc2EventData)
            if event:
                self.queueEvent(event)
            
        elif bfbc2EventType in self._eventMap:
            self.queueEvent(b3.events.Event(
                    self._eventMap[bfbc2EventType],
                    bfbc2EventData))
        else:
            self.queueEvent(b3.events.Event(
                    b3.events.EVT_UNKNOWN,
                    str(bfbc2EventType) + ': ' + str(bfbc2EventData)))

    def getClientByExactNameOrConnect(self, exactName):
        client = self.clients.getByExactName(exactName)
        if client is None:
            self.output.write('')


    def getPlayerList(self, maxRetries=None):
        if self.PunkBuster:
            return self.PunkBuster.getPlayerList()
        else:
            data = self.write(('admin.listPlayers', 'all'))
            if not data:
                return {}

            players = {}
            for p in data:
                self.debug('player: %s' % p)
                continue
                m = re.match(self._regPlayer, line.strip())
                if m:
                    d = m.groupdict()
                    d['pbid'] = None
                    players[str(m.group('slot'))] = d
                #elif '------' not in line and 'map: ' not in line and 'num score ping' not in line:
                    #self.verbose('getPlayerList() = Line did not match format: %s' % line)

        return players


    def getMap(self):
        data = self.write('serverInfo')
        if not data:
            return None
        return data[4]
    


    #----------------------------------
    def OnPlayerChat(self, action, data):
        #['envex', 'gg']
        if not len(data) == 2:
            return None
        client = self.clients.getByExactName(data[0])
        return b3.events.Event(b3.events.EVT_CLIENT_SAY, data[1], client)


    def OnPlayerLeave(self, action, data):
        #player.onLeave: ['GunnDawg']
        client = self.clients.getByExactName(data[0])
        if client: 
            client.disconnect()
        return None
    

    def OnPlayerJoin(self, action, data):
        #player.onJoin: ['OrasiK']
        self.debug(self.output.write(''))
        self._clientConnectID = data
        return None


    def OnPlayerKill(self, action, data):
        #player.onKill: ['Juxta', '6blBaJlblu']
        if not len(data) == 2:
            return None
        attacker = self.clients.getByExactName(data[0])
        if not attacker:
            self.bot('No attacker')
            return None

        victim = self.clients.getByExactName(data[1])
        if not victim:
            self.bot('No victim')
            return None
        
        return b3.events.Event(b3.events.EVT_CLIENT_KILL, (100, None, None), attacker, victim)


    def OnPunkBusterMessage(self, action, data):
        self.debug("punkbuster message : %s" % data)
        return b3.events.Event(b3.events.EVT_UNKNOWN, data)







    def OnShutdowngame(self, action, data, match=None):
        #self.game.mapEnd()
        #self.clients.sync()
        return b3.events.Event(b3.events.EVT_GAME_ROUND_END, data)


    def OnExit(self, action, data, match=None):
        self.game.mapEnd()
        return b3.events.Event(b3.events.EVT_GAME_EXIT, None)

    def OnItem(self, action, data, match=None):
        client = self.getClient(match)
        if client:
            return b3.events.Event(b3.events.EVT_CLIENT_ITEM_PICKUP, match.group('text'), client)
        return None

    def OnClientbegin(self, action, data, match=None):
        # we get user info in two parts:
        # 19:42.36 ClientBegin: 4
        # 19:42.36 Userinfo: \cg_etVersion\ET Pro, ET 2.56\cg_u
        # we need to store the ClientConnect ID for the next call to userinfo

        self._clientConnectID = data

        return None

    def OnClientuserinfo(self, action, data, match=None):
        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info %s' % bclient)
        if bclient:
            client = self.clients.getByCID(bclient['cid'])

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    setattr(client, k, v)
            else:
                client = self.clients.newClient(bclient['cid'], **bclient)

        return None

    def OnClientuserinfochanged(self, action, data, match=None):
        return self.OnClientuserinfo(action, data, match)

    def OnUserinfo(self, action, data, match=None):
        #f = re.findall(r'\\name\\([^\\]+)', data)

        #if f:
        #    client = self.clients.getByExactName(f[0])
        #    if client:

        try:
            id = self._clientConnectID
        except:
            id = None

        self._clientConnectID = None

        if not id:
            self.error('OnUserinfo called without a ClientConnect ID')
            return None

        return self.OnClientuserinfo(action, '%s %s' % (id, data), match)

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

        self.game.startRound()

        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)



    def message(self, client, text):
        try:
            if client == None:
                self.say(text)
            elif client.cid == None:
                pass
            else:
                lines = []
                for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
                    lines.append(self.getCommand('message', cid=client.cid, prefix=self.msgPrefix, message=line))

                self.writelines(lines)
        except:
            pass

    def say(self, msg):
        lines = []
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            lines.append(self.getCommand('say', prefix=self.msgPrefix, message=line))

        if len(lines):        
            self.writelines(lines)

    def smartSay(self, client, msg):
        if client and (client.state == b3.STATE_DEAD or client.team == b3.TEAM_SPEC):
            self.verbose('say dead state: %s, team %s', client.state, client.team)
            self.sayDead(msg)
        else:
            self.verbose('say all')
            self.say(msg)

    def sayDead(self, msg):
        wrapped = self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length'])
        lines = []
        for client in self.clients.getClientsByState(b3.STATE_DEAD):
            if client.cid:                
                for line in wrapped:
                    lines.append(self.getCommand('deadsay', cid=client.cid, prefix=self.msgPrefix, message=line))

        if len(lines):        
            self.writelines(lines)

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        if isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('kick', cid=client, reason=reason))
            return
        elif admin:
            reason = self.getMessage('kicked_by', client.exactName, admin.exactName, reason)
        else:
            reason = self.getMessage('kicked', client.exactName, reason)

        if self.PunkBuster:
            self.PunkBuster.kick(client, 0.5, reason)
        else:
            self.write(self.getCommand('kick', cid=client.cid, reason=reason))

        if not silent:
            self.say(reason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_KICK, reason, client))
        client.disconnect()

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
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
            reason = self.getMessage('banned_by', client.exactName, admin.exactName, reason)
        else:
            reason = self.getMessage('banned', client.exactName, reason)

        if self.PunkBuster:
            self.PunkBuster.ban(client, reason)
            # bans will only last 7 days, this is a failsafe incase a ban cant
            # be removed from punkbuster
            #self.PunkBuster.kick(client, 1440 * 7, reason)
        else:
            self.write(self.getCommand('ban', cid=client.cid, reason=reason))

        if not silent:
            self.say(reason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, reason, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        if self.PunkBuster:
            if client.pbid:
                result = self.PunkBuster.unBanGUID(client)

                if result:                    
                    admin.message('^3Unbanned^7: %s^7: %s' % (client.exactName, result))

                if not silent:
                    if admin:
                        self.say(self.getMessage('unbanned_by', client.exactName, admin.exactName, reason))
                    else:
                        self.say(self.getMessage('unbanned', client.exactName, reason))
            elif admin:
                admin.message('%s^7 unbanned but has no punkbuster id' % client.exactName)
        elif admin:
            admin.message('^3Unbanned^7: %s^7. You may need to manually remove the user from the game\'s ban file.' % client.exactName)

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        duration = b3.functions.time2minutes(duration)

        if isinstance(client, b3.clients.Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('tempban', cid=client, reason=reason))
            return
        elif admin:
            reason = self.getMessage('temp_banned_by', client.exactName, admin.exactName, b3.functions.minutesStr(duration), reason)
        else:
            reason = self.getMessage('temp_banned', client.exactName, b3.functions.minutesStr(duration), reason)

        if self.PunkBuster:
            # punkbuster acts odd if you ban for more than a day
            # tempban for a day here and let b3 re-ban if the player
            # comes back
            if duration > 1440:
                duration = 1440

            self.PunkBuster.kick(client, duration, reason)
        else:
            self.write(self.getCommand('tempban', cid=client.cid, reason=reason))

        if not silent:
            self.say(reason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN_TEMP, reason, client))
        client.disconnect()




    def getTeam(self, team):
        team = int(team)
        if team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 3:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN

    def getPlayerPings(self):
        return None
        data = self.write('status')
        if not data:
            return {}

        players = {}
        for line in data.split('\n'):
            #self.debug('Line: ' + line + "-")
            m = re.match(self._regPlayerShort, line)
            if not m:
                m = re.match(self._regPlayer, line.strip())
            
            if m:
                players[str(m.group('slot'))] = int(m.group('ping'))
            #elif '------' not in line and 'map: ' not in line and 'num score ping' not in line:
                #self.verbose('getPlayerScores() = Line did not match format: %s' % line)
        
        return players
        
    def getPlayerScores(self):
        return None
        data = self.write('status')
        if not data:
            return {}

        players = {}
        for line in data.split('\n'):
            #self.debug('Line: ' + line + "-")
            m = re.match(self._regPlayerShort, line)
            if not m:
                m = re.match(self._regPlayer, line.strip())
            
            if m:  
                players[str(m.group('slot'))] = int(m.group('score'))
            #elif '------' not in line and 'map: ' not in line and 'num score ping' not in line:
                #self.verbose('getPlayerScores() = Line did not match format: %s' % line)
        
        return players


    def getCvar(self, cvarName):
        return None
        if self._reCvarName.match(cvarName):
            #"g_password" is:"^7" default:"scrim^7"
            val = self.write(cvarName)
            self.debug('Get cvar %s = [%s]', cvarName, val)
            #sv_mapRotation is:gametype sd map mp_brecourt map mp_carentan map mp_dawnville map mp_depot map mp_harbor map mp_hurtgen map mp_neuville map mp_pavlov map mp_powcamp map mp_railyard map mp_rocket map mp_stalingrad^7 default:^7

            m = self._reCvar.match(val)
            if m and m.group('cvar').lower() == cvarName.lower():
                return b3.cvar.Cvar(m.group('cvar'), value=m.group('value'), default=m.group('default'))

        return None

    def set(self, cvarName, value):
        self.warning('Parser.set() is depreciated, use Parser.setCvar() instead')
        self.setCvar(cvarName, value)

    def setCvar(self, cvarName, value):
        return None
        if re.match('^[a-z0-9_.]+$', cvarName, re.I):
            self.debug('Set cvar %s = [%s]', cvarName, value)
            self.write(self.getCommand('set', name=cvarName, value=value))
        else:
            self.error('%s is not a valid cvar name', cvarName)

    
    def getMaps(self):
        return None

    def sync(self):
        plist = self.getPlayerList()
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
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

    def authorizeClients(self):
        players = self.getPlayerList(maxRetries=4)
        self.verbose('authorizeClients() = %s' % players)

        for cid, p in players.iteritems():
            sp = self.clients.getByCID(cid)
            if sp:
                # Only set provided data, otherwise use the currently set data
                sp.ip   = p.get('ip', sp.ip)
                sp.pbid = p.get('pbid', sp.pbid)
                sp.guid = p.get('guid', sp.guid)
                sp.data = p
                sp.auth()
