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
# 9/1/2010 - 1.0.6 - xlr8or
#  Moved sync to a thread 30 secs after InitGame
# 17/1/2010 - 1.0.7 - xlr8or
#  Moved OnInitgame and OnExitlevel to codparser!
# 25/1/2010 - 1.2.0 - xlr8or - refactored cod parser series

__author__  = 'xlr8or'
__version__ = '1.2.0'

import b3.parsers.cod2
import b3.parsers.q3a
import b3.functions
import re, threading

class Cod5Parser(b3.parsers.cod2.Cod2Parser):
    gameName = 'cod5'
    IpsOnly = False

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
