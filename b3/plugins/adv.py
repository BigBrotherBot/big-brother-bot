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
# 04/18/2011 - 1.3.1 - Courgette
#    makes @admins show admins' level as well
# 04/18/2011 - 1.3.0 - Courgette
#    add the @admins keyword that displays the connected admins
#    when the ad is @topstats or @amdins but no message is to be shown, then 
#      try next ad
# 10/24/2010 - 1.2.2 - Courgette
#    Prevent crash when no feed is specified in config
# 08/20/2010 - 1.2.1 - xlr8or
#    Add @topstats for xlrstats
# 08/06/2010 - 1.2 - xlr8or
#    Add feedparser (@feed or @feed <nr>)
# 08/06/2010 - 1.1.5 - xlr8or
#    Remove save() errors and !advsave when XML adds are used
#    This needs to be re-enabled when saving to XML is supported
# 11/22/2009 - 1.1.4 - Courgette
#    fix bug when using external text ads file which is empty
# 2/27/2009 - 1.1.3 - xlr8or
#    Added Anubis suggestion @nextmap to ads and also @time to show time.
# 11/30/2005 - 1.1.2 - ThorN
#    Use PluginCronTab instead of CronTab
# 8/29/2005 - 1.1.0 - ThorN
#    Converted to use XML config

__author__ = 'ThorN'
__version__ = '1.3.1'

import b3
import os
import time
import string
import b3.lib.feedparser as feedparser
import b3.plugin
import b3.cron

class MessageLoop:
    items = None
    def __init__(self):
        self.items = []
        self.index = 0

    def put(self, item):
        self.items.append(item)

    def getnext(self):
        try:
            item = self.items[self.index]
        except:
            self.index = 0
            return None
    
        self.index += 1

        if self.index >= len(self.items):
            self.index = 0

        return item

    def getitem(self, index):
        try:
            return self.items[index]
        except:
            return None

    def remove(self, index):
        # empty the list
        i = 0

        items = []
        for item in self.items:
            if i != index:
                items.append(item)

            i += 1

        self.items = items
            
    def clear(self):
        # empty the list
        self.items = []

