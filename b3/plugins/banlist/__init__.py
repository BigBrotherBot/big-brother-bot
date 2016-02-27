#
# Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2008 Courgette <courgette@bigbrotherbot.net>
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

__version__ = '2.8'
__author__  = 'Courgette'

import b3
import b3.cron
import b3.events
import b3.plugin
import codecs
import gzip
import os
import random
import re
import string
import StringIO
import thread
import time
import urllib2

from b3.functions import getCmd
from ConfigParser import NoOptionError


user_agent =  "B3 Banlist plugin/%s" % __version__


class BanlistPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _banlists = None
    _whitelists = None
    _immunity_level = None
    _auto_update = None

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Startup the plugin.
        """
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            raise AttributeError('could not find admin plugin')

        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = getCmd(self, cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        self.registerEvent('EVT_CLIENT_AUTH', self.onAuth)

        if self._banlists:
            for banlist in self._banlists:
                if banlist._cronTab :
                    # remove existing crontab
                    self.console.cron - banlist._cronTab
        if self._whitelists:
            for whitelist in self._whitelists:
                if whitelist._cronTab :
                    # remove existing crontab
                    self.console.cron - whitelist._cronTab

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        try:
            self._immunity_level = self.config.getint('global_settings', 'immunity_level')
        except (NoOptionError, ValueError):
            self._immunity_level = 100

        try:
            self._auto_update = self.config.getboolean('global_settings', 'auto_update')
        except (NoOptionError, ValueError):
            self._auto_update = True

        self.info('immunity level : %s' % self._immunity_level)
        self.info('auto update : %s' % self._auto_update)

        # load banlists from config
        self._banlists = []
        for banlistconfig in self.config.get('ip_banlist'):
            try:
                b = IpBanlist(self, banlistconfig)
                self._banlists.append(b)
                self.info("IP banlist [%s] loaded" % b.name)
            except Exception, e:
                self.error(e)

        for banlistconfig in self.config.get('guid_banlist'):
            try:
                b = GuidBanlist(self, banlistconfig)
                self._banlists.append(b)
                self.info("Guid banlist [%s] loaded" % b.name)
            except Exception, e:
                self.error(e)

        for banlistconfig in self.config.get('pbid_banlist'):
            try:
                b = PbidBanlist(self, banlistconfig)
                self._banlists.append(b)
                self.info("PBid banlist [%s] loaded" % b.name)
            except Exception, e:
                self.error(e)

        for banlistconfig in self.config.get('rules_of_combat'):
            try:
                b = RocBanlist(self, banlistconfig)
                self._banlists.append(b)
                self.info("RocBanlist [%s] loaded" % b.name)
            except Exception, e:
                self.error(e)

        self.debug("%d banlist loaded" % len(self._banlists))

        # load whitelists from config
        self._whitelists = []
        for whitelistconfig in self.config.get('ip_whitelist'):
            try:
                b = IpBanlist(self, whitelistconfig)
                self._whitelists.append(b)
                self.info("IP white list [%s] loaded" % b.name)
            except Exception, e:
                self.error(e)

        for whitelistconfig in self.config.get('guid_whitelist'):
            try:
                b = GuidBanlist(self, whitelistconfig)
                self._whitelists.append(b)
                self.info("Guid white list [%s] loaded" % b.name)
            except Exception, e:
                self.error(e)

        for whitelistconfig in self.config.get('pbid_whitelist'):
            try:
                b = PbidBanlist(self, whitelistconfig)
                self._whitelists.append(b)
                self.info("PBid white list [%s] loaded" % b.name)
            except Exception, e:
                self.error(e)

        self.debug("%d whitelists loaded" % len(self._whitelists))
        self.checkConnectedPlayers()

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH.
        """
        if self._banlists:
            thread.start_new_thread(self.checkClient, (event.client,))

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def checkConnectedPlayers(self):
        """
        Check all the connected players.
        """
        self.info("checking all connected players")
        clients = self.console.clients.getList()
        for c in clients:
            self.checkClient(c)

    def checkClient(self, client):
        """
        Examine players ip-bans and allow/deny to connect.
        """
        self.debug('checking slot: %s, %s, %s, %s' % (client.cid, client.name, client.ip, client.guid))

        for whitelist in self._whitelists:
            result = whitelist.isBanned(client)
            if result is not False:
                self.info('@%s %s, ip:%s, guid:%s. Found in whitelist : %s' % (client.id, client.name, client.ip,
                                                                               client.guid, whitelist.name))
                msg = whitelist.getMessage(client)
                if msg and msg!="":
                    self.console.write(msg)
                return

        for banlist in self._banlists:
            result = banlist.isBanned(client)
            if result is not False:
                if client.maxLevel < self._immunity_level:
                    client.kick('BANLISTED [%s] %s' % (banlist.name, result), keyword="banlist", silent=True)
                    self.info('kicking @%s %s, ip:%s, guid:%s. Found in banlist : %s' % (client.id, client.name,
                                                                                         client.ip, client.guid, banlist.name))
                    msg = banlist.getMessage(client)
                    if msg and msg!="":
                        self.console.write(msg)
                    return
                else:
                    client.notice("%s, ip:%s, guid:%s found in banlist [%s] but is immune "
                                  "due to its level %s" % (client.name, client.ip, client.guid,
                                                           banlist.name, client.maxLevel), None)
                    self.info("@%s %s, ip:%s, guid:%s found in banlist [%s] but is immune "
                              "due to its level %s" % (client.id, client.name, client.ip,
                                                       client.guid, banlist.name, client.maxLevel))
                    return

    def _verboseUpdateBanListFromUrl(self, client, banlist):
        """
        Update a banlist from a URL
        """
        try:
            result = banlist.updateFromUrl()
            if result is True:
                client.message('^7[^4%s^7] ^2updated' % banlist.name)
            else:
                client.message('^7[^4%s^7] update ^1failed^7: %s' % (banlist.name, result))
        except BanlistException, e:
            self.warning("%s" % e.message)
            client.message('^7[^4%s^7] update ^1failed^7: %s' % (banlist.name, e.message))

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_banlistinfo(self, data=None, client=None, cmd=None):
        """
        [<num> <name|file|time|url|force_ip_range>] - get info about specified banlist
        """
        if not data:
            client.message('Loaded lists :')
            banlistnames = []
            for b in self._banlists:
                banlistnames.append('^3[%s]^2 %s' % (self._banlists.index(b), b.name))
            for b in self._whitelists:
                banlistnames.append('^3[%s]^2 %s' % (len(self._banlists) + self._whitelists.index(b), b.name))
            client.message(", ".join(banlistnames))

        else:
            m = re.match(r"(?P<num>\d+) (?P<info>name|file|time|url|force_ip_range)", data)
            if m is None:
                client.message('invalid data, try !help banlistinfo')
                return

            index = int(m.group('num'))
            info = m.group('info')
            try:
                b = self._banlists[index]
            except IndexError:
                try:
                    whitelistindex = index - len(self._banlists)
                    b = self._whitelists[whitelistindex]
                except IndexError:
                    client.message('cannot find banlist [%s]' % index)
                    return

            if info == 'time':
                msg = self.console.formatTime(b.getModifiedTime())
            else:
                msg = getattr(b, info)
            if client:
                client.message('%s' % msg)
            else:
                self.debug('%s' % msg)

    def cmd_banlistupdate(self, data=None, client=None, cmd=None):
        """
        Update all banlists from URL
        """
        self.debug("%s requested banlist update" % client.name)

        for banlist in self._banlists:
            if banlist.url is not None:
                thread.start_new_thread(self._verboseUpdateBanListFromUrl, (client, banlist))

        for banlist in self._whitelists:
            if banlist.url is not None:
                thread.start_new_thread(self._verboseUpdateBanListFromUrl, (client, banlist))

    def cmd_banlistcheck(self, data=None, client=None, cmd=None):
        """
        Check all players against banlists
        """
        if client is not None: client.message("checking players ...")
        self.checkConnectedPlayers()
        if client is not None: client.message("^4done")


