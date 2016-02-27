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
# 27/02/2009 - 1.0.1 - xlr8or         - added connection counter to prevent infinite new_player() loop
#                                     - changed check on length of guid
#                                     - break off authentication if no codguid and no PB is available to prevent
#                                       error flooding
# 03/03/2009 - 1.0.2 - xlr8or         - fixed typo causing Exception in new_player()
# 19/05/2009 - 1.0.3 - xlr8or         - changed authentication queue to remove an Exception raised when the Key was
#                                       no longer available
# 31/10/2009 - 1.0.4 - xlr8or         - fixed suicides
# 06/01/2010 - 1.0.5 - xlr8or         - fixed unassigned pbid bug for non-pb servers
# 09/01/2010 - 1.0.6 - xlr8or         - moved sync to a thread 30 secs after InitGame
# 17/01/2010 - 1.0.7 - xlr8or         - moved on_initgame and OnExitlevel to codparser!
# 25/01/2010 - 1.2.0 - xlr8or         - refactored cod parser series
# 01/05/2010 - 1.2.1 - xlr8or         - delegate guid length checking to cod parser
# 24/10/2010 - 1.3   - xlr8or         - action mapping added
#                                     - add JoinTeam event processing
# 14/11/2010 - 1.3.1 - xlr8or         - fix bug in onJT() and translate_action()
# 09/07/2011 - 1.3.2 - 82ndab.Bravo17 - add fuzzy guid search in sync() from COD4 series
# 10/03/2013 - 1.3.3 - 82ndab.Bravo17 - llow kicking by full name, even if not authed by B3
# 30/07/2014 - 1.3.4 - Fenix          - fixes for the new getWrap implementation
# 29/08/2014 - 1.3.5 - 82ndab.Bravo17 - reduce min guid length to 8
# 04/08/2014 - 1.4   - Fenix          - syntax cleanup
# 15/10/2014 - 1.4.1 - 82ndab.Bravo17 - allow minimum guid length to be set in b3 xml, guid_length in b3 section
# 19/03/2015 - 1.4.2 - Fenix          - removed unused import statemnet (from b3 import functions)
#                                     - removed deprecated usage of dict.has_key (us 'in dict' instead)

__author__ = 'xlr8or'
__version__ = '1.4.2'

import b3.functions
import b3.parsers.cod2
import string

from b3.events import Event

class Cod5Parser(b3.parsers.cod2.Cod2Parser):

    gameName = 'cod5'
    IpsOnly = False

    _guidLength = 8
    
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

    # Next actions need translation to the EVT_CLIENT_ACTION (Treyarch has a
    # different approach on actions). While IW put all EVT_CLIENT_ACTION in the A;
    # action, Treyarch creates a different action for each EVT_CLIENT_ACTION.

    _actionMap = (
        'ad',  # Actor Damage (dogs)
        'vd',  # Vehicle Damage
        'bd',  # Bomb Defused
        'bp',  # Bomb Planted
        'fc',  # Flag Captured
        'fr',  # Flag Returned
        'ft',  # Flag Taken
        'rc',  # Radio Captured
        'rd'   # Radio Destroyed
    )

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def pluginsStarted(self):
        """
        Called after the parser loaded and started all plugins.
        """
        self.patch_b3_admin_plugin()
        self.debug('Admin plugin has been patched')

        if self.config.has_option('b3', 'guid_length'):
            self._guidLength = self.config.getint('b3', 'guid_length')
            self.info('Min guid length has been set to %s', self._guidLength)

    
    ####################################################################################################################
    #                                                                                                                  #
    #   PARSING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def parse_line(self, line):
        """
        Parse a log line creating necessary events.
        :param line: The log line to be parsed
        """
        m = self.getLineParts(line)
        if not m:
            return False

        match, action, data, client, target = m
        func = 'On%s' % string.capwords(action).replace(' ','')
        
        if hasattr(self, func):
            func = getattr(self, func)
            event = func(action, data, match)
            if event:
                self.queueEvent(event)
        elif action in self._eventMap:
            self.queueEvent(self.getEvent(self._eventMap[action], data=data, client=client, target=target))
        elif action in self._actionMap:
            # addition for cod5 actionMapping
            self.translateAction(action, data, match)
        else:
            self.queueEvent(self.getEvent('EVT_UNKNOWN', str(action) + ': ' + str(data), client, target))

    def translateAction(self, action, data, match=None):
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            client = self.getClient(match)
            if not client:
                return None
        self.debug('Queueing action (translated) for %s: %s' % (client.name, action) )
        self.queueEvent(self.getEvent('EVT_CLIENT_ACTION', data=action, client=client))

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

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

        event_key = 'EVT_CLIENT_KILL'
        if attacker.cid == victim.cid or attacker.cid == '-1':
            event_key = 'EVT_CLIENT_SUICIDE'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team and \
                victim.team and attacker.team == victim.team and \
                match.group('aweap') != 'briefcase_bomb_mp':
            event_key = 'EVT_CLIENT_KILL_TEAM'

        victim.state = b3.STATE_DEAD
        data = (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype'))
        return self.getEvent(event_key, data=data, client=attacker, target=victim)

    def OnJt(self, action, data, match=None):
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            client = self.getClient(match)
            if not client:
                return None
        client.team = self.getTeam(match.group('team'))
        
    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def sync(self):
        """
        For all connected players returned by self.get_player_list(), get the matching Client
        object from self.clients (with self.clients.get_by_cid(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        """
        self.debug('Synchronizing clients')
        plist = self.getPlayerList(maxRetries=4)
        mlist = {}

        for cid, c in plist.iteritems():
            cid = str(cid)
            client = self.clients.getByCID(cid)
            if client:
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
        
        return mlist