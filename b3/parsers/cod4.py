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
# 22/1/2012 - 1.3.5 -82ndab-Bravo17
#    * Add JT method for some COD4 mods
# 7/3/2012 - 1.3.6 - 82ndab-Bravo17
#    * Change Client Auth method so it updates empty pbids
# 2012/11/18 - 1.3.7 - Courgette
#    * fix: player not authenticated (without punkbuster) when qport or port is a negative number
# 2013/01/02 - 1.3.8 - Courgette
#    * improve parsing rcon status status responses that are missing characters
# 2013/01/12 - 1.3.9 - Courgette
#    * fix bug when cod4ClientAuthMethod handles an unexpected error
# 2013/05/10 - 1.4.0 - 82ndab.Bravo17
#    * Allow kicking by full name, even if not authed by B3
#

__author__  = 'ThorN, xlr8or'
__version__ = '1.4.0'

import b3.parsers.cod2
import b3.functions
import re
from b3 import functions


class Cod4Parser(b3.parsers.cod2.Cod2Parser):
    gameName = 'cod4'
    IpsOnly = False
    _guidLength = 32
    
    _commands = {}
    _commands['message'] = 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'
    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'banclient %(cid)s'
    _commands['unban'] = 'unbanuser %(name)s' # remove players from game engine's ban.txt
    _commands['tempban'] = 'clientkick %(cid)s'
    _commands['kickbyfullname'] = 'kick %(cid)s'

    #num score ping guid                             name            lastmsg address               qport rate
    #--- ----- ---- -------------------------------- --------------- ------- --------------------- ----- -----
    #  0     0   14 1aaaaaaaaaaaaaaaaaaaaaaaaaaaaaab player1^7               0 11.22.33.44:-6187 -1609 25000
    #  1     0   12 1ccccccccccccccccccccccccccccccc player2^7               0 22.33.44.55:-10803-23569 25000
    #  3   486  185 ecc77e3400a38cc71b3849207e20e1b0 GO_NINJA^7              0 111.222.111.111:-15535-2655 25000
    #  4     0   23 blablablabfa218d4be29e7168c637be ^1XLR^78^9or[^7^7               0 135.94.165.296:63564  25313 25000
    #  5    92  509 0123456789abcdef0123456789abcdef 7ajimaki^7            100 11.222.111.44:28960   -27329 25000
    #  6     0  206 0123456789a654654646545789abcdef [NRNS]ArmedGuy^7        0 11.22.111.44:28960    -21813 25000
    #  7    30  229 012343213211313213321313131bcdef Franco^7                0 111.22.111.111:23144  22922 25000
    _regPlayer = re.compile(r"""
^\s*
  (?P<slot>[0-9]+)
\s+
  (?P<score>[0-9-]+)
\s+
  (?P<ping>[0-9]+)
\s+
  (?P<guid>[0-9a-f]+)
\s+
  (?P<name>.*?)
\s+
  (?P<last>[0-9]+?)
\s*
  (?P<ip>(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9]))
:?
  (?P<port>-?[0-9]{1,5})
\s*
  (?P<qport>-?[0-9]{1,5})
\s+
  (?P<rate>[0-9]+)
$
""", re.IGNORECASE | re.VERBOSE)

    def __new__(cls, *args, **kwargs):
        patch_b3_clients()
        return b3.parsers.cod2.Cod2Parser.__new__(cls)

    def pluginsStarted(self):
        self.patch_b3_admin_plugin()
        self.debug('Admin Plugin has been patched.')

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


def patch_b3_clients():
    #############################################################
    # Below is the code that change a bit the b3.clients.Client
    # class at runtime. What the point of coding in python if we
    # cannot play with its dynamic nature ;)
    #
    # why ?
    # because doing so make sure we're not broking any other
    # working and long tested parser. The changes we make here
    # are only applied when the frostbite parser is loaded.
    #############################################################

    def cod4ClientAuthMethod(self):
        if not self.authed and self.guid and not self.authorizing:
            self.authorizing = True

            name = self.name
            ip = self.ip
            pbid = self.pbid
            try:
                inStorage = self.console.storage.getClient(self)
            except KeyError, msg:
                self.console.debug('User not found %s: %s', self.guid, msg)
                inStorage = False
            except Exception, e:
                self.console.error('auth self.console.storage.getClient(client) - %s' % self, exc_info=e)
                self.authorizing = False
                return False

            #lastVisit = None
            if inStorage:
                self.console.bot('Client found in storage %s, welcome back %s', str(self.id), self.name)
                self.lastVisit = self.timeEdit
                if self.pbid == '':
                    self.pbid = pbid
            else:
                self.console.bot('Client not found in the storage %s, create new', str(self.guid))

            self.connections = int(self.connections) + 1
            self.name = name
            self.ip = ip
            self.save()
            self.authed = True

            self.console.debug('Client Authorized: [%s] %s - %s', self.cid, self.name, self.guid)

            # check for bans
            if self.numBans > 0:
                ban = self.lastBan
                if ban:
                    self.reBan(ban)
                    self.authorizing = False
                    return False

            self.refreshLevel()

            self.console.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_AUTH,
                self,
                self))

            self.authorizing = False

            return self.authed
        else:
            return False

    b3.clients.Client.auth = cod4ClientAuthMethod
