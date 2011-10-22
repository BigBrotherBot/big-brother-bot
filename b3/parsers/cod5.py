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
# 9/1/2010 - 1.0.6 - xlr8or
#  Moved sync to a thread 30 secs after InitGame
# 17/1/2010 - 1.0.7 - xlr8or
#  Moved OnInitgame and OnExitlevel to codparser!
# 25/1/2010 - 1.2.0 - xlr8or - refactored cod parser series
# 1/5/2010 - 1.2.1 - xlr8or - delegate guid length checking to cod parser
# 24/10/2010 - 1.3 - xlr8or 
#  ActionMapping added
#  Add JoinTeam event processing
# 14/11/2010 - 1.3.1 - xlr8or 
#  fix bug in onJT() and translateAction()
# 9/7/2011 - 1.3.2 - 82ndab.Bravo17
#  Add fuzzy guid search in sync() from COD4 series

__author__  = 'xlr8or'
__version__ = '1.3.2'

import b3.parsers.cod2
import b3.functions
import re
import threading
import string
from b3 import functions

class Cod5Parser(b3.parsers.cod2.Cod2Parser):
    gameName = 'cod5'
    IpsOnly = False
    _guidLength = 9

    """\
    Next actions need translation to the EVT_CLIENT_ACTION (Treyarch has a different approach on actions)
    While IW put all EVT_CLIENT_ACTION in the A; action, Treyarch creates a different action for each EVT_CLIENT_ACTION.
    """
    _actionMap = (
        'ad', # Actor Damage (dogs)
        'vd', # Vehicle Damage
        'bd', # Bomb Defused
        'bp', # Bomb Planted
        'fc', # Flag Captured
        'fr', # Flag Returned
        'ft', # Flag Taken
        'rc', # Radio Captured
        'rd'  # Radio Destroyed
    )

    def parseLine(self, line):           
        m = self.getLineParts(line)
        if not m:
            return False

        match, action, data, client, target = m

        func = 'On%s' % string.capwords(action).replace(' ','')
        
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

        # Addition for cod5 actionMapping
        elif action in self._actionMap:
            self.translateAction(action, data, match)

        else:
            self.queueEvent(b3.events.Event(
                    b3.events.EVT_UNKNOWN,
                    str(action) + ': ' + str(data),
                    client,
                    target
                ))

    def translateAction(self, action, data, match=None):
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            client = self.getClient(match)
            if not client:
                return None
        self.debug('Queueing Action (translated) for %s: %s' % (client.name, action) )
        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_ACTION, action, client))

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
             attacker.team == victim.team and \
             match.group('aweap') != 'briefcase_bomb_mp':
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

    # join team
    def OnJt(self, action, data, match=None):
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            client = self.getClient(match)
            if not client:
                return None
        client.team = self.getTeam(match.group('team'))
        
    # sync
    def sync(self):
        self.debug('Synchronising Clients')
        plist = self.getPlayerList(maxRetries=4)
        mlist = {}

        for cid, c in plist.iteritems():
            cid = str(cid)
            client = self.clients.getByCID(cid)
            if client:
                if client.guid and c.has_key('guid') and not self.IpsOnly:
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
