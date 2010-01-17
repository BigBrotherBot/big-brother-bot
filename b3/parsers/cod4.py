# BigBrotherBot(B3) (www.bigbrotherbot.com)
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
# v1.1.2  : xlr8or - Alternate approach on the <32 character guid issue
# v1.1.3  : xlr8or - Improved approach for non PB servers
#         : Tighter regexp for playernames. _reColor strips ascii <33, 47 and >127
#           This includes spaces and also the / is removed. 
# v1.1.4  : xlr8or - Removed bug for non PB servers
# v1.1.5  : Bakes - Improved suicide code, now works with weapon suicides, not falling.
# v1.1.6  : xlr8or - Minor bugfix regarding unassigned pbid on non pb servers.
# v1.2.0  : xlr8or - Big CoD4 MakeOver 
# 17/1/2010 - 1.2.1 - xlr8or
#  Moved OnInitgame and OnExitlevel to codparser!

__author__  = 'ThorN, xlr8or'
__version__ = '1.2.1'

import b3.parsers.cod2
import b3.parsers.q3a
import b3.functions
import re, threading
from b3 import functions

class Cod4Parser(b3.parsers.cod2.Cod2Parser):
    gameName = 'cod4'
    _counter = {}

    #num score ping guid                             name            lastmsg address               qport rate
    #--- ----- ---- -------------------------------- --------------- ------- --------------------- ----- -----
    #  4     0   23 blablablabfa218d4be29e7168c637be ^1XLR^78^9or[^7^7               0 135.94.165.296:63564  25313 25000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[a-z0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9-]+)\s+(?P<rate>[0-9]+)$', re.I)


    # join
    def OnJ(self, action, data, match=None):
        # COD4 stores the PBID in the log file
        codguid = match.group('guid')
        cid = match.group('cid')
        name = match.group('name')

        client = self.getClient(match)
        if client:
            self.verbose2('ClientObject already exists')
            # update existing client
            client.state = b3.STATE_ALIVE
            # possible name changed
            client.name = name
            # Join-event for mapcount reasons and so forth
            return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)
        else:
            self._counter[cid] = 1
            t = threading.Timer(2, self.newPlayer, (cid, codguid, name))
            t.start()
            self.debug('%s connected, waiting for Authentication...' %name)
            self.debug('Our Authentication queue: %s' % self._counter)

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

    # kill
    def OnK(self, action, data, match=None):
        victim = self.getClient(victim=match)
        if not victim:
            self.debug('No victim %s' % match.groupdict())
            self.OnJ(action, data, match)
            return None

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.debug('No attacker %s' % match.groupdict())
            return None

        # COD4 doesn't report the team on kill, only use it if it's set
        # Hopefully the team has been set on another event
        if match.group('ateam'):
            attacker.team = self.getTeam(match.group('ateam'))

        if match.group('team'):
            victim.team = self.getTeam(match.group('team'))

        attacker.name = match.group('aname')
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_KILL
        
        if attacker.cid == victim.cid or attacker.cid == '-1':
            self.verbose2('Suicide Detected')
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and \
             attacker.team and \
             victim.team and \
             attacker.team == victim.team:
            self.verbose2('Teamkill Detected')
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

    def sync(self):
        self.debug('Synchronising Clients')
        plist = self.getPlayerList()
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                if client.guid and c.has_key('guid'):
                    if functions.fuzzyGuidMatch(client.guid, c['guid']):
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
        players = self.getPlayerList()
        self.verbose('authorizeClients() = %s' % players)

        for cid, p in players.iteritems():
            if self.PunkBuster:
                # Use guid since we already get the guid in the log file
                sp = self.clients.getByGUID(p['guid'])

                # Don't use invalid guid/pbid
                if len(p['guid']) < 32:
                    del p['guid']

                if len(p['pbid']) < 32:
                    del p['pbid']
            else:
                sp = self.clients.getByCID(cid)

            if sp:
                # Only set provided data, otherwise use the currently set data
                sp.ip   = p.get('ip', sp.ip)
                sp.pbid = p.get('pbid', sp.pbid)
                sp.guid = p.get('guid', sp.guid)
                sp.data = p
                sp.auth()


    def connectClient(self, ccid):
        if self.PunkBuster:
            self.debug('Getting the (PunkBuster) Playerlist')
        else:
            self.debug('Getting the (status) Playerlist')
        players = self.getPlayerList()
        self.verbose('connectClient() = %s' % players)

        for cid, p in players.iteritems():
            #self.debug('cid: %s, ccid: %s, p: %s' %(cid, ccid, p))
            if int(cid) == int(ccid):
                self.debug('Client found in status/playerList')
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
        # Seems there is no difference in guids if we either do or don't use PunkBuster
        if sp:
            if not codguid:
                self.error('No Guid... cannot continue!')
                return None
            guid = codguid
            pbid = codguid
            if len(guid) < 32:
                guid = sp['guid']
            if len(pbid) < 32:
                pbid = sp['pbid']
            ip = sp['ip']
            #self.debug('sp: %s' % sp)
            self._counter.pop(cid)
        elif self._counter[cid] > 10:
            self.debug('Couldn\'t Auth %s, giving up...' % name)
            self._counter.pop(cid)
            return None
        # Player is not in the status response (yet), retry
        else:
            self.debug('%s not yet fully connected, retrying...#:%s' %(name, self._counter[cid]))
            self._counter[cid] +=1
            t = threading.Timer(4, self.newPlayer, (cid, codguid, name))
            t.start()
            return None
            
        client = self.clients.newClient(cid, name=name, ip=ip, state=b3.STATE_ALIVE, guid=guid, pbid=pbid, data={ 'codguid' : codguid })
        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)
