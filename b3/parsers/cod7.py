# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010
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
# CHANGELOG
#
# 15.01.2011 - 1.0.0 - Freelander, Courgette
#   * Initial release
# 22.01.2011 - 1.0.1 - Freelander
#   * Do not try to authenticate [3arc]democlient
#   * Inherits from cod5 parser now to handle actions
# 01.02.2011 - 1.0.2 - Freelander
#   * Force glogsync to 1 on every round start as it may be lost after a 
#     server restart/crash 
# 01.02.2011 - 1.0.3 - Just a baka
#   * Pre-Match Logic
# 08.02.2011 - 1.0.4 - Just a baka
#   * Reworked Pre-Match logic to reflect latest changes to cod7http

## @file
#  CoD7 Parser

__author__  = 'Freelander, Courgette, Just a baka'
__version__ = '1.0.4'

import re
import string
import threading
import b3.parsers.cod7_rcon as rcon
import b3.parsers.cod5

class Cod7Parser(b3.parsers.cod5.Cod5Parser):
    gameName = 'cod7'
    IpsOnly = False
    _guidLength = 5
    OutputClass = rcon.Cod7Rcon

    _usePreMatchLogic = True
    _preMatch = False
    _elFound = True
    _igBlockFound = False
    _sgFound = False
    _logTimer = 0
    _logTimerOld = 0

    """\
    Next actions need translation to the EVT_CLIENT_ACTION (Treyarch has a different approach on actions)
    While IW put all EVT_CLIENT_ACTION in the A; action, Treyarch creates a different action for each EVT_CLIENT_ACTION.
    """
    _actionMap = (
        'AD', # Actor Damage (dogs)
        'VD'  # Vehicle Damage
    )

    #num score ping guid                             name            lastmsg address               qport rate
    #--- ----- ---- -------------------------------- --------------- ------- --------------------- ----- -----
    #  4     0   23 blablablabfa218d4be29e7168c637be ^1XLR^78^9or[^7^7               0 135.94.165.296:63564  25313 25000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)(?P<qportsep>[-\s]+)(?P<qport>[0-9-]+)\s+(?P<rate>[0-9]+)$', re.I)
    _regPlayerWithDemoclient = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+|unknown):?(?P<port>[0-9-]+)?(?P<qportsep>[-\s]+)(?P<qport>[0-9-]+)\s+(?P<rate>[0-9]+)$', re.I)

    def startup(self):
        """Implements some necessary tasks on initial B3 start."""

        # add the world client
        client = self.clients.newClient(-1, guid='WORLD', name='World', hide=True, pbid='WORLD')

        # get map from the status rcon command
        map = self.getMap()
        if map:
            self.game.mapName = map
            self.info('map is: %s'%self.game.mapName)

        if self.config.has_option('server', 'use_prematch_logic'):
            self._usePreMatchLogic = self.config.getboolean('server', 'use_prematch_logic')

        # Pre-Match Logic part 1
        if self._usePreMatchLogic:
            self._regPlayer, self._regPlayerWithDemoclient = self._regPlayerWithDemoclient, self._regPlayer
            playerList = self.getPlayerList()
            self._regPlayer, self._regPlayerWithDemoclient = self._regPlayerWithDemoclient, self._regPlayer
        
            if len(playerList) >= 6:
                self.verbose('PREMATCH OFF: PlayerCount >=6: not a Pre-Match')
                self._preMatch = False
            elif '0' in playerList and playerList['0']['guid'] == '0':
                self.verbose('PREMATCH OFF: Got a democlient presence: not a Pre-Match')
                self._preMatch = False
            else:
                self.verbose('PREMATCH ON: PlayerCount < 6, got no democlient presence. Defaulting to a pre-match.')
                self._preMatch = True
        else:
            self._preMatch = False

        # Force g_logsync
        self.debug('Forcing server cvar g_logsync to %s and turning UNIX timestamp log timers off.' % self._logSync)
        self.write('g_logsync %s' % self._logSync)
        self.write('g_logTimeStampInSeconds 0')

        self.setVersionExceptions()
        self.debug('Parser started.')

    def parseLine(self, line):
        """Called from parseLine method in Parser class to introduce pre-match logic
        and action mapping
        """

        m = self.getLineParts(line)
        if not m:
            return False

        match, action, data, client, target = m

        func = 'On%s' % string.capwords(action).replace(' ','')

        # Timer (in seconds) that always reflects the current event's timestamp
        t = re.match(self._lineTime, line)
        if t:
            self._logTimerOld = self._logTimer
            self._logTimer = int(t.group('minutes')) * 60 + int(t.group('seconds'))

        # Pre-Match Logic part 2
        # Ignore Pre-Match K/D-events
        if self._preMatch and (func == 'OnD' or func == 'OnK' or func == 'OnAd' or func == 'OnVd'):
            self.verbose('PRE-MATCH: Ignoring kill/damage.')
            return False

        # Prevent OnInitgame from being called twice due to server-side initGame doubling
        elif func == 'OnInitgame':
            if not self._igBlockFound:
                self._igBlockFound = True
                self.verbose('Found 1st InitGame from block')
            elif self._logTimerOld <= self._logTimer:
                self.verbose('Found 2nd InitGame from block, ignoring')
                return False

        # ExitLevel means there will be Pre-Match right after the mapload
        elif self._usePreMatchLogic and func == 'OnExitlevel':
            self._preMatch = True
            self.debug('PRE-MATCH ON: found ExitLevel')
            self._elFound = True
            self._igBlockFound = False

        # If we track ShutdownGame events, we could detect sudden server restarts and re-matches
        elif func == 'OnShutdowngame':
            self._sgFound = True
            self._igBlockFound = False

        # Round switch (InitGame after ShutdownGame, but there was no ExitLevel):
        if self._preMatch and not self._elFound and self._igBlockFound and self._sgFound and self._logTimerOld <= self._logTimer:
            self.preMatch = False
            self.debug('PRE-MATCH OFF: found a round change.')
            self._igBlockFound = False
            self._sgFound = False

        # Timer reset
        elif self._logTimerOld > self._logTimer:
            self.debug('Old timer: %s / New timer: %s' % (self._logTimerOld, self._logTimer))
            if self._usePreMatchLogic:
                self._preMatch = True
                self.debug('PRE-MATCH ON: Server crash/restart detected.')
            else:
                self.debug('Server crash/restart detected.')
            self._elFound = False
            self._igBlockFound = False
            self._sgFound = False

            # Payload
            self.write('setadmindvar g_logsync %s' % self._logSync)
            self.write('setadmindvar g_logTimeStampInSeconds 0')

        # Initgame after ExitLevel
        else:
            self._elFound = False
            self._sgFound = False

        #self.debug("-==== FUNC!!: " + func)

        if hasattr(self, func):
            func = getattr(self, func)
            event = func(action, data, match)

            if event:
                self.queueEvent(event)
        elif action in self._eventMap:
            self.queueEvent(b3.events.Event(
                    self._eventMap[action],
                    data,
                    client,
                    target
                ))

        # Addition for cod7 actionMapping
        elif action in self._actionMap:
            self.translateAction(action, data, match)

        else:
            self.queueEvent(b3.events.Event(
                    b3.events.EVT_UNKNOWN,
                    str(action) + ': ' + str(data),
                    client,
                    target
                ))

    def OnJ(self, action, data, match=None):
        """Client join"""

        codguid = match.group('guid')
        cid = match.group('cid')
        name = match.group('name')

        if codguid == '0' and cid == '0' and name == '[3arc]democlient':
            self.verbose('Authentication not required for [3arc]democlient. Aborting Join.')
            self._preMatch = 0
            return None
        
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


