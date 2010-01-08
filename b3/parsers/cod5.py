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
#
# 2/27/2009 - 1.0.1 - xlr8or
#  Added connection counter to prevent infinite newPlayer() loop.
#  Changed check on length of guid.
#  Break off authentication if no codguid and no PB is available to prevent error flooding
# 3/3/2009 - 1.0.2 - xlr8or
#  Fixed typo causing Exception in newPlayer()
# 19/5/2009 - 1.0.3 - xlr8or
#  Changed authentication queue to remove an Exception raised when the Key was no longer available
# 31/10/2009 - 1.0.4 - xlr8or
#  Fixed suicides
# 6/1/2010 - 1.0.5 - xlr8or
#  Fixed unassigned pbid bug for non-pb servers

__author__  = 'xlr8or'
__version__ = '1.0.5'

import b3.parsers.cod2
import b3.parsers.q3a
import b3.functions
import re, threading

class Cod5Parser(b3.parsers.cod2.Cod2Parser):
    gameName = 'cod5'
    _counter = {}

    # join
    def OnJ(self, action, data, match=None):
        codguid = match.group('guid')
        cid = match.group('cid')
        name = match.group('name')
        
        if len(codguid) < 9: # not sure what the min length of the guid is, seen 9 and 10 nr guids
            # invalid guid
            codguid = None

        client = self.getClient(match)

        if client:
            # update existing client
            client.state = b3.STATE_ALIVE
            # possible name changed
            client.name = match.group('name')
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

        # COD5 first version doesn't report the team on kill, only use it if it's set
        # Hopefully the team has been set on another event
        if match.group('ateam'):
            attacker.team = self.getTeam(match.group('ateam'))

        if match.group('team'):
            victim.team = self.getTeam(match.group('team'))

        attacker.name = match.group('aname')
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_KILL
        
        if attacker.cid == victim.cid or attacker.cid == '-1':
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and \
             attacker.team and \
             victim.team and \
             attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

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
            guid = sp['pbid']
            pbid = guid # save pbid in both fields to be consistent with other pb enabled databases
            ip = sp['ip']
            self._counter.pop(cid)
        # PunkBuster is not enabled, using codguid
        elif sp:
            if not codguid:
                self.error('No CodGuid and no PunkBuster... cannot continue!')
                return None
            else:
                guid = codguid
                pbid = None
                ip = sp['ip']
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
