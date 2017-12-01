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

__author__ = 'ThorN'
__version__ = '1.6.1'

import b3
import os
import time
import feedparser
import b3.plugin
import b3.cron

from b3 import B3_RSS
from ConfigParser import NoOptionError


class MessageLoop(object):

    items = None

    def __init__(self):
        self.items = []
        self.index = 0

    def put(self, item):
        """
        Add an element to the list.
        """
        self.items.append(item)

    def getnext(self):
        """
        Get the next item in the list.
        """
        try:
            item = self.items[self.index]
        except IndexError:
            self.index = 0
            return None

        self.index += 1

        if self.index >= len(self.items):
            self.index = 0

        return item

    def getitem(self, index):
        """
        Get a specific element from the list.
        :param index: The element index
        """
        try:
            return self.items[index]
        except IndexError:
            return None

    def remove(self, index):
        """
        Remove an element from the list.
        :param index: The element index
        """
        i = 0
        items = []
        for item in self.items:
            if i != index:
                items.append(item)
            i += 1

        self.items = items

    def clear(self):
        """
        Empty the list
        """
        self.items = []


class AdvPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _xlrstatsPlugin = None
    _cronTab = None
    _msg = None
    _fileName = None
    _rate = '2'
    _feed = B3_RSS
    _feedpre = u'News: '
    _feedmaxitems = 5
    _feeditemnr = 0
    _replay = 0

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize the plugin
        """
        if self._adminPlugin:
            self._adminPlugin.registerCommand(self, 'advadd', 100, self.cmd_advadd)
            self._adminPlugin.registerCommand(self, 'advrate', 100, self.cmd_advrate)
            self._adminPlugin.registerCommand(self, 'advlist', 100, self.cmd_advlist)
            self._adminPlugin.registerCommand(self, 'advload', 100, self.cmd_advload)
            self._adminPlugin.registerCommand(self, 'advrem', 100, self.cmd_advrem)
            if self._fileName:
                self._adminPlugin.registerCommand(self, 'advsave', 100, self.cmd_advsave)

        self._xlrstatsPlugin = self.console.getPlugin('xlrstats')
        if not self._xlrstatsPlugin:
            self.debug('XLRstats not installed: @topstats not available!')
        else:
            self.debug('XLRstats found: @topstats available!')

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        self._adminPlugin = self.console.getPlugin('admin')
        self._msg = MessageLoop()

        try:
            self._rate = self.config.get('settings', 'rate')
            self.debug('loaded settings/rate: %s' % self._rate)
        except NoOptionError:
            self.warning('could not find settings/max_level in config file, using default: 2')

        if self.config.has_option('settings', 'ads'):
            self._fileName = self.console.getAbsolutePath(self.config.get('settings', 'ads'))
            self.load_from_file(self._fileName)
        else:
            self._fileName = None
            self.load_from_config()

        try:
            self._feed = self.config.get('newsfeed', 'url')
        except NoOptionError:
            pass

        try:
            self._feedmaxitems = self.config.getint('newsfeed', 'items')
        except (NoOptionError, ValueError):
            pass

        # reduce feedmaxitems 1 point, since we're starting at item 0, this makes counting easier...
        self._feedmaxitems -= 1
        self.verbose('self._feedmaxitems: %s' % self._feedmaxitems)

        try:
            self._feedpre = self.config.get('newsfeed', 'pretext')
        except NoOptionError:
            pass

        # test if we have a proper feed
        if self._feed is not None:
            if self._feed.strip() == '':
                self._feed = None
            else:
                f = feedparser.parse(self._feed)
                if not f or f['bozo'] == 1:
                    self._feed = None
                    self.warning('error reading feed at %s' % self._feed)
                    self.debug(f['bozo_exception'])

        if self._cronTab:
            # remove existing crontab
            self.console.cron - self._cronTab

        (m, s) = self._get_rate_minsec(self._rate)
        self._cronTab = b3.cron.PluginCronTab(self, self.adv, second=s, minute=m)
        self.console.cron + self._cronTab

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def save(self):
        """
        Save the current advertisements list.
        """
        if self._fileName:
            f = file(self._fileName, 'w')
            for msg in self._msg.items:
                if msg:
                    f.write(msg + "\n")
            f.close()
        else:
            self.verbose('save to XML config not supported')
            raise Exception('save to XML config not supported')

    def load_from_file(self, filename):
        """
        Load advertisements from a file.
        """
        if not os.path.isfile(filename):
            self.error('advertisement file %s does not exist', filename)
            return

        with open(filename, 'r') as f:
            self.load(f.readlines())

    def load_from_config(self):
        """
        Load advertisement from the plugin configuration file.
        """
        items = []
        for e in self.config.get('ads/ad'):
            items.append(e.text)

        self.load(items)

    def load(self, items=None):
        """
        Load an advertisement message.
        """
        if items is None:
            items = []

        self._msg.clear()
        for w in items:
            w = w.strip()
            if len(w) > 1:
                if w[:6] == '/spam#':
                    w = self._adminPlugin.getSpam(w[6:])
                self._msg.put(w)

    def adv(self, first_try=True):
        """
        Display an advertisement message.
        :param first_try: Whether or not it's the first time we try to display this ad
        """
        ad = self._msg.getnext()
        if ad:
            if ad == "@nextmap":
                nextmap = self.console.getNextMap()
                if nextmap:
                    ad = "^2Next map: ^3" + nextmap
                else:
                    self.debug('could not get nextmap')
                    ad = None
            elif ad == "@time":
                ad = "^2Time: ^3" + self.console.formatTime(time.time())
            elif ad[:5] == "@feed" and self._feed:
                ad = self.get_feed(ad)
                if not ad or ad == self._feedpre:
                    # we didn't get an item from the feedreader, move on to the next ad
                    self._replay += 1
                    # prevent endless loop if only feeditems are used as adds
                    if self._replay < 10:
                        self.adv()
                    else:
                        self.debug('something wrong with the newsfeed: disabling it. Fix the feed and do !advload')
                        self._feed = None
                    return
            elif ad == "@topstats":
                if self._xlrstatsPlugin:
                    self._xlrstatsPlugin.cmd_xlrtopstats(data='3', client=None, cmd=None, ext=True)
                    if first_try:
                        # try another ad
                        self.adv(first_try=False)
                        return
                    else:
                        ad = None
                else:
                    self.error('XLRstats not installed! Cannot use @topstats in adv plugin!')
                    ad = '@topstats not available: XLRstats is not installed!'
            elif ad == "@admins":
                try:
                    command = self._adminPlugin._commands['admins']
                    command.executeLoud(data=None, client=None)
                    ad = None
                except Exception, err:
                    self.error("could not send adv message @admins", exc_info=err)
                    if first_try:
                        # try another ad
                        self.adv(first_try=False)
                        return
                    else:
                        ad = None
            elif ad == "@regulars":
                try:
                    command = self._adminPlugin._commands['regulars']
                    command.executeLoud(data=None, client=None)
                    ad = None
                except Exception, err:
                    self.error("could not send adv message @regulars", exc_info=err)
                    if first_try:
                        # try another ad
                        self.adv(first_try=False)
                        return
                    else:
                        ad = None

            if ad:
                self.console.say(ad)
            self._replay = 0

    def get_feed(self, ad):
        """
        Get a feed item to display.
        """
        i = ad.split()
        if len(i) == 2 and isinstance(i, list):
            i = i[1]
            self._feeditemnr = i
        else:
            if self._feeditemnr > self._feedmaxitems:
                self._feeditemnr = 0
            i = self._feeditemnr

        try:
            f = feedparser.parse(self._feed)
        except Exception:
            self.debug('not able to retrieve feed')
            return None
        try:
            _item = f['entries'][i]['title']
            self._feeditemnr += 1
            return self._feedpre + _item
        except Exception:
            self.debug('feeditem %s out of range' % i)
            self._feeditemnr = 0
            return None

    def _get_rate_minsec(self, rate):
        """
        Allow to define the rate in second by adding 's' at the end
        :param rate: The rate string representation
        """
        seconds = 0
        minutes = '*'
        if rate[-1] == 's':
            # rate is in seconds
            s = rate[:-1]
            if int(s) > 59:
                s = 59
            seconds = '*/%s' % s
        else:
            minutes = '*/%s' % rate
        self.debug('%s -> (%s,%s)' % (rate, minutes, seconds))
        return minutes, seconds

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_advadd(self, data, client=None, cmd=None):
        """
        <add> - add a new advertisement message
        """
        if not data:
            client.message('Missing data, try !help advadd')
        else:
            self._msg.put(data)
            client.message('^3Adv: ^7"%s^7" added' % data)
            if self._fileName:
                self.save()

    def cmd_advsave(self, data, client=None, cmd=None):
        """
        - save the current advertisement list
        """
        try:
            self.save()
            client.message('^3Adv: ^7saved %s messages' % len(self._msg.items))
        except Exception, e:
            client.message('^3Adv: ^7error saving: %s' % e)

    def cmd_advload(self, data, client=None, cmd=None):
        """
        Reload adv plugin configuration.
        """
        self.onLoadConfig()
        client.message('^3Adv: ^7loaded %s messages' % len(self._msg.items))

    def cmd_advrate(self, data, client=None, cmd=None):
        """
        [<rate>] - get/set the advertisement rotation rate
        """
        if not data:
            if self._rate[-1] == 's':
                client.message('Current rate is every %s seconds' % self._rate[:-1])
            else:
                client.message('Current rate is every %s minutes' % self._rate)
        else:
            self._rate = data
            (m, s) = self._get_rate_minsec(self._rate)
            self._cronTab.minute = m
            self._cronTab.second = s
            if self._rate[-1] == 's':
                client.message('^3Adv: ^7rate set to %s seconds' % self._rate[:-1])
            else:
                client.message('^3Adv: ^7rate set to %s minutes' % self._rate)

    def cmd_advrem(self, data, client=None, cmd=None):
        """
        <index> - removes an advertisement message
        """
        if not data:
            client.message('Missing data, try !help advrem')
        else:

            try:
                item_index = int(data) - 1
            except ValueError:
                client.message("Invalid data, use the !advlist command to list valid items numbers")
            else:
                if not 0 <= item_index < len(self._msg.items):
                    client.message("Invalid data, use the !advlist command to list valid items numbers")
                else:
                    item = self._msg.getitem(item_index)

                    if item:
                        self._msg.remove(int(data) - 1)
                        if self._fileName:
                            self.save()
                        client.message('^3Adv: ^7removed item: %s' % item)
                    else:
                        client.message('^3Adv: ^7item %s not found' % data)

    def cmd_advlist(self, data, client=None, cmd=None):
        """
        List advertisement messages
        """
        if len(self._msg.items) > 0:
            i = 0
            for msg in self._msg.items:
                i += 1
                client.message('^3Adv: ^7[^2%s^7] %s' % (i, msg))
        else:
            client.message('^3Adv: ^7no ads loaded')