#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
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
# CHANGELOG
#    1/16/2010 - 2.2.0 - xlr8or
#       Added ignore_length as an optional configurable option
#       Started debugging the badname checker
#    8/13/2005 - 2.0.0 - ThorN
#       Converted to use XML config
#       Allow custom penalties for words and names
#    7/23/2005 - 1.1.0 - ThorN
#       Added data column to penalties table
#       Put censored message/name in the warning data

__author__  = 'ThorN'
__version__ = '2.2.0'

import b3, re, traceback, sys, threading
import b3.events
import b3.plugin
from b3 import functions

class PenaltyData:
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    type = None
    reason = None
    keyword = None
    duration = 0

class CensorData:
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    penalty = None
    regexp = None

#--------------------------------------------------------------------------------------------------
class CensorPlugin(b3.plugin.Plugin):
    _adminPlugin = None
    _reClean = re.compile(r'[^0-9a-z ]+', re.I)
    _defaultBadWordPenalty = None
    _defaultBadNamePenalty = None
    _maxLevel = 0
    _ignoreLength = 3

    def onStartup(self):
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            return False

        self.registerEvent(b3.events.EVT_CLIENT_SAY)
        self.registerEvent(b3.events.EVT_CLIENT_TEAM_SAY)
        self.registerEvent(b3.events.EVT_CLIENT_NAME_CHANGE)
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)

    def onLoadConfig(self):
        try:
            self._maxLevel = self.config.getint('settings', 'max_level')
        except:
            self._maxLevel = 0
        try:
            self._ignoreLength = self.config.getint('settings', 'ignore_length')
        except:
            self._ignoreLength = 3

        penalty = self.config.get('badwords/penalty')[0]

        self._defaultBadWordPenalty = PenaltyData(type = penalty.get('type'),
                            reason = penalty.get('reason'),
                            keyword = penalty.get('reasonkeyword'),
                            duration = functions.time2minutes(penalty.get('duration')))

        penalty = self.config.get('badnames/penalty')[0]

        self._defaultBadNamePenalty = PenaltyData(type = penalty.get('type'),
                            reason = penalty.get('reason'),
                            keyword = penalty.get('reasonkeyword'),
                            duration = functions.time2minutes(penalty.get('duration')))

        # load bad words into memory
        self._badWords = []

        for e in self.config.get('badwords/badword'):
            regexp  = e.find('regexp')
            word    = e.find('word')
            penalty = e.find('penalty')

            if regexp != None:
                # has a regular expression
                self._badWords.append(self._getCensorData(e.get('name'), regexp.text.strip(), penalty, self._defaultBadWordPenalty))

            if word != None:
                # has a plain word
                self._badWords.append(self._getCensorData(e.get('name'), '\\s' + word.text.strip() + '\\s', penalty, self._defaultBadWordPenalty))

        # load bad names into memory
        self._badNames = []

        for e in self.config.get('badnames/badname'):
            regexp  = e.find('regexp')
            word    = e.find('word')
            penalty = e.find('penalty')
            if regexp != None:
                # has a regular expression
                self._badNames.append(self._getCensorData(e.get('name'), regexp.text.strip(), penalty, self._defaultBadNamePenalty))

            if word != None:
                # has a plain word
                self._badNames.append(self._getCensorData(e.get('name'), '\\s' + word.text.strip() + '\\s', penalty, self._defaultBadNamePenalty))

    def _getCensorData(self, name, regexp, penalty, defaultPenalty):
        try:
            regexp = re.compile(regexp, re.I)
        except re.error, e:
            self.error('Invalid regular expression: %s - %s' % (name, regexp))
            raise

        if penalty is not None:
            pd = PenaltyData(type = penalty.get('type'),
                            reason = penalty.get('reason'),
                            keyword = penalty.get('reasonkeyword'),
                            duration = functions.time2minutes(penalty.get('duration')))
        else:
            pd = defaultPenalty

        return CensorData(penalty = pd, regexp = regexp)

    def onEvent(self, event):
        try:
            if not event.client:
                return
            elif event.client.cid == None:
                return
            elif event.client.maxLevel > self._maxLevel:
                return
            elif not event.client.connected:
                return

            if event.type == b3.events.EVT_CLIENT_AUTH or event.type == b3.events.EVT_CLIENT_NAME_CHANGE:
                self.checkBadName(event.client)

            elif len(event.data) > self._ignoreLength:
                if event.type == b3.events.EVT_CLIENT_SAY or \
                   event.type == b3.events.EVT_CLIENT_TEAM_SAY:
                    raw = ' ' + event.data + ' '
                    cleaned = ' ' + self.clean(event.data) + ' '

                    for w in self._badWords:
                        if w.regexp.search(cleaned):
                            self.penalizeClient(w.penalty, event.client, '%s => %s' % (event.data, cleaned))
                            raise b3.events.VetoEvent
                        elif raw != cleaned and w.regexp.search(raw):
                            # Data has special characters, check those too
                            self.penalizeClient(w.penalty, event.client, event.data)
                            raise b3.events.VetoEvent


        except b3.events.VetoEvent:
            raise
        except Exception, msg:
            self.error('Censor plugin error: %s - %s', msg, traceback.extract_tb(sys.exc_info()[2]))

    def penalizeClient(self, penalty, client, data=''):
        """\
        This is the default penalisation for using bad language in say and teamsay
        """
        #self.debug("%s"%((penalty.type, penalty.reason, penalty.keyword, penalty.duration),))
        self._adminPlugin.penalizeClient(penalty.type, client, penalty.reason, penalty.keyword, penalty.duration, None, data)

    def penalizeClientBadname(self, penalty, client, data=''):
        """\
        This is the penalisation for bad names
        """
        #self.debug("%s"%((penalty.type, penalty.reason, penalty.keyword, penalty.duration),))
        self._adminPlugin.penalizeClient(penalty.type, client, penalty.reason, penalty.keyword, penalty.duration, None, data)

    def checkBadName(self, client):
        if not client.connected:
            self.debug('Client not connected?')
            return

        self.debug('Checking %s for badname' % (client.exactName))
        name = ' ' + self.clean(client.exactName) + ' '
        for w in self._badNames:
            if w.regexp.search(name):
                self.penalizeClientBadname(w.penalty, client, '%s => %s' % (client.exactName, name))

                t = threading.Timer(60, self.checkBadName, (client,))
                t.start()
                return

        if name != client.exactName:
            # name has special characters, check those too
            name = client.exactName
            for w in self._badNames:
                if w.regexp.search(name):
                    self.penalizeClientBadname(w.penalty, client, client.exactName)

                    t = threading.Timer(60, self.checkBadName, (client,))
                    t.start()

                    return

    def clean(self, data):
        return re.sub(self._reClean, ' ', self.console.stripColors(data.lower()))
    
    
if __name__ == '__main__':
    import time
    from b3.fake import fakeConsole
    from b3.fake import joe
    
    p = CensorPlugin(fakeConsole, '@b3/conf/plugin_censor.xml')
    p.onStartup()

    fakeConsole.noVerbose = True
    joe._maxLevel = 0
    joe.connected = True
    
    #p.onEvent(b3.events.Event(b3.events.EVT_CLIENT_SAY, "fuck", joe))
    joe.says('hello')
    joe.says('fuck')
    joe.says('nothing wrong')
    joe.says('ass')
    joe.says('shit')
    
    time.sleep(2)
    
    