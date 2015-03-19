#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
#
#              1.1.2 - xlr8or         - alternate approach on the <32 character guid issue
#              1.1.3 - xlr8or         - improved approach for non PB servers
#                                     - tighter regexp for playernames. _recolor strips ascii <33, 47 and >127
#                                     - this includes spaces and also the / is removed.
#              1.1.4 - xlr8or         - removed bug for non PB servers
#              1.1.5 - Bakes          - improved suicide code, now works with weapon suicides, not falling.
#              1.1.6 - xlr8or         - minor bugfix regarding unassigned pbid on non pb servers.
#              1.2.0 - xlr8or         - big CoD4 MakeOver
#
# 17/01/2010 - 1.2.1 - xlr8or         - moved on_initgame and OnExitlevel to codparser!
# 25/01/2010 - 1.3.0 - xlr8or         - refactored cod parser series
# 27/01/2010 - 1.3.1 - xlr8or         - added authorize_clients() for ipsonly
#                                     - minor bugfix in sync() for ipsonly
# 31/01/2010 - 1.3.2 - xlr8or         - modified unban to remove bans from game's ban list
# 01/05/2010 - 1.3.2 - xlr8or         - delegate guid length checking to cod parser
# 07/11/2010 - 1.3.3 - GrosBedo       - messages now support named $variables instead of %s
# 08/11/2010 - 1.3.4 - GrosBedo       - messages can now be empty (no message broadcasted on kick/tempban/ban/unban)
# 22/01/2012 - 1.3.5 - 82ndab-Bravo17 - add JT method for some COD4 mods
# 07/03/2012 - 1.3.6 - 82ndab-Bravo17 - change Client Auth method so it updates empty pbids
# 18/11/2012 - 1.3.7 - Courgette      - fix: player not authenticated (without punkbuster) when qport or port is a
#                                       negative number
# 02/01/2013 - 1.3.8 - Courgette      - improve parsing rcon status status responses that are missing characters
# 12/01/2013 - 1.3.9 - Courgette      - fix bug when cod4_client_auth_method handles an unexpected error
# 10/05/2013 - 1.4.0 - 82ndab-Bravo17 - allow kicking by full name, even if not authed by B3
# 02/05/2014 - 1.4.1 - Fenix          - rewrote dictionary creation as literal
# 30/07/2014 - 1.4.2 - Fenix          - fixes for the new getWrap implementation
# 03/08/2014 - 1.5   - Fenix          - syntax cleanup
# 19/03/2015 - 1.5.1 - Fenix          - removed unused import statemnet (from b3 import functions)
#                                     - removed deprecated usage of dict.has_key (us 'in dict' instead)

__author__ = 'ThorN, xlr8or'
__version__ = '1.5.1'

import b3.clients
import b3.functions
import b3.parsers.cod2
import re