class Banlist(object):

    _cronTab = None

    plugin = None
    name = None
    file = None
    message = None
    url = None
    remote_lastmodified = None
    remote_etag = None

    def __init__(self, plugin, config):
        """
        Create a new Banlist
        :param plugin: the banlist plugin instance
        :param config: the banlist plugin configuration file instance
        """
        self.plugin = plugin
        self.file_content = ""  # the banlist file content
        self.cache = {}  # used to cache isBanned results. Must be cleared after banlist file change/update
        self.cache_time = 0  # holds the modifed time of the banlist file used to fill that cache

        node = config.find('name')
        if node is None or node.text is None or node.text == '':
            self.plugin.warning("name not found in config")
        else:
            self.name = node.text

        node = config.find('file')
        if node is None or node.text is None or node.text == '':
            raise BanlistException("file not found in config")
        else:
            self.file = b3.getAbsolutePath(node.text)

        node = config.find('url')
        if node is not None and node.text != '':
            self.url = node.text

        node = config.find('message')
        if node is not None and node.text != '':
            self.message = node.text

        if not os.path.isfile(self.file):
            if self.url is None:
                raise BanlistException("file '%s' not found or not a file." % self.file)
            else:
                # create file from url
                result = self.updateFromUrl()
                if result is not True:
                    raise BanlistException("failed to create '%s' from %s. (%s)" % (self.file, self.url, result))

        elif self.url is not None:
            # check if file ues older than an hour
            fileage = (time.time() - os.stat("%s" % self.file)[8])
            self.plugin.debug("%s age is %s" % (self.file, fileage))
            if fileage > 3600:
                self.plugin.debug("[%s] file is older than an hour" % self.name)
                if self.plugin._auto_update:
                    result = self.updateFromUrl()
                    if result is not True:
                        raise BanlistException("failed to create '%s' from %s. (%s)" % (self.file, self.url, result))
                else:
                    self.plugin.warning("%s [%s] file is older than an hour, consider updating" % (self.__class__.__name__, self.name))


        if self.url is not None and self.plugin._auto_update:
            rmin = random.randint(0,59)
            self.plugin.debug("[%s] will be autoupdated at %s min of every hour" % (self.name, rmin))
            self._cronTab = b3.cron.PluginCronTab(self.plugin, self.autoUpdateFromUrl, 0, rmin, '*', '*', '*', '*')
            self.plugin.console.cron + self._cronTab

        self.plugin.info("loading %s [%s], file:[%s], url:[%s], message:[%s]" % (self.__class__.__name__, self.name,
                                                                                 self.file, self.url, self.message))

    def clear_cache(self):
        self.cache = {}
        self.cache_time = self.getModifiedTime()

    def _checkFileExists(self):
        if not os.path.isfile(self.file):
            if self.url is None:
                self.plugin.error("file '%s' not found or not a file." % self.file)
                return False
            else:
                # create file from url
                self._updateFromUrlAndCheckAll()
                return False # return False as _updateFromUrlAndCheckAll will call onBanlistUpdate
        else:
            return True

    def _updateFromUrlAndCheckAll(self):
        try:
            result = self.updateFromUrl()
            if result is not True:
                raise BanlistException("failed to update '%s' from %s. (%s)" % (self.file, self.url, result))
            self.plugin.checkConnectedPlayers()
        except BanlistException, e:
            self.plugin.warning("%s" % e.message)

    def updateFromUrl(self):
        """
        Download the banlist from the url found in config and save it.
        :return: True if succeeded, else return a string with the reason of failure
        """
        self.plugin.info("[%s] updating from %s" % (self.name, self.url))

        try:
            req =  urllib2.Request(self.url, None)
            req.add_header('User-Agent', user_agent)
            req.add_header('Accept-encoding', 'gzip')
            if self.remote_lastmodified:
                req.add_header('If-Modified-Since', self.remote_lastmodified)
            if self.remote_etag:
                req.add_header('If-None-Match', self.remote_etag)
            opener = urllib2.build_opener()
            self.plugin.debug('headers : %r', req.headers)
            webFile =  opener.open(req)
            result = webFile.read()
            webFile.close()
            if webFile.headers.get('content-encoding', '') == 'gzip':
                result = StringIO.StringIO(result)
                gzipper = gzip.GzipFile(fileobj=result)
                result = gzipper.read()
            self.remote_lastmodified = webFile.headers.get('Last-Modified') 
            self.remote_etag = webFile.headers.get('ETag') 
            self.plugin.debug('received headers : %s', webFile.info())
            self.plugin.debug("received %s bytes", len(result))
            localFile = open(self.file, 'w')
            localFile.write(result)
            localFile.close()
            return True
        except urllib2.HTTPError, err:
            if err.code == 304:
                self.plugin.info("remote banlist unchanged since last update")
                return True
            else:
                self.remote_etag = self.remote_lastmodified = None
                self.plugin.error("%r", err)
                return "%s" % err
        except urllib2.URLError, err:
            self.remote_etag = self.remote_lastmodified = None
            return "%s" % err
        except IOError, e:
            self.remote_etag = self.remote_lastmodified = None
            if hasattr(e, 'reason'):
                return "%s" % e.reason
            elif hasattr(e, 'code'):
                return "error code: %s" % e.code
            self.plugin.debug("%s" % e)
            return "%s" % e

    def autoUpdateFromUrl(self):
        thread.start_new_thread(self._updateFromUrlAndCheckAll, ())

    def getMessage(self, client):
        """
        Return the message with pattern $name replaced with the banlist's name.
        """
        return self.message.replace('$name','%s' % client.name)\
            .replace('$ip','%s' % client.ip)\
            .replace('$guid','%s' % client.guid)\
            .replace('$pbid','%s' % client.pbid)\
            .replace('$id','@%s' % client.id)

    def getModifiedTime(self):
        """
        return the last modified time of the banlist file
        """
        return os.stat("%s" % self.file)[8]

    def getHumanModifiedTime(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.getModifiedTime()))

    def refreshBanlistContent(self):
        if not self._checkFileExists():
            return ""

        if self.cache_time != self.getModifiedTime():
            with open(self.file) as f:
                self.plugin.verbose("updating %s content cache from %s" % (self, self.file))
                self.file_content = f.read()
            self.clear_cache()