#--------------------------------------------------------------------------------------------------
class AdvPlugin(b3.plugin.Plugin):
    _adminPlugin = None
    _cronTab = None
    _msg = None
    _fileName = None
    _rate = None
    _feed = 'http://forum.bigbrotherbot.net/news-2/?type=rss;action=.xml'
    _feedpre = u'News: '
    _feedmaxitems = 5
    _feeditemnr = 0
    _replay = 0

    def onStartup(self):
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
            self.debug('XLRstats not installed, @topstats not available!')
        else:
            self.debug('XLRstats found, @topstats available!')

    def onLoadConfig(self):
        self._adminPlugin = self.console.getPlugin('admin')
        self._msg = MessageLoop()

        try:
            self._rate = self.config.get('settings', 'rate')
            self.info('adv rate is %s' % self._rate)
        except:
            self.error('config missing [settings].rate')
            return False

        if self.config.has_option('settings', 'ads'):
            self._fileName = self.console.getAbsolutePath(self.config.get('settings', 'ads'))
            self.loadFromFile(self._fileName)
        else:
            self._fileName = None
            self.loadFromConfig()

        try:
            self._feed = self.config.get('newsfeed', 'url')
        except:
            pass

        try:
            self._feedmaxitems = self.config.getint('newsfeed', 'items')
        except:
            pass
        #reduce feedmaxitems 1 point, since we're starting at item 0, this makes counting easier...
        self._feedmaxitems -= 1
        self.verbose('self._feedmaxitems: %s' %self._feedmaxitems)

        try:
            self._feedpre = self.config.get('newsfeed', 'pretext')
        except:
            pass

        #test if we have a proper feed
        if self._feed is not None:
            if self._feed.strip() == '':
                self._feed = None
            else:
                f = feedparser.parse(self._feed)
                
                if not f or f['bozo'] == 1:
                    self._feed = None
                    self.warning('Error reading feed at %s' % self._feed)
                    self.debug(f['bozo_exception'])

        if self._cronTab:
            # remove existing crontab
            self.console.cron - self._cronTab

        (min, sec) = self._getRateMinSec()
        self._cronTab = b3.cron.PluginCronTab(self, self.adv, second=sec, minute=min)
        self.console.cron + self._cronTab

    def save(self):
        if self._fileName:        
            f = file(self._fileName, 'w')
            for msg in self._msg.items: 
                if msg:         
                    f.write(msg + "\n")
            f.close()
        else:
            self.verbose('Save to XML config not supported')
            raise Exception('Save to XML config not supported')

    def loadFromFile(self, fileName):
        if not os.path.isfile(fileName):
            self.error('Ad file %s does not exist', fileName)
            return False

        f = file(fileName, 'r')
        self.load(f.readlines())
        f.close()

    def loadFromConfig(self):
        items = []
        for e in self.config.get('ads/ad'):
            items.append(e.text)

        self.load(items)

    def load(self, items=[]):
        self._msg.clear()

        for w in items:
            w = w.strip()
            if len(w) > 1:
                if w[:6] == '/spam#':
                    w = self._adminPlugin.getSpam(w[6:])
                self._msg.put(w)                
        
    def adv(self, firstTry=True):
        ad = self._msg.getnext()
        if ad:
            if ad == "@nextmap":
                ad = "^2Next map: ^3" + self.console.getNextMap()
            elif ad == "@time":
                ad = "^2Time: ^3" + self.console.formatTime(time.time())
            elif ad[:5] == "@feed" and self._feed:
                ad = self.getFeed(ad)
                if not ad or ad == self._feedpre:
                    #we didn't get an item from the feedreader, move on to the next ad
                    self._replay += 1
                    #prevent endless loop if only feeditems are used as adds
                    if self._replay < 10:
                        self.adv()
                    else:
                        self.debug('Something wrong with the newsfeed, disabling it. Fix the feed and do !advload')
                        self._feed = None
                    return
            elif ad == "@topstats":
                if self._xlrstatsPlugin:
                    self._xlrstatsPlugin.cmd_xlrtopstats(data='3', client=None, cmd=None, ext=True)
                    if firstTry:
                        # try another ad
                        self.adv(firstTry=False)
                        return
                    else:
                        ad = None
                else:
                    self.error('XLRstats not installed! Cannot use @topstats in adv plugin!')
                    ad = '@topstats not available, XLRstats is not installed!'
            elif ad == "@admins":
                admins = self._adminPlugin.getAdmins()
                nlist = []
                for c in admins:
                    if c.maskGroup:
                        nlist.append('%s^7 [^3%s^7]' % (c.exactName, c.maskGroup.level))
                    else:
                        nlist.append('%s^7 [^3%s^7]' % (c.exactName, c.maxLevel))
                if len(nlist)>0:
                    ad = self._adminPlugin.getMessage('admins', string.join(nlist, ', '))
                else:
                    if firstTry:
                        # try another ad
                        self.adv(firstTry=False)
                        return
                    else:
                        ad = None
            if ad:
                self.console.say(ad)
            self._replay = 0

    def getFeed(self, ad):
        i = ad.split()
        if len(i) == 2 and type(i) == type(1):
            i = i[1]
            self._feeditemnr = i
        else:
            if self._feeditemnr > self._feedmaxitems:
                self._feeditemnr = 0
            i = self._feeditemnr
        try:
            f = feedparser.parse(self._feed)
        except:
            self.debug('Not able to retrieve feed')
            return None
        try:
            _item = f['entries'][i]['title']
            self._feeditemnr += 1
            return self._feedpre + _item
        except:
            self.debug('Feeditem %s out of range' %i)
            self._feeditemnr = 0
            return None

    def cmd_advadd(self, data, client=None, cmd=None):
        self._msg.put(data)
        client.message('^3Adv: ^7"%s^7" added' % data)
        if self._fileName:
            self.save()

    def cmd_advsave(self, data, client=None, cmd=None):
        try:
            self.save()
            client.message('^3Adv: ^7Saved %s messages' % len(self._msg.items)) 
        except Exception, e:
            client.message('^3Adv: ^7Error saving: %s' % e)

    def cmd_advload(self, data, client=None, cmd=None):
        self.onLoadConfig()
        client.message('^3Adv: ^7Loaded %s messages' % len(self._msg.items))    

    def cmd_advrate(self, data, client=None, cmd=None):
        self._rate = data
        (min, sec) = self._getRateMinSec()
        self._cronTab.minute = min
        self._cronTab.second = sec
        if self._rate[-1] == 's':
            client.message('^3Adv: ^7Rate set to %s seconds' % self._rate[:-1])    
        else:
            client.message('^3Adv: ^7Rate set to %s minutes' % self._rate)    

    def cmd_advrem(self, data, client=None, cmd=None):
        item = self._msg.getitem(int(data) - 1)

        if item:
            self._msg.remove(int(data) - 1)
            if self._fileName:
                self.save()
            client.message('^3Adv: ^7Removed item: %s' % item)    
        else:
            client.message('^3Adv: ^7Item %s not found' % data) 

    def cmd_advlist(self, data, client=None, cmd=None):
        if len(self._msg.items) > 0:
            i = 0
            for msg in self._msg.items:
                i += 1
                client.message('^3Adv: ^7[^2%s^7] %s' % (i, msg))
        else:
            client.message('^3Adv: ^7No ads loaded')

    def _getRateMinSec(self):
        """\
        allow to define the rate in second by adding 's' at the end
        """
        sec = 0
        min = '*'
        if self._rate[-1] == 's':
            # rate is in seconds
            s = self._rate[:-1]
            if int(s) > 59:
                s = 59
            sec = '*/%s' % s
        else:
            min = '*/%s' % self._rate
        self.debug('%s -> (%s,%s)' % (self._rate, min, sec))
        return (min, sec)
    
