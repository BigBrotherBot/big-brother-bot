# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

__version__ = '1.7'
__author__ = 'guwashi / xlr8or'

import b3
import b3.events
import b3.plugin


class CountryfilterPlugin(b3.plugin.Plugin):

    requiresPlugins = ['geolocation']

    cf_announce_accept = True
    cf_announce_reject = True
    cf_message_exclude_from = ''
    cf_order = 'deny,allow'
    cf_deny_from = ''
    cf_allow_from = 'all'
    maxLevel = 1
    
    ignore_names = []
    ignore_ips = []
    block_ips = []

    _default_messages = {
        'cf_allow_message': '^7$name ^2(country: $country)^7 is accepted by B3',
        'cf_deny_message': '^7%(name)s ^1(country: %(country)s)^7 was rejected by B3'
    }

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Startup the plugin
        """
        self.registerEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', self.onGeolocationSuccess)
        self.debug('plugin started')

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        # settings section

        self.cf_announce_accept = self.getSetting('settings', 'cf_announce_accept', b3.BOOL, self.cf_announce_accept)
        self.cf_announce_reject = self.getSetting('settings', 'cf_announce_reject', b3.BOOL, self.cf_announce_reject)
        self.cf_message_exclude_from = self.getSetting('settings', 'cf_message_exclude_from', b3.STR, self.cf_message_exclude_from)
        self.cf_order = self.getSetting('settings', 'cf_order', b3.STR, self.cf_order)
        self.cf_deny_from = self.getSetting('settings', 'cf_deny_from', b3.STR, self.cf_deny_from)
        self.cf_allow_from = self.getSetting('settings', 'cf_allow_from', b3.STR, self.cf_allow_from)
        self.maxLevel = self.getSetting('settings', 'maxlevel', b3.LEVEL, self.maxLevel)

        # ignore section
        try:
            # seperate entries on the ,
            _l = self.config.get('ignore', 'names').split(',')
            # strip leading and trailing whitespaces from each list entry
            self.ignore_names = [x.strip() for x in _l]
        except:
            pass

        self.debug('ignored names: %s' % self.ignore_names)

        try:
            _l = self.config.get('ignore', 'ips').split(',')
            self.ignore_ips = [x.strip() for x in _l]
        except:
            pass

        self.debug('ignored ip\'s: %s' % self.ignore_ips)
        self.debug('ignored maxlevel: %s' % self.maxLevel)

        # block section
        try:
            _l = self.config.get('block', 'ips').split(',')
            self.block_ips = [x.strip() for x in _l]
        except:
            pass

        self.debug('blocked ip\'s: %s' % self.block_ips)

    ####################################################################################################################
    #                                                                                                                  #
    #    HANDLE EVENTS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def onGeolocationSuccess(self, event):
        """
        Handle EVT_CLIENT_GEOLOCATION_SUCCESS
        """
        client = event.client
        self.debug('checking player: %s, name: %s, ip: %s, level: %s' % (client.cid, client.name, client.ip, client.maxLevel))
        self.debug('country: %s <%s>' % (client.location.country, client.location.cc))
        if self.isAllowConnect(client.location.cc, client):
            if self.cf_announce_accept and not self.isMessageExcludeFrom(client.location.cc) and client.guid and self.console.upTime() > 300:
                self.console.say(self.getMessage('cf_allow_message', {'name': client.name, 'country': client.location.country}))
        else:
            if self.cf_announce_reject and not self.isMessageExcludeFrom(client.location.cc):
                self.console.say(self.getMessage('cf_deny_message', {'name': client.name, 'country': client.location.country}))
            client.kick(silent=True)
            raise b3.events.VetoEvent
        self.debug('checking done')

    def isAllowConnect(self, cc, client):
        """
        Is player allowed to connect?
        :param cc: The client country code
        :param client: The clienbt to check
        http://httpd.apache.org/docs/mod/mod_access.html
        """
        if client.maxLevel > self.maxLevel:
            self.debug('%s is a higher level user, and allowed to connect' % client.name)
            result = True
        elif client.name in self.ignore_names:
            self.debug('name is on ignorelist, allways allowed to connect')
            result = True
        elif str(client.ip) in self.ignore_ips:
            self.debug('ip address is on ignorelist, allways allowed to connect')
            result = True
        elif str(client.ip) in self.block_ips:
            self.debug('ip address is on blocklist, never allowed to connect')
            result = False
        elif 'allow,deny' == self.cf_order:
            # self.debug('allow,deny - checking')
            result = False  # deny
            if -1 != self.cf_allow_from.find('all'):
                result = True
            if -1 != self.cf_allow_from.find(cc):
                result = True
            if -1 != self.cf_deny_from.find('all'):
                result = False
            if -1 != self.cf_deny_from.find(cc):
                result = False
        else:  # 'deny,allow' (default)
            # self.debug('deny,allow - checking')
            result = True  # allow
            if -1 != self.cf_deny_from.find('all'):
                result = False
            if -1 != self.cf_deny_from.find(cc):
                result = False
            if -1 != self.cf_allow_from.find('all'):
                result = True
            if -1 != self.cf_allow_from.find(cc):
                result = True
        return result

    def isMessageExcludeFrom(self, cc):
        """
        Is message allowed to print?
        :param cc: The country code
        """
        result = False
        if -1 != self.cf_message_exclude_from.find('all'):
            result = True
        if -1 != self.cf_message_exclude_from.find(cc):
            result = True
        return result