class IpBanlist(Banlist):

    _forceRange = None

    def __init__(self, plugin, config):
        """
        Create a new IpBanlist
        :param plugin: the banlist plugin instance
        :param config: the banlist plugin configuration file instance
        """
        Banlist.__init__(self, plugin, config)
        # set specific settings
        node = config.find('force_ip_range')
        if node is not None and string.upper(node.text) in ('YES', '1', 'ON', 'TRUE'):
            self._forceRange = True
        else:
            self._forceRange = False
        self.plugin.debug("%s [%s] force IP range : %s" % (self.__class__.__name__, self.name, self._forceRange))

    def isBanned(self, client):
        """
        Check whether a client is banned
        """
        if not client.ip:
            return False

        self.refreshBanlistContent()

        if client.ip not in self.cache:
            self.cache[client.ip] = self.isIpInBanlist(client.ip)

        rv, msg = self.cache[client.ip]
        if rv:
            self.plugin.info(msg)
        else:
            self.plugin.verbose(msg)
        return rv

    def isIpInBanlist(self, ip):
        # search the exact ip
        rStrict = re.compile(r'''^(?P<entry>%s(?:[^\d\n\r].*)?)$''' % re.escape(ip), re.MULTILINE)
        m = rStrict.search(self.file_content)
        if m:
            return ip, "ip '%s' matches banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        # search the ip with .0 at the end
        rRange = re.compile(r'''^(?P<entry>%s\.0(?:[^\d\n\r].*)?)$''' % re.escape('.'.join(ip.split('.')[0:3])), re.MULTILINE)
        m = rRange.search(self.file_content)
        if m:
            return ip, "ip '%s' matches (by range) banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        # search the ip with .0.0 at the end
        rRange = re.compile(r'''^(?P<entry>%s\.0\.0(?:[^\d\n\r].*)?)$''' % re.escape('.'.join(ip.split('.')[0:2])), re.MULTILINE)
        m = rRange.search(self.file_content)
        if m:
            return ip, "ip '%s' matches (by range) banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        # search the ip with .0.0.0 at the end
        rRange = re.compile(r'''^(?P<entry>%s\.0\.0\.0(?:[^\d\n\r].*)?)$''' % re.escape('.'.join(ip.split('.')[0:1])), re.MULTILINE)
        m = rRange.search(self.file_content)
        if m:
            return ip, "ip '%s' matches (by range) banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        # if force range is set, enforce search by range even if banlist ip are not ending with ".0"
        if self._forceRange:
            rForceRange = re.compile(r'''^(?P<entry>%s\.\d{1,3}(?:[^\d\n\r].*)?)$''' % re.escape('.'.join(ip.split('.')[0:3])), re.MULTILINE)
            m = rForceRange.search(self.file_content)
            if m:
                return ip, "ip '%s' matches (by forced range) banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        return False, "ip '%s' not found in banlist (%s %s)" % (ip, self.name, self.getHumanModifiedTime())


