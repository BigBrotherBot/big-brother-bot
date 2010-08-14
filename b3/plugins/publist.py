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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# $Id: publist.py 43 2005-12-06 02:17:55Z thorn $
#
# CHANGELOG
# 11/30/2005 - 1.0.3 - ThorN
# Use PluginCronTab instead of CronTab
# 23:29 17/07/2008 - 1.1.6- Courgette
# Add specific user-agent
# url is now store in a property
# add info: version, parserversion, database, plugins, os
# cron job will trigger at a random minute time to avoid jamming
# 22:58 18/07/2008 - 1.1.7 - Courgette
# add parser version and plugins' versions
# 7/7/2009 - 1.1.8 - xlr8or
# removed cvar check and critical stop
# 7/14/2009 - 1.1.9 - courgette
# bot version sent is now only the version number
# 10/5/2009 - 1.1.10 - xlr8or
# made the urllib not exit on error when connection to masterserver is impossible
# 10/19/2009 - 1.1.11 - Courgette
# add a timeout to the HTTP call (need urllib2 for that)
# initial call is now threaded
# 13/11/2009 - 1.1.12 - Courgette
# minor severity of messages
# do not send heartbeat when publicIP is obviously not public
# 23/11/2009 - 1.2.0 - Courgette
# * publist plugin now also update B3 master on shutdown
# 22/12/2009 - 1.3 - Courgette
# * bot version tells if the bot is built with py2exe
# 10/03/2010 - 1.4 - Courgette
# * rconPort is sent 
# 21/03/2010 - 1.4.1 - Courgette
# * fix rconPort when update type of ping is sent 
# 17/04/2010 - 1.5 - Courgette
# * allow to send ping to an additionnal master (mostly used for debugging master code)
# * send the python version to the master
#

__version__ = '1.5'
__author__  = 'ThorN, Courgette'

import sys
import thread
import urllib
import urllib2
import socket
import b3, os, random
import b3.events
import b3.plugin
from b3 import functions
from b3.functions import getModule




#--------------------------------------------------------------------------------------------------
class PublistPlugin(b3.plugin.Plugin):
    _cronTab = None
    _url='http://www.bigbrotherbot.net/master/serverping.php'
    _secondUrl = None
    requiresConfigFile = False
    
    def onLoadConfig(self):
        try:
            self._secondUrl = self.config.get('settings', 'url')
            self.debug('Using second url : %s' % self._secondUrl)
        except:
            pass
            
    def onStartup(self):
      
        # get the plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False

        
        # set cvar for advertising purposes
        try:
            cvarValue = 'B3 %s' % b3.versionId
            self.console.setCvar('_B3',cvarValue)
        except:
            pass
        
        
        if self.console._publicIp == '127.0.0.1':
            self.info("publist will not send heartbeat to master server as publicIp is not public.")
            return
        
        rmin = random.randint(0,59)
        rhour = random.randint(0,23)
        self.debug("publist will send heartbeat at %02d:%02d every day" % (rhour,rmin))
        self._cronTab = b3.cron.PluginCronTab(self, self.update, 0, rmin, rhour, '*', '*', '*')
        self.console.cron + self._cronTab
        
        # send initial heartbeat
        thread.start_new_thread(self.update, ())
      
    def onEvent(self, event):
        if event.type == b3.events.EVT_STOP:
            info = {
                'action' : 'shutdown',
                'ip' : self.console._publicIp,
                'port' : self.console._port,
                'rconPort' : self.console._rconPort
            }
            #self.debug(info)
            self.info('Sending shutdown info to B3 master')
            self.sendInfo(info)
    
    def update(self):
        self.debug('Sending heartbeat to B3 master...')
        socket.setdefaulttimeout(10)
        
        plugins = []
        for pname in self.console._pluginOrder:
            plugins.append("%s/%s" % (pname, getattr(getModule(self.console.getPlugin(pname).__module__), '__version__', 'Unknown Version')))
          
        try:
            database = functions.splitDSN(self.console.storage.dsn)['protocol']
        except:
            database = "unknown"
            
        version = getattr(b3, '__version__', 'Unknown Version')
        if b3.functions.main_is_frozen():
            version += " win32"
            
        info = {
            'action' : 'update',
            'ip' : self.console._publicIp,
            'port' : self.console._port,
            'rconPort' : self.console._rconPort,
            'version' : version,
            'parser' : self.console.gameName,
            'parserversion' : getattr(getModule(self.console.__module__), '__version__', 'Unknown Version'),
            'database' : database,
            'plugins' : ','.join(plugins),
            'os' : os.name,
            'python_version': sys.version
        }
        #self.debug(info)
        self.sendInfo(info)
        
    
    def sendInfo(self, info={}):
        self.sendInfoToMaster(self._url, info)
        if self._secondUrl is not None:
            self.sendInfoToMaster(self._secondUrl, info)
    
    def sendInfoToMaster(self, url, info={}):
        try:
            request = urllib2.Request('%s?%s' % (url, urllib.urlencode(info)))
            request.add_header('User-Agent', "B3 Publist plugin/%s" % __version__)
            opener = urllib2.build_opener()
            replybody = opener.open(request).read()
            if len(replybody)>0: 
                self.debug("master replied: %s" % replybody)
        except IOError, e:
            if hasattr(e, 'reason'):
                self.error('Unable to reach B3 masterserver, maybe the service is down or internet was unavailable')
                self.debug(e.reason)
            elif hasattr(e, 'code'):
                if e.code == 400:
                    self.info('B3 masterserver refused the heartbeat. reason: %s', e.msg)
                else:
                    self.info('Unable to reach B3 masterserver, maybe the service is down or internet was unavailable')
                    self.debug(e)
        except:
            self.warning('Unable to reach B3 masterserver. unknown error')
            print sys.exc_info()


if __name__ == '__main__':
    from b3.fake import fakeConsole
    import time
    
    from b3.config import XmlConfigParser
    
    conf = XmlConfigParser()
    conf.setXml("""
    <configuration plugin="publist">
        <settings name="settings">
            <set name="url">http://test.somewhere.com/serverping.php</set>
        </settings>
    </configuration>
    """)

    
    #fakeConsole._publicIp = '127.0.0.1'
    fakeConsole._publicIp = '11.22.33.44'
    p = PublistPlugin(fakeConsole, conf)
    #p.onStartup()
    p.onLoadConfig()
    #p.update()
    
    p.sendInfo({'version': '1.3-dev', 
            'os': 'nt', 
            'database': 'unknown', 
            'action': 'update', 
            'ip': '91.121.95.52', 
            'parser': 'iourt41', 
            'plugins': '', 
            'port': 27960, 
            'parserversion': '1.2', 
            'rconPort': None,
            'python_version': sys.version
    })
    
    time.sleep(5) # so we can see thread working

    #p.sendInfo({'action' : 'shutdown', 'ip' : '91.121.95.52', 'port' : 27960, 'rconPort' : None })
    