#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
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

__version__ = '1.1.8'
__author__  = 'ThorN'

import urllib
import b3, os, random
import b3.events
import b3.plugin
from b3 import functions

# set up our URLopener so we can specify a custom User-Agent
class PublistURLopener(urllib.FancyURLopener):
    version = "B3 Publist plugin/%s" % __version__
urllib._urlopener = PublistURLopener()


#--------------------------------------------------------------------------------------------------
class PublistPlugin(b3.plugin.Plugin):
  _cronTab = None
  _url='http://www.bigbrotherbot.com/master/serverping.php'
  requiresConfigFile = False

  def onStartup(self):
    
    # get the plugin so we can register commands
    self._adminPlugin = self.console.getPlugin('admin')
    if not self._adminPlugin:
      # something is wrong, can't start without admin plugin
      self.error('Could not find admin plugin')
      return False
    
    try:
      self._advertise = self._adminPlugin.config.getboolean('server', 'list')
    except:
      pass

    # set cvar for advertising purposes
    try:
      cvarValue = 'B3 %s' % b3.versionId
      self.console.setCvar('_B3',cvarValue)
    except:
      pass
    
    rmin = random.randint(0,59)
    rhour = random.randint(0,23)
    self.debug("publist will send heartbeat at %02d:%02d every day" % (rhour,rmin))
    self._cronTab = b3.cron.PluginCronTab(self, self.update, 0, rmin, rhour, '*', '*', '*')
    self.console.cron + self._cronTab
    
    # send initial heartbeat
    self.update()
    

  def update(self):
    self.debug('Sending heartbeat to B3 master...')
    
    
    def getModule(name):
      mod = __import__(name)
      components = name.split('.')
      for comp in components[1:]:
        mod = getattr(mod, comp)
      return mod
      
    plugins = []
    for pname in self.console._pluginOrder:
      plugins.append("%s/%s" % (pname, getattr(getModule(self.console.getPlugin(pname).__module__), '__version__', 'Unknown Version')))
      
    info = {
      'ip' : self.console._publicIp,
      'port' : self.console._port,
      'version' : b3.versionId,
      'parser' : self.console.gameName,
      'parserversion' : getattr(getModule(self.console.__module__), '__version__', 'Unknown Version'),
      'database' : functions.splitDSN(self.console.storage.dsn)['protocol'],
      'plugins' : ','.join(plugins),
      'os' : os.name
    }
    #self.debug(info)

    f = urllib.urlopen('%s?%s' % (self._url, urllib.urlencode(info)))
    self.debug(f.read())
    f.close()

      