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
#

__author__  = 'Freelander, Courgette'
__version__ = '1.0.2'

import re, threading
import b3.parsers.cod7_rcon as rcon
import b3.parsers.cod5

class Cod7Parser(b3.parsers.cod5.Cod5Parser):
    gameName = 'cod7'
    IpsOnly = False
    _guidLength = 6
    OutputClass = rcon.Cod7Rcon

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
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[a-z0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9-]+)\s+(?P<rate>[0-9]+)$', re.I)

    def startup(self):
        # add the world client
        client = self.clients.newClient(-1, guid='WORLD', name='World', hide=True, pbid='WORLD')

        if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
            # test if PunkBuster is active
            result = self.write('PB_SV_Ver')
            if result != '':
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
        self.write('g_logsync %s' %self._logSync)

        self.setVersionExceptions()
        self.debug('Parser started.')

    # join
    def OnJ(self, action, data, match=None):
        codguid = match.group('guid')
        cid = match.group('cid')
        name = match.group('name')

        if codguid == '0' and cid == '0' and name == '[3arc]democlient':
            self.verbose('Authentication not required for [3arc]democlient. Aborting Join.')
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

        # Force g_logsync again as it may lost during a server crash/restart
        self.debug('Forcing server cvar g_logsync to %s' % self._logSync)
        self.write('g_logsync %s' %self._logSync)

        #Sync clients 30 sec after InitGame
        t = threading.Timer(30, self.clients.sync)
        t.start()
        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)

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