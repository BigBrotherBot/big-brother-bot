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

__author__ = 'ThorN, Courgette'
__version__ = '1.14'

import b3
import b3.cron
import b3.events
import b3.plugin
import sys
import urllib
import urllib2
import socket
import os
import random

from b3 import functions
from b3.functions import getModule
from ConfigParser import NoOptionError
from time import strftime


class PublistPlugin(b3.plugin.Plugin):

    requiresConfigFile = False

    _cronTab = None
    _url = 'http://www.bigbrotherbot.net/master/serverping.php'
    _secondUrl = None
    _heartbeat_sent = False
    _initial_heartbeat_delay_minutes = 5

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        if self.config is None:
            return

        try:
            self._secondUrl = self.config.get('settings', 'url')
            self.debug('using second url: %s' % self._secondUrl)
        except NoOptionError:
            pass
        
        try:
            self._initial_heartbeat_delay_minutes = self.config.getint('settings', 'delay')
            self.debug('loaded settings/delay: %s' % self._initial_heartbeat_delay_minutes)
        except (NoOptionError, ValueError):
            pass
            
    def onStartup(self):
        """
        Initialize the plugin.
        """
        try:
            # set cvar for advertising purposes
            self.console.setCvar('_B3', 'B3 %s' % b3.versionId)
        except Exception:
            pass  # some B3 parser have no cvar and no setCvar method (Q3 specific method)

        if self.console._publicIp == '127.0.0.1':
            self.info("publist will not send heartbeat to master server as publicIp is not public")
            return
        
        rmin = random.randint(0, 59)
        rhour = random.randint(0, 23)
        self.debug("publist will send heartbeat at %02d:%02d every day" % (rhour, rmin))
        self._cronTab = b3.cron.PluginCronTab(self, self.update, 0, rmin, rhour, '*', '*', '*')
        self.console.cron + self._cronTab
        
        # planning initial heartbeat
        # v1.9.1: Changing the threaded timer to a one time crontab to enable quick shutdown of the bot.
        _im = int(strftime('%M')) + self._initial_heartbeat_delay_minutes
        if _im >= 60:
            _im -= 60

        self.info('initial heartbeat will be sent to B3 master server at %s minutes' % (str(_im).zfill(2)))
        self._cronTab = b3.cron.OneTimeCronTab(self.update, 0, _im, '*', '*', '*', '*')
        self.console.cron + self._cronTab

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onStop(self, event):
        """
        Handle intercepted events
        """
        if self._heartbeat_sent:
            self.shutdown()

    ####################################################################################################################
    #                                                                                                                  #
    #    FUNCTIONS                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    def removeCrontab(self):
        """
        Removes the current crontab.
        """
        try:
            self.console.cron - self._cronTab
        except KeyError: 
            pass

    def shutdown(self):
        """
        Send a shutdown heartbeat to B3 master server.
        """
        self.info('Sending shutdown info to B3 master')
        info = {
            'action': 'shutdown',
            'ip': self.console._publicIp,
            'port': self.console._port,
            'rconPort': self.console._rconPort
        }
        # self.debug(info)
        self.sendInfo(info)
    
    def update(self):
        """
        Send an update heartbeat to B3 master server.
        """
        self.debug('sending heartbeat to B3 master...')
        socket.setdefaulttimeout(10)
        
        plugins = []
        for pname in self.console._plugins:
            try:
                pl = self.console.getPlugin(pname)
                p_module = getModule(pl.__module__)
                p_version = getattr(p_module, '__version__', 'unknown')
                plugins.append("%s/%s" % (pname, p_version))
            except Exception, e:
                self.warning("could not get version for plugin named '%s'" % pname, exc_info=e)
          
        try:
            database = functions.splitDSN(self.console.storage.dsn)['protocol']
        except Exception:
            database = "unknown"

        version = getattr(b3, '__version__', 'unknown')
        if b3.functions.main_is_frozen():
            version_info = b3.getB3versionInfo()
            version = '%s %s%s' % (version, version_info[1], version_info[2])
            
        info = {
            'action': 'update',
            'ip': self.console._publicIp,
            'port': self.console._port,
            'rconPort': self.console._rconPort,
            'version': version,
            'parser': self.console.gameName,
            'parserversion': getattr(getModule(self.console.__module__), '__version__', 'unknown'),
            'database': database,
            'plugins': ','.join(plugins),
            'os': os.name,
            'python_version': sys.version,
            'default_encoding': sys.getdefaultencoding()
        }
        
        if self.console.gameName in ('bfbc2', 'moh', 'bf3'):
            try:
                cvar_description = self.console.getCvar('serverDescription')
                if cvar_description is not None:
                    info.update({'serverDescription': cvar_description.value})
                cvar_banner_url = self.console.getCvar('bannerUrl')
                if cvar_banner_url is not None:
                    info.update({'bannerUrl': cvar_banner_url.value})
            except Exception, e:
                self.debug(e)
        
        self.debug(info)
        self.sendInfo(info)
    
    def sendInfo(self, info=None):
        """
        Send information to the B3 master server.
        """
        if info is None:
            info = {}
        self.sendInfoToMaster(self._url, info)
        self._heartbeat_sent = True
        if self._secondUrl is not None:
            self.sendInfoToMaster(self._secondUrl, info)
    
    def sendInfoToMaster(self, url, info=None):
        """
        Send data to the B3 master server.
        """
        if info is None:
            info = {}
        try:
            request = urllib2.Request('%s?%s' % (url, urllib.urlencode(info)))
            request.add_header('User-Agent', "B3 Publist plugin/%s" % __version__)
            opener = urllib2.build_opener()
            replybody = opener.open(request).read()
            if len(replybody) > 0:
                self.debug("master replied: %s" % replybody)
        except IOError, e:
            if hasattr(e, 'reason'):
                self.error('unable to reach B3 masterserver: maybe the service is down or internet was unavailable')
                self.debug(e.reason)
            elif hasattr(e, 'code'):
                if e.code == 400:
                    self.info('B3 masterserver refused the heartbeat: %s: disabling publist', e)
                    self.removeCrontab()
                elif e.code == 403:
                    self.info('B3 masterserver definitely refused our ping: disabling publist')
                    self.removeCrontab()
                else:
                    self.info('unable to reach B3 masterserver: maybe the service is down or internet was unavailable')
                    self.debug(e)
        except Exception:
            self.warning('unable to reach B3 masterserver: unknown error')
            print sys.exc_info()