class Cod4Parser(b3.parsers.cod2.Cod2Parser):

    gameName = 'cod4'
    IpsOnly = False

    _guidLength = 32
    
    _commands = {
        'message': 'tell %(cid)s %(message)s',
        'say': 'say %(message)s',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'clientkick %(cid)s',
        'ban': 'banclient %(cid)s',
        'unban': 'unbanuser %(name)s',
        'tempban': 'clientkick %(cid)s',
        'kickbyfullname': 'kick %(cid)s'
    }

    # num score ping guid                             name            lastmsg address               qport rate
    # --- ----- ---- -------------------------------- --------------- ------- --------------------- ----- -----
    #   0     0   14 1aaaaaaaaaaaaaaaaaaaaaaaaaaaaaab player1^7             0 11.22.33.44:-6187     -1609 25000
    #   1     0   12 1ccccccccccccccccccccccccccccccc player2^7             0 22.33.44.55:-10803   -23569 25000
    #   3   486  185 ecc77e3400a38cc71b3849207e20e1b0 GO_NINJA^7            0 111.222.111.111:-15535-2655 25000
    #   4     0   23 blablablabfa218d4be29e7168c637be ^1XLR^78^9or[^7       0 135.94.165.296:63564  25313 25000
    #   5    92  509 0123456789abcdef0123456789abcdef 7ajimaki^7          100 11.222.111.44:28960  -27329 25000
    #   6     0  206 0123456789a654654646545789abcdef [NRNS]ArmedGuy^7      0 11.22.111.44:28960   -21813 25000
    #   7    30  229 012343213211313213321313131bcdef Franco^7              0 111.22.111.111:23144  22922 25000
    _regPlayer = re.compile(r'^\s*(?P<slot>[0-9]+)\s+'
                            r'(?P<score>[0-9-]+)\s+'
                            r'(?P<ping>[0-9]+)\s+'
                            r'(?P<guid>[0-9a-f]+)\s+'
                            r'(?P<name>.*?)\s+'
                            r'(?P<last>[0-9]+?)\s*'
                            r'(?P<ip>(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}'
                            r'(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])):?'
                            r'(?P<port>-?[0-9]{1,5})\s*'
                            r'(?P<qport>-?[0-9]{1,5})\s+'
                            r'(?P<rate>[0-9]+)$', re.IGNORECASE | re.VERBOSE)

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def __new__(cls, *args, **kwargs):
        patch_b3_clients()
        return b3.parsers.cod2.Cod2Parser.__new__(cls)

    def pluginsStarted(self):
        """
        Called after the parser loaded and started all plugins.
        """
        self.patch_b3_admin_plugin()
        self.debug('Admin plugin has been patched')

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

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

        eventkey = 'EVT_CLIENT_KILL'
        if attacker.cid == victim.cid or attacker.cid == '-1':
            self.verbose2('Suicide detected')
            eventkey = 'EVT_CLIENT_SUICIDE'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team and \
                victim.team and attacker.team == victim.team and \
                match.group('aweap') != 'briefcase_bomb_mp':
            self.verbose2('Teamkill detected')
            eventkey = 'EVT_CLIENT_KILL_TEAM'

        victim.state = b3.STATE_DEAD
        data = (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype'))
        return self.getEvent(eventkey, data=data, client=attacker, target=victim)

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a client.
        :param client: The client to unban
        :param reason: The reason for the unban
        :param admin: The admin who unbanned this client
        :param silent: Whether or not to announce this unban
        """
        if self.PunkBuster:
            if client.pbid:
                result = self.PunkBuster.unBanGUID(client)

                if result:                    
                    admin.message('^3Unbanned^7: %s^7: %s' % (client.exactName, result))

                if admin:
                    variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
                    fullreason = self.getMessage('unbanned_by', variables)
                else:
                    variables = self.getMessageVariables(client=client, reason=reason)
                    fullreason = self.getMessage('unbanned', variables)

                if not silent and fullreason != '':
                    self.say(fullreason)

            elif admin:
                admin.message('%s ^7unbanned but has no punkbuster id' % client.exactName)
        else:
            name = self.stripColors(client.exactName[:15])
            result = self.write(self.getCommand('unban', name=name, reason=reason))
            if admin:
                admin.message(result)

    def sync(self):
        """
        For all connected players returned by self.get_player_list(), get the matching Client
        object from self.clients (with self.clients.get_by_cid(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        """
        self.debug('Synchronizing clients')
        plist = self.getPlayerList(maxRetries=4)
        self.verbose2('plist: %s' % plist)
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                self.verbose2('client found: %s' % client.name)
                if client.guid and 'guid' in c and not self.IpsOnly:
                    if b3.functions.fuzzyGuidMatch(client.guid, c['guid']):
                        # player matches
                        self.debug('in-sync %s == %s', client.guid, c['guid'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.guid, c['guid'])
                        client.disconnect()
                elif client.ip and 'ip' in c:
                    if client.ip == c['ip']:
                        # player matches
                        self.debug('in-sync %s == %s', client.ip, c['ip'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.ip, c['ip'])
                        client.disconnect()
                else:
                    self.debug('no-sync: no guid or ip found')
            else:
                self.verbose2('no client found for cid: %s' % cid)
        
        return mlist

    def authorizeClients(self):
        """
        For all connected players, fill the client object with properties allowing to find
        the user in the database (usualy guid, or punkbuster id, ip) and call the
        Client.auth() method.
        """
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

########################################################################################################################
##                                                                                                                    ##
##  APPLY SPECIFIC PARSER PATCHES TO B3 CORE MODULES                                                                  ##
##                                                                                                                    ##
########################################################################################################################

def patch_b3_clients():

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
                self.console.error('Auth self.console.storage.getClient(client) - %s' % self, exc_info=e)
                self.authorizing = False
                return False

            #lastVisit = None
            if inStorage:
                self.console.bot('Client found in storage %s: welcome back %s', str(self.id), self.name)
                self.lastVisit = self.timeEdit
                if self.pbid == '':
                    self.pbid = pbid
            else:
                self.console.bot('Client not found in the storage %s: create new', str(self.guid))

            self.connections = int(self.connections) + 1
            self.name = name
            self.ip = ip
            self.save()
            self.authed = True

            self.console.debug('Client authorized: [%s] %s - %s', self.cid, self.name, self.guid)

            # check for bans
            if self.numBans > 0:
                ban = self.lastBan
                if ban:
                    self.reBan(ban)
                    self.authorizing = False
                    return False

            self.refreshLevel()
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_AUTH', data=self, client=self))
            self.authorizing = False
            return self.authed
        else:
            return False

    b3.clients.Client.auth = cod4ClientAuthMethod