###################################################################
# ALTER THE WAY parser.py work for game logs starting with http://
###################################################################

from b3.parser import Parser

# backup original loadArbPlugins
originalLoadArbPlugins = Parser.loadArbPlugins

def newLoadArbPlugins(self):
    """Call original loadArbPlugin method from the Parser class
    then unload the httpytail plugin
    then load the cod7http plugin instead"""
    print "running newLoadArbPlugins "
    
    ## first, run usual loadArbPlugins
    originalLoadArbPlugins(self)
    
    if self.config.has_option('server','game_log') \
        and self.config.get('server','game_log')[0:7] == 'http://' :
        
        # undo httpytail load
        self._pluginOrder.remove('httpytail')
        del self._plugins['httpytail']

        # load cod7http        
        p = 'cod7http'
        self.bot('Loading %s', p)
        try:
            pluginModule = self.pluginImport(p)
            self._plugins[p] = getattr(pluginModule, '%sPlugin' % p.title()) (self)
            self._pluginOrder.append(p)
            version = getattr(pluginModule, '__version__', 'Unknown Version')
            author  = getattr(pluginModule, '__author__', 'Unknown Author')
            self.bot('Plugin %s (%s - %s) loaded', p, version, author)
            self.screen.write('.')
            self.screen.flush()
        except Exception, msg:
            self.critical('Error loading plugin: %s', msg)
            raise SystemExit('error while loading %s' % p)

# make newLoadArbPlugins the default
Parser.loadArbPlugins = newLoadArbPlugins