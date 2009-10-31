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


__author__  = 'ThorN, xlr8or'
__version__ = '1.1.5'

import b3.parsers.cod2
import b3.parsers.q3a
import b3.functions
import re
from b3 import functions

class Cod4Parser(b3.parsers.cod2.Cod2Parser):
    gameName = 'cod4'
    #_reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[a-z0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)


    def getClient(self, match=None, attacker=None, victim=None):
        """Get a client object using the best availible data.
        Prefer GUID first, then Client ID (CID)
        """
        if attacker:
            keys = ['aguid', 'acid']
        else:
            keys = ['guid', 'cid']

        methods = [self.clients.getByGUID, self.clients.getByCID]

        match = attacker or victim or match

        for k, m in zip(keys, methods):
            client = m(match.group(k))
            if client:
                return client

    # join
    def OnJ(self, action, data, match=None):
        # COD4 stores the PBID in the log file
        codguid = match.group('guid')
        cid = match.group('cid')
        pbid = ''

        client = self.getClient(match)

        if client:
            # update existing client
            client.state = b3.STATE_ALIVE
            # possible name changed
            client.name = match.group('name')
        else:
            # make a new client
            if self.PunkBuster:
                guid = codguid
                pbid = codguid
            else:
                guid = codguid

            sp = self.connectClient(cid)
            if sp and self.PunkBuster:
                if not sp['pbid']:
                    self.debug('PunkBuster is enabled in b3.xml, yet I cannot retrieve the PunkBuster Guid. Are you sure PB is enabled?')
                #self.debug('sp: %s' % sp)
                if len(guid) < 32:
                    guid = sp['guid']
                if len(pbid) < 32:
                    pbid = sp['pbid']
                ip = sp['ip']
            elif sp:
                if not codguid:
                    self.error('No CodGuid and no PunkBuster... cannot continue!')
                    return None
                else:
                    if len(guid) < 32:
                        guid = sp['guid']
                    ip = sp['ip']
            else:
                ip = ''

            if len(guid) < 32:
                # break it of, we can't get a valid 32 character guid, attempt to join on a future event.
                self.debug('Ignoring Client! guid: %s (%s), ip: %s' %(guid, len(guid), ip) )
                return None
            else:
                self.debug('guid: %s (%s), ip: %s' %(guid, len(guid), ip) )
            
            client = self.clients.newClient(match.group('cid'), name=match.group('name'), ip=ip, state=b3.STATE_ALIVE, guid=guid, pbid=pbid)

        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)

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

        if match.group('acid') == '-1':
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and \
             attacker.team and \
             victim.team and \
             attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

    def sync(self):
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