if __name__ == '__main__':
    from b3.fake import fakeConsole
    from b3.fake import joe, moderator, superadmin
    from b3.config import XmlConfigParser
    
    def test1():
        conf = XmlConfigParser()
        conf.setXml("""
    <configuration plugin="adv">
        <!--
            Note: within ads, you can use the following variables : @nextmap @time
            or rules as defined in the admin plugin config file. ie: /spam#rule1
        -->
        <settings name="settings">
            <!-- rate in minutes-->
            <set name="rate">5</set>
            <!--
                you can either set here a text file that will contain one ad per line
                or fill the <ads> section below
            -->
            <!-- <set name="ads">c:/somewhere/my_ads.txt</set> -->
        </settings>
      <settings name="newsfeed">
            <!--
                you can include newsitems in your adds by setting the section below
                you can add feeditems in the adds like this:
                @feed   (will pick the next newsitem each time it is included in the rotation,
                   rotating until 'items' is reached and then start over.)
                @feed 0 (will pick the latest newsitem available from the feed and add it in the rotation)
                @feed 1 (will pick the second latest item in line)
                etc.
            -->
            <set name="url">http://forum.bigbrotherbot.net/news-2/?type=rss;action=.xml</set>
            <set name="url.bak"></set>
            <set name="items">5</set>
            <set name="pretext">News: </set>
        </settings>
        <ads>
            <ad>^2Big Brother Bot is watching you... www.BigBrotherBot.net</ad>
            <ad>@topstats</ad>
            <ad>@feed</ad>
            <ad>/spam#rule1</ad>
            <ad>@time</ad>
            <ad>@feed</ad>
            <ad>^2Do you like B3? Consider donating to the project at www.BigBrotherBot.net</ad>
            <ad>@nextmap</ad>
        </ads>
    </configuration>
        """)
        p = AdvPlugin(fakeConsole, conf)
        p.onStartup()
        
        p.adv()
        print "-----------------------------"
        time.sleep(2)
        
        joe.connects(1)
        joe._maxLevel = 100
        joe.says('!advlist')
        time.sleep(2)
        joe.says('!advrem 0')
        time.sleep(2)
        joe.says('!advrate 5s')
        time.sleep(5)
        
        time.sleep(60)
        
    def testAdmins():
        conf = XmlConfigParser()
        conf.setXml("""
      <configuration plugin="adv">
        <settings name="settings">
            <set name="rate">1s</set>
        </settings>
        <ads>
            <ad>^2Do you like B3? Consider donating to the project at www.BigBrotherBot.net</ad>
            <ad>@admins</ad>
        </ads>
    </configuration>
        """)
        p = AdvPlugin(fakeConsole, conf)
        p.onStartup()
        
        p.adv()
        print "-----------------------------"
        time.sleep(4)
        joe.connects(1)
        time.sleep(4)
        moderator.connects(2)
        time.sleep(4)
        superadmin.connects(3)
        
        time.sleep(60)


    #test1()
    testAdmins()