class GuidBanlist(Banlist):

    def isBanned(self, client):
        """
        Check whether a client is banned
        """
        if not client.guid:
            return False

        self.refreshBanlistContent()

        if client.guid not in self.cache:
            self.cache[client.guid] = self.isGuidInBanlist(client.guid)

        rv, msg = self.cache[client.guid]
        if rv:
            self.plugin.info(msg)
        else:
            self.plugin.verbose(msg)
        return rv

    def isGuidInBanlist(self, guid):
        re_guid = re.compile(r'''^(?P<entry>\s*%s\b.*)$''' % re.escape(guid), re.IGNORECASE | re.MULTILINE)
        m = re_guid.search(self.file_content)
        if m:
            return guid, "guid '%s' matches banlist entry %r (%s %s)" % (guid, m.group('entry'), self.name, self.getHumanModifiedTime())
        return False, "guid '%s' not found in banlist (%s %s)" % (guid, self.name, self.getHumanModifiedTime())


class PbidBanlist(Banlist):

    def isBanned(self, client):
        """
        Check whether a client is banned
        """
        if not client.pbid:
            return False

        self.refreshBanlistContent()

        if client.pbid not in self.cache:
            self.cache[client.pbid] = self.isPbidInBanlist(client.pbid)

        rv, msg = self.cache[client.pbid]
        if rv:
            self.plugin.info(msg)
        else:
            self.plugin.verbose(msg)
        return rv

    def isPbidInBanlist(self, pbid):
        re_guid = re.compile(r'''^(?P<entry>\s*%s\b.*)$''' % re.escape(pbid), re.IGNORECASE | re.MULTILINE)
        m = re_guid.search(self.file_content)
        if m:
            return pbid, "PBid '%s' matches banlist entry %r (%s %s)" % (pbid, m.group('entry'), self.name, self.getHumanModifiedTime())
        return False, "PBid '%s' not found in banlist (%s %s)" % (pbid, self.name, self.getHumanModifiedTime())


class RocBanlist(Banlist):

    def isBanned(self, client):
        """
        Check whether a client is banned
        """
        if not client.guid:
            return False

        if not self._checkFileExists():
            return False

        f = codecs.open(self.file, "r", "iso-8859-1" )
        banlist=f.read()
        self.plugin.debug(u"checking %s" % client.guid)
        if u'BannedID="%s"' % client.guid in banlist:
            f.close()
            return client.guid

        f.close()
        return False


class BanlistException(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)