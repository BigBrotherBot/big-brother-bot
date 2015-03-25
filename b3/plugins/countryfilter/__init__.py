#
# CountryFilter Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 www.xlr8or.com <xlr8or@bigbrotherbot.net>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
#
# 08/11/2009 - 1.1.6  - Courgette - now uses PurePythonGeoIP bundled in b3.lib
#                                 - reading config, makes use of getpath whenever applicable (allow to use @b3 and @conf)
# 20/06/2010 - 1.1.7  - xlr8or    - added client's maxlevel for filtering
# 22/06/2010 - 1.1.8b - xlr8or    - added some debug info
# 30/06/2010 - 1.1.8  - xlr8or    - tested
# 29/07/2010 - 1.2.0  - xlr8or    - added support for BF:BC2 (PB enabled servers only!)
# 30/10/2010 - 1.2.1  - xlr8or    - added support for MOH (PB enabled servers only!)
# 09/11/2010 - 1.3    - Courgette - added support for BF3 (PB enabled servers only!)
# 04/12/2014 - 1.4    - xlr8or    - moved maxlevel setting to 'settings section'
#                                 - added ip blocking function and section in config file
#                                 - fixed and re-ordered config file.
# 04/12/2014 - 1.4.1  - xlr8or    - removed faulty semicolon
# 05/12/2014 - 1.5    - xlr8or    - added player check on plugin start
#                                 - added bf4
#                                 - PEP 8 changes
# 25/03/2015 - 1.6    - Fenix     - make plugin dependent from geolocation plugin
#                                 - changes for built-in release
#                                 - removed redundancy with location plugin
#                                 - stop processing events after applying kick penalty
#                                 - added cf_announce_accept, cf_announce_reject configuration values

__version__ = '1.6'
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
        'cf_allow_message': '^^7$name ^2(country: $country)^7 is accepted by B3.',
        'cf_deny_message': '^7%(name)s ^1(Country: %(country)s)^7 was rejected by B3.'
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
        try:
            self.cf_announce_accept = self.config.getboolean('settings', 'cf_announce_accept')
        except:
            pass

        self.debug('setting/cf_announce_accept: %s' % self.cf_announce_accept)

        try:
            self.cf_announce_reject = self.config.getboolean('settings', 'cf_announce_reject')
        except:
            pass

        self.debug('setting/cf_announce_reject: %s' % self.cf_announce_reject)

        try:
            self.cf_message_exclude_from = self.config.get('settings', 'cf_message_exclude_from')
        except:
            pass

        self.debug('setting/cf_message_exclude_from: %s' % self.cf_message_exclude_from)

        try:
            self.cf_order = self.config.get('settings', 'cf_order')
        except:
            pass

        self.debug('setting/cf_order: %s' % self.cf_order)

        try:
            self.cf_deny_from = self.config.get('settings', 'cf_deny_from')
        except:
            pass

        self.debug('setting/cf_deny_from: %s' % self.cf_deny_from)

        try:
            self.cf_allow_from = self.config.get('settings', 'cf_allow_from')
        except:
            pass

        self.debug('setting/cf_allow_from: %s' % self.cf_allow_from)

        try:
            self.maxLevel = self.config.getint('settings', 'maxlevel')
        except:
            pass

        self.debug('setting/maxlevel: %s' % self.maxLevel)

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