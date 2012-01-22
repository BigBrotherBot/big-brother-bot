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
# v1.1.2  : xlr8or - Alternate approach on the <32 character guid issue
# v1.1.3  : xlr8or - Improved approach for non PB servers
#         : Tighter regexp for playernames. _reColor strips ascii <33, 47 and >127
#           This includes spaces and also the / is removed. 
# v1.1.4  : xlr8or - Removed bug for non PB servers
# v1.1.5  : Bakes - Improved suicide code, now works with weapon suicides, not falling.
# v1.1.6  : xlr8or - Minor bugfix regarding unassigned pbid on non pb servers.
# v1.2.0  : xlr8or - Big CoD4 MakeOver 
# 17/1/2010 - 1.2.1 - xlr8or
#  * Moved OnInitgame and OnExitlevel to codparser!
# 25/1/2010 - 1.3.0 - xlr8or - refactored cod parser series
# 27/1/2010 - 1.3.1 - xlr8or
#  * Added authorizeClients() for IpsOnly
#  * Minor bugfix in sync() for IpsOnly
# 31/1/2010 - 1.3.2 - xlr8or
#  * Modified unban to remove bans from game's ban list
# 1/5/2010 - 1.3.2 - xlr8or - delegate guid length checking to cod parser
# 7/11/2010 - 1.3.3 - GrosBedo
#    * messages now support named $variables instead of %s
# 8/11/2010 - 1.3.4 - GrosBedo
#    * messages can now be empty (no message broadcasted on kick/tempban/ban/unban)
# 22/1/2012 - 1.3.5 -92ndab-Bravo17
#    * Add JT method for some COD4 mods



__author__  = 'ThorN, xlr8or'
__version__ = '1.3.5'

import b3.parsers.cod2
import b3.functions
import re, threading
from b3 import functions

class Cod4Parser(b3.parsers.cod2.Cod2Parser):
    gameName = 'cod4'
    IpsOnly = False
    _guidLength = 32

    #num score ping guid                             name            lastmsg address               qport rate
    #--- ----- ---- -------------------------------- --------------- ------- --------------------- ----- -----
    #  4     0   23 blablablabfa218d4be29e7168c637be ^1XLR^78^9or[^7^7               0 135.94.165.296:63564  25313 25000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[a-z0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9-]+)\s+(?P<rate>[0-9]+)$', re.I)


    # join team (Some mods eg OW use JT)
    def OnJt(self, action, data, match=None):
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            client = self.getClient(match)
            if not client:
                return None
        client.team = self.getTeam(match.group('team'))
        self.debug('%s has just changed team to %s' % (client.name, client.team))
        
    
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
             attacker.team == victim.team and \
             match.group('aweap') != 'briefcase_bomb_mp':
            self.verbose2('Teamkill Detected')
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

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
            _name = self.stripColors(client.exactName[:15])
            result = self.write(self.getCommand('unban', name=_name, reason=reason))
            if admin:
                admin.message(result)

    def sync(self):
        self.debug('Synchronising Clients')
        plist = self.getPlayerList(maxRetries=4)
        self.verbose2('plist: %s' % plist)
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                self.verbose2('Client found: %s' % client.name)
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
            else:
                self.verbose2('No client found for cid: %s' % cid)
        
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
                if self.IpsOnly:
                    sp.guid = p.get('ip', sp.guid)
                else:
                    sp.guid = p.get('guid', sp.guid)
                sp.data = p
                sp.